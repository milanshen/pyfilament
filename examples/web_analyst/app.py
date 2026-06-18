import asyncio
import json
import logging
import os
import re

import requests
from agents import Agent, RunContextWrapper, Runner, RunResult, function_tool
from pydantic import BaseModel

from filament import get_logger, task
from filament.db.session import async_session_scope
from filament.redis.semaphore import RedisSemaphore
from filament.state.task_type_state import upsert_task_type_state

MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1')
logging.getLogger().setLevel(logging.DEBUG)


class PageBrief(BaseModel):
    category: str
    """news | docs | product | blog | reference | other"""
    title: str
    """title of the page"""
    summary: str
    """summary of the page, 2-3 plain-language sentences"""
    key_points: list[str]
    """key points of the page, 3-5 short bullets"""
    audience: str
    """audience of the page"""
    key_links: list[str]
    """notable links, from the extract_links tool"""


class PageCategory(BaseModel):
    category: str
    """news | docs | product | blog | reference | other"""


# The full HTML rides in the run context so the tool can read it without the
# model echoing thousands of chars back as a tool argument. The Agents SDK hides
# the RunContextWrapper param from the tool's JSON schema.
class PageContext(BaseModel):
    html: str


BRIEF_INSTRUCTIONS = (
    "Analyze the web page's raw HTML and return a brief. Ignore nav, ads and "
    'boilerplate; focus on the main content. '
    'The HTML below is TRUNCATED, so you cannot see every link. You MUST call the '
    'extract_links tool (it takes no arguments and reads the full page) to populate '
    'key_links; never guess or hand-copy links from the truncated HTML.'
)


### TOOLS

# The `@task` lives on the real work, as deep as possible; a thin `@function_tool`
# wrapper exposes it to the agent. Each tool call shows up as its own filament run.


@task
async def extract_links(html: str) -> list[str]:
    logger = get_logger()
    hrefs = re.findall(r"""href=["'](https?://[^"']+)["']""", html)
    links = list(dict.fromkeys(hrefs))[:20]
    logger.info('extract_links found %d link(s)', len(links))
    return links


# Why two functions instead of one @task @function_tool: the decorators can't stack.
# @function_tool turns the function into a FunctionTool object, but @task asserts it
# wraps a coroutine/async-gen function (a FunctionTool isn't one), so @task over
# @function_tool raises "Unsupported function". The reverse fails too — @task returns
# a FilamentRemoteTaskType, which @function_tool can't introspect to build its schema.
# So the real work stays a plain @task with a clean, serializable `html: str`
# signature (its own filament run, with input/output schema), and this thin
# @function_tool adapts the SDK's calling convention — hiding RunContextWrapper from
# the tool schema and pulling the HTML out of the run context — then delegates to it.
@function_tool(
    name_override='extract_links',
    description_override='Return up to 20 distinct absolute (http/https) links found on the page. '
    'Takes no arguments — it reads the full HTML from the run context.',
)
async def extract_links_tool(ctx: RunContextWrapper[PageContext]) -> list[str]:
    return await extract_links(ctx.context.html)


### AGENTS

triage_agent = Agent(
    name='Triage',
    model=MODEL,
    output_type=PageCategory,
    instructions='Classify the page from its URL and HTML. Return only the category: '
    'news | docs | product | blog | reference | other.',
)
news_agent = Agent(
    name='News Analyst',
    model=MODEL,
    output_type=PageBrief,
    tools=[extract_links_tool],
    instructions='You analyze a news or aggregator page; surface the highest-impact stories. ' + BRIEF_INSTRUCTIONS,
)
docs_agent = Agent(
    name='Docs Analyst',
    model=MODEL,
    output_type=PageBrief,
    tools=[extract_links_tool],
    instructions='You analyze documentation or reference pages; lead with what the reader can DO. '
    + BRIEF_INSTRUCTIONS,
)
general_agent = Agent(
    name='General Analyst',
    model=MODEL,
    output_type=PageBrief,
    tools=[extract_links_tool],
    instructions=BRIEF_INSTRUCTIONS,
)

# category -> specialist (anything else falls back to general_agent).
SPECIALISTS = {
    'news': news_agent,
    'docs': docs_agent,
    'reference': docs_agent,
    'product': docs_agent,
    'blog': docs_agent,
    'other': general_agent,
}


def build_prompt(url: str, html: str) -> str:
    return f'URL: {url}\n\nHTML (truncated):\n{html[:8000]}'


