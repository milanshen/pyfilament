"""A minimal filament example: a weather agent powered by the Anthropic API.

No queue and no worker — every @task runs in-process with a plain `await`. Each @task still shows up as its own filament run, so you get the full call tree (the agent loop, each model call, and each get_weather lookup) for free.

Run it from the repo root:

    export ANTHROPIC_API_KEY=sk-ant-...
    python -m examples.get_weather

Requires the Anthropic SDK (`pip install anthropic`).
"""

from __future__ import annotations

import asyncio
import logging

from anthropic import AsyncAnthropic

from filament import get_logger, task

MODEL = 'claude-sonnet-4-6'
logging.getLogger().setLevel(logging.DEBUG)

# One shared async client. The Anthropic SDK reads ANTHROPIC_API_KEY from the env.
client = AsyncAnthropic()

# The single tool we expose to the model. `input_schema` is the JSON schema the
# model fills in when it decides to call get_weather.
WEATHER_TOOL = {
    'name': 'get_weather',
    'description': 'Get the current weather for a city.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'city': {'type': 'string', 'description': 'City name, e.g. "Paris"'},
        },
        'required': ['city'],
    },
}

# Canned data keeps the example offline and deterministic. Swap this for a real
# weather API call and it stays a single @task — the agent loop doesn't change.
FAKE_WEATHER = {
    'paris': '18°C, light rain',
    'tokyo': '24°C, clear',
    'new york': '21°C, partly cloudy',
    'cairo': '33°C, sunny',
}


### TOOLS


# The @task lives on the real work. It's a normal async function with a clean,
# serializable signature, so filament records its input (city) and output.
@task
async def get_weather(city: str) -> str:
    logger = get_logger()
    logger.info('Looking up weather for %s', city)
    return FAKE_WEATHER.get(city.lower(), f'No data for {city}; assume 20°C and mild.')


# Wrapping the model call in a @task gives each request its own run, plus retries
# on a flaky network. `cache` keys on the arguments, so re-asking an identical
# question is answered (and paid for) once.
@task(tries=3, delay=1, cache=True, cache_ttl=3600)
async def call_model(messages: list[dict]) -> dict:
    logger = get_logger()
    response = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[WEATHER_TOOL],
        messages=messages,
    )
    usage = response.usage
    logger.info(
        'model call: stop=%s, input=%s, output=%s',
        response.stop_reason,
        usage.input_tokens,
        usage.output_tokens,
    )
    # Return a plain dict so the result round-trips cleanly through filament.
    return {
        'stop_reason': response.stop_reason,
        'content': [block.model_dump() for block in response.content],
    }


### AGENT


@task
async def answer_weather_question(question: str) -> str:
    """Run the tool-use loop: ask the model, run any get_weather call it requests,
    feed the result back, and repeat until it produces a final answer."""
    logger = get_logger()
    logger.info('Question: %s', question)
    messages: list[dict] = [{'role': 'user', 'content': question}]

    while True:
        reply = await call_model(messages)
        messages.append({'role': 'assistant', 'content': reply['content']})

        if reply['stop_reason'] != 'tool_use':
            # No tool requested — gather the text blocks and we're done.
            text = ' '.join(b['text'] for b in reply['content'] if b['type'] == 'text')
            return text.strip()

        # Run each requested tool call as its own filament run, then hand the
        # results back to the model in a single user turn.
        tool_results = []
        for block in reply['content']:
            if block['type'] != 'tool_use':
                continue
            assert block['name'] == 'get_weather', f'Unexpected tool: {block["name"]}'
            weather = await get_weather(block['input']['city'])
            tool_results.append({'type': 'tool_result', 'tool_use_id': block['id'], 'content': weather})
        messages.append({'role': 'user', 'content': tool_results})


### RUN


@task
async def main():
    logger = get_logger()
    logger.info('Starting main')
    questions = [
        'What is the weather in Paris?',
        'Should I bring sunglasses in Cairo or Tokyo right now?',
    ]
    for question in questions:
        answer = await answer_weather_question(question)
        print(f'Q: {question}\nA: {answer}\n')


if __name__ == '__main__':
    asyncio.run(main())
