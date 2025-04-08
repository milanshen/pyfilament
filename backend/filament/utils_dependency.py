TASK_RUN_REGISTRY = {}


def register_frame(task_run, frame):
    frame_id = id(frame)
    TASK_RUN_REGISTRY[frame_id] = task_run


def unregister_frame(frame):
    frame_id = id(frame)
    if frame_id in TASK_RUN_REGISTRY:
        del TASK_RUN_REGISTRY[frame_id]


def is_registered_frame(frame):
    frame_id = id(frame)
    return frame_id in TASK_RUN_REGISTRY


def get_frame_task_run(frame):
    frame_id = id(frame)
    return TASK_RUN_REGISTRY.get(frame_id)
