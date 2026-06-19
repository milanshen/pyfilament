"""A minimal filament example: a weather agent powered by the Anthropic API.

No queue and no worker — every @task runs in-process with a plain `await`, yet each still shows up as its own filament run, so you get the full call tree for free.

Run it from the repo root (requires `pip install anthropic`):

    export ANTHROPIC_API_KEY=sk-ant-...
    python -m examples.get_weather
"""

from __future__ import annotations

import asyncio
import logging

from anthropic import AsyncAnthropic

from filament import get_logger, task

MODEL = 'claude-sonnet-4-6'
MAX_TURNS = 10
logging.getLogger().setLevel(logging.DEBUG)

client = AsyncAnthropic()

WEATHER_TOOL = {
    'name': 'get_weather',
    'description': 'Get the current weather for a city.',
    'input_schema': {
        'type': 'object',
        'properties': {'city': {'type': 'string', 'description': 'City name, e.g. "Paris"'}},
        'required': ['city'],
    },
}

FAKE_WEATHER = {
    'paris': '18°C, light rain',
    'tokyo': '24°C, clear',
    'new york': '21°C, partly cloudy',
    'cairo': '33°C, sunny',
}


### TOOLS


@task
async def get_weather(city: str) -> str:
    get_logger().info('Looking up weather for %s', city)
    return FAKE_WEATHER.get(city.lower(), f'No data for {city}; assume 20°C and mild.')


# `cache` keys on the arguments, so re-asking an identical question is paid for once.
@task(tries=3, delay=1, cache=True, cache_ttl=3600)
async def call_model(messages: list[dict]) -> dict:
    response = await client.messages.create(model=MODEL, max_tokens=1024, tools=[WEATHER_TOOL], messages=messages)
    usage = response.usage
    get_logger().info(
        'model call: stop=%s, input=%s, output=%s', response.stop_reason, usage.input_tokens, usage.output_tokens
    )
    # Plain dict so the result round-trips cleanly through filament.
    return {'stop_reason': response.stop_reason, 'content': [block.model_dump() for block in response.content]}


### AGENT


@task
async def answer_weather_question(question: str) -> str:
    """Tool-use loop: ask the model, run any get_weather call it requests, feed the
    result back, and repeat until it produces a final answer."""
    get_logger().info('Question: %s', question)
    messages: list[dict] = [{'role': 'user', 'content': question}]
    for _ in range(MAX_TURNS):
        reply = await call_model(messages)
        messages.append({'role': 'assistant', 'content': reply['content']})
        if reply['stop_reason'] != 'tool_use':
            return ' '.join(b['text'] for b in reply['content'] if b['type'] == 'text').strip()
        tool_results = []
        for block in reply['content']:
            if block['type'] != 'tool_use':
                continue
            assert block['name'] == 'get_weather', f'Unexpected tool: {block["name"]}'
            weather = await get_weather(block['input']['city'])
            tool_results.append({'type': 'tool_result', 'tool_use_id': block['id'], 'content': weather})
        messages.append({'role': 'user', 'content': tool_results})
    raise RuntimeError(f'No final answer after {MAX_TURNS} turns')


### RUN


@task
async def main():
    questions = [
        'What is the weather in Paris?',
        'Should I bring sunglasses in Cairo or Tokyo right now?',
    ]
    for question in questions:
        answer = await answer_weather_question(question)
        print(f'Q: {question}\nA: {answer}\n')


if __name__ == '__main__':
    asyncio.run(main())
