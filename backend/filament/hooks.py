from filament.utils_call_stack import peek_task_run


def get_current_task_run():
    task_run = peek_task_run()
    if task_run is not None:
        return task_run
    raise RuntimeError('No task found in stack')