# NOTE: params are intentionally left unannotated. filament introspects the
# signature to build an input JSON schema, and the third-party `Agent` type can't
# be rendered into one — leaving the params bare makes filament skip the schema
# instead of erroring. Types: agent: Agent, prompt: str, context: PageContext | None.
@task
async def run_agent(agent, prompt, context=None) -> RunResult:
    logger = get_logger()
    logger.info('Running agent: %s', agent.name)
    result = await Runner.run(agent, prompt, context=context)
    try:
        u = result.context_wrapper.usage
        logger.info('token usage: total=%s, input=%s, output=%s', u.total_tokens, u.input_tokens, u.output_tokens)
    except Exception:  # noqa: BLE001 - usage logging must never break a run
        pass
    return result


### TASKS


@task(tries=3, delay=1, timeout=30, rate_limit=2)
async def fetch_page(url: str) -> str:
    """Download a page. `tries` rides out a flaky network, `rate_limit=2` stays
    polite, `timeout` aborts a hang."""
    logger = get_logger()
    logger.info('GET %s', url)
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


@task(tries=3, delay=2, cache=True, cache_ttl=3600)
async def summarize(url: str, html: str) -> PageBrief:
    """Classify the page, then run the matching specialist (which may call
    extract_links). `cache` keys on (url, html), so an identical page is briefed
    (and paid for) once. Each run_agent is its own run, so the delegation tree
    shows up."""
    logger = get_logger()
    prompt = build_prompt(url, html)
    triage = await run_agent(triage_agent, prompt)
    category = (triage.final_output.category or 'other').lower()
    try:
        specialist = SPECIALISTS[category]
    except Exception:
        logger.exception('Error getting specialist for category: %s', category)
    # The specialist gets the full HTML via context so extract_links works on the
    # whole page, not the truncated prompt.
    result = await run_agent(specialist, prompt, PageContext(html=html))
    return result.final_output


@task(max_concurrent=4)
async def analyze_page(url: str) -> PageBrief:
    """The distributed unit of work: fetch, then summarize. Submitted to the queue
    with .request() and run by a worker via .serve(); fetch/summarize/run_agent run
    in that worker as child runs. `max_concurrent=4` is a *global* cap shared across
    every worker, not a per-process one."""
    logger = get_logger()
    logger.info('analyze %s', url)
    html = await fetch_page(url)
    brief = await summarize(url, html)
    logger.info('analyze %s complete', url)
    log_brief(url, brief)
    return brief


### DISTRIBUTED RUN
#
# Two processes share a Redis queue. Run both from the repo root:
#   Terminal 1:  python -m examples.web_analyst.worker   # serve forever
#   Terminal 2:  python -m examples.web_analyst          # submit jobs
#
# analyze_page is the queued unit: run_web_analyst_pipeline enqueues one run per URL
# with .request(); a worker pulls each off the stream and runs it (fetch/summarize/
# run_agent execute inside that worker as child runs). Start more workers in more
# terminals and they share the queue and the global max_concurrent cap.


TASK_TYPES = [extract_links, run_agent, fetch_page, summarize, analyze_page]


async def register_task_types() -> None:
    """Create each @task type's DB row once, serially, under a single lock. Call
    before submitting or serving so concurrent first-time runs never race to insert
    the same task_type row."""
    async with RedisSemaphore(name='web_analyst:register_task_types', max_leases=1, ttl=60):
        async with async_session_scope() as session:
            for task_type in TASK_TYPES:
                await upsert_task_type_state(session, task_type)


@task
async def run_web_analyst_pipeline(urls: list[str]) -> None:
    """Enqueue one analyze_page run per URL, then await the workers' results.
    Results come back in URL order."""
    logger = get_logger()
    await register_task_types()
    logger.info('submitting %d url(s) to the queue …', len(urls))
    runs = await asyncio.gather(*(analyze_page.request(url) for url in urls))
    results = await asyncio.gather(*runs)
    # Results that cross the Redis queue come back as plain dicts (JSON round-trip),
    # so rebuild the model. model_validate also accepts an existing PageBrief.
    logger.info('Run it again — fetches and briefs come straight from the cache.')
    return [PageBrief.model_validate(r) for r in results]


DEFAULT_URLS = [
    'https://news.ycombinator.com',
    'https://lite.cnn.com',
    'https://text.npr.org',
    'https://docs.python.org/3/',
    'https://fastapi.tiangolo.com',
    'https://react.dev',
    'https://peps.python.org/pep-0008/',
    'https://www.rfc-editor.org/rfc/rfc9110.html',
    'https://simonwillison.net',
    'https://example.com',
]


def log_brief(url: str, b: PageBrief) -> None:
    # Build one message so the brief lands as a single log entry in the filament UI.
    # get_logger() ties it to the surrounding run (run_web_analyst_pipeline) via the
    # call stack, so it shows under that run rather than only on stdout.
    payload = {'url': url, 'model': MODEL, **b.model_dump()}
    get_logger().info(json.dumps(payload, indent=2, ensure_ascii=False))
