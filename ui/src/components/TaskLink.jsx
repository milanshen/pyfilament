import { useContext } from 'react';

import { LinkTo } from '@/components/LinkTo';
import TaskContext from '@/components/TaskContext';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { getShortUuid } from '@/utils';

function TaskLink({ taskRun = null, taskType = null }) {
    const taskContext = useContext(TaskContext);
    const rootTaskRun = taskContext?.rootTaskRun;
    const rootTaskType = taskContext?.rootTaskType;
    taskType = taskType || taskRun?.taskType;
    return (
        <div className="flex">
            <a>
                {taskType && (
                    <Tooltip delayDuration={500}>
                        <TooltipTrigger className="text-left">
                            {taskType.id === rootTaskType?.id ? (
                                taskType.name
                            ) : (
                                <LinkTo url={`/task-type/${taskType.id}`}>{taskType.name}</LinkTo>
                            )}
                        </TooltipTrigger>
                        <TooltipContent>{taskType.funcAddress}</TooltipContent>
                    </Tooltip>
                )}
                {taskRun && taskType && <span className="text-neutral-500">:</span>}
                {taskRun && (
                    <Tooltip delayDuration={500}>
                        <TooltipTrigger>
                            {taskRun.taskUuid === rootTaskRun?.taskUuid ? (
                                getShortUuid(taskRun.taskUuid)
                            ) : (
                                <LinkTo url={`/task-run/${taskRun.id}`}>{getShortUuid(taskRun.taskUuid)}</LinkTo>
                            )}
                        </TooltipTrigger>
                        <TooltipContent>
                            <div className="flex gap-2">
                                <span>{taskRun.taskUuid}</span>
                                <span
                                    className="cursor-pointer hover:underline"
                                    onClick={() => {
                                        navigator.clipboard.writeText(taskRun.taskUuid);
                                    }}
                                >
                                    copy
                                </span>
                            </div>
                        </TooltipContent>
                    </Tooltip>
                )}
            </a>
        </div>
    );
}

export default TaskLink;
