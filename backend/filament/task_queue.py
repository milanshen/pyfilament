import logging

import redis
import redis.asyncio

from filament.redis_utils import r

logger = logging.getLogger(__name__)


def get_stream_name(task):
    return f'filament:task:run:{task.name}'


def get_channel_name(task_uuid):
    return f'filament:task:result:{task_uuid}'


def get_group_name():
    return 'group:workers'


async def setup_queue(task):
    logger.info(f'setting up queue for {task.name}')
    stream_name = get_stream_name(task)
    group_name = get_group_name()
    # existing_groups = await r.xinfo_groups(stream_name)
    # group_names = [group["name"] for group in existing_groups]
    # if group_name in group_names:
    #     return
    try:
        logger.info(f'creating group {group_name} for stream {stream_name}')
        await r.xgroup_create(stream_name, group_name, id='0', mkstream=True)
    except redis.ResponseError as e:
        # there might be a race condition where two workers try to create the same group
        if 'BUSYGROUP Consumer Group name already exists' not in str(e):
            raise


async def enqueue_task_run(filament_task_run):
    stream_name = get_stream_name(filament_task_run.type)
    logger.debug(f'{filament_task_run.uuid} enqueuing to {stream_name} with data {filament_task_run.model_dump_json()}')
    await r.xadd(stream_name, {'json_data': filament_task_run.model_dump_json()})
    logger.info(f'{filament_task_run.uuid} enqueued to {stream_name}')


async def dequeue_task_run(task, worker_id):
    stream_name = get_stream_name(task)
    group_name = get_group_name()
    worker_name = f'worker:{worker_id}'
    resp = await r.xreadgroup(group_name, worker_name, streams={stream_name: '>'}, count=1)
    for stream_name, messages in resp:
        if stream_name != stream_name:
            continue
        for message_id, message_data in messages:
            # TODO: ideally, we ack after processing the message
            await r.xack(stream_name, group_name, message_id)
            logger.info(f'{message_id} dequeued from {stream_name} by {worker_name}')
            return message_data['json_data']


async def publish_task_result(task_result, is_final=True):
    channel_name = get_channel_name(task_result.task_uuid)
    logger.debug(f'{task_result.task_uuid} publishing to {channel_name} with data {task_result.model_dump_json()}')
    await r.set(channel_name, task_result.model_dump_json())
    if is_final:
        await r.publish(channel_name, 'complete')
    else:
        await r.publish(channel_name, 'partial')


async def listen_for_task_result(task_uuid):
    channel_name = get_channel_name(task_uuid)
    pubsub = r.pubsub()
    last_result = None
    has_yielded = False
    await pubsub.subscribe(channel_name)
    async for message in pubsub.listen():
        if message['type'] == 'message':
            logger.debug(f'{message["data"]} received on {channel_name}')
            if message['data'] == 'complete':
                await pubsub.unsubscribe(channel_name)
                final_result = await r.get(channel_name)
                if not has_yielded and last_result != final_result:
                    yield final_result
                return
            elif message['data'] == 'partial':
                has_yielded = True
                last_result = await r.get(channel_name)
                yield last_result
