import logging

from redis import ResponseError

from filament.redis_utils import r

logger = logging.getLogger(__name__)


def get_stream_name(task_type):
    return f'filament:task:run:{task_type.name}'


def get_channel_name(task_uuid):
    return f'filament:task:result:{task_uuid}'


def get_group_name():
    return 'group:workers'


async def setup_queue(task_type):
    logger.info(f'setting up queue for {task_type.name}')
    stream_name = get_stream_name(task_type)
    group_name = get_group_name()
    # existing_groups = await r.xinfo_groups(stream_name)
    # group_names = [group["name"] for group in existing_groups]
    # if group_name in group_names:
    #     return
    try:
        logger.info(f'creating group {group_name} for stream {stream_name}')
        await r.xgroup_create(stream_name, group_name, id='0', mkstream=True)
    except ResponseError as e:
        # there might be a race condition where two workers try to create the same group
        if 'BUSYGROUP Consumer Group name already exists' not in str(e):
            raise


async def enqueue_task_run(filament_task_run):
    stream_name = get_stream_name(filament_task_run.type)
    logger.info(f'{filament_task_run.uuid} enqueuing to {stream_name} with data {filament_task_run.model_dump_json()}')
    await r.xadd(stream_name, {'json_data': filament_task_run.model_dump_json()})
    logger.info(f'{filament_task_run.uuid} enqueued to {stream_name}')


async def dequeue_task_run(task_type, worker_id):
    stream_name = get_stream_name(task_type)
    group_name = get_group_name()
    worker_name = f'worker:{worker_id}'
    logger.info(f'{worker_name} attempting to read from {stream_name} for group {group_name}')
    resp = await r.xreadgroup(group_name, worker_name, streams={stream_name: '>'}, count=1, block=0)
    for _stream_name, messages in resp:
        assert _stream_name == stream_name, f'Expected stream {stream_name}, got {_stream_name}'
        assert len(messages) == 1, f'Expected exactly one message, got {len(messages)}'
        message_id, message_data = messages[0]
        logger.info(f'{message_id} read from {stream_name} by {worker_name}')
        return message_id, message_data['json_data']
    raise ValueError(f'No messages in stream {stream_name} for group {group_name}')


async def publish_task_result(task_result, is_final=True, message_id=None):
    channel_name = get_channel_name(task_result.task_uuid)
    logger.debug(f'{task_result.task_uuid} publishing to {channel_name} with data {task_result.model_dump_json()}')
    await r.set(channel_name, task_result.model_dump_json())
    if is_final:
        await r.publish(channel_name, 'complete')
        if message_id:
            stream_name = get_stream_name(task_result.type)
            await r.xack(stream_name, get_group_name(), message_id)
            logger.info(f'{message_id} acked in {stream_name}')
    else:
        await r.publish(channel_name, 'partial')


async def listen_for_task_result(task_uuid):
    channel_name = get_channel_name(task_uuid)
    pubsub = r.pubsub()
    await pubsub.subscribe(channel_name)
    async for message in pubsub.listen():
        if message['type'] == 'message':
            logger.debug(f'{message["data"]} received on {channel_name}')
            if message['data'] == 'complete':
                await pubsub.unsubscribe(channel_name)
                yield await get_task_result(task_uuid), True
            elif message['data'] == 'partial':
                yield await get_task_result(task_uuid), False
            else:
                raise ValueError(f'Unknown message type: {message["data"]}')


async def get_task_result(task_uuid):
    channel_name = get_channel_name(task_uuid)
    return await r.get(channel_name)
