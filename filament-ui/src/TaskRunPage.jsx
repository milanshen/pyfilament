import { useMutation, useQuery } from '@apollo/client';
import { useQuery as useReactQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import _ from 'lodash';
import { useContext, useState } from 'react';
import { useParams } from 'react-router-dom';

import TasksTimeline from '@/TasksTimeline';
import ExpandableMessage from '@/components/ExpandableMessage';
import HumanTime from '@/components/HumanTime';
import { LinkTo } from '@/components/LinkTo';
import StateBadge from '@/components/StateBadge';
import TaskContext from '@/components/TaskContext';
import TaskLink from '@/components/TaskLink';
import TaskLogs from '@/components/TaskLogs';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { CANCEL_TASK_RUN, GET_TASK_RUN, GET_TASK_RUN_BREADCRUMB } from '@/queries';
import { getDurationHumanReadable, getTaskDuration, isTerminalState } from '@/utils';

function TaskRunPage() {
    const { taskRunId } = useParams();
    const { refetch: refetchTaskRun } = useQuery(GET_TASK_RUN, { skip: true });
    const [selectedTask, setSelectedTask] = useState(null);

    const fetchFullTree = async (variables, depth = 1) => {
        const { data } = await refetchTaskRun(variables);
        const taskRun = data.getTaskRun;
        const newChildTasks = [];
        if (depth > 0) {
            for (const childTask of taskRun.childTasks) {
                const childData = await fetchFullTree({ id: childTask.id }, depth - 1);
                newChildTasks.push(childData);
            }
        }
        let newTaskRun = { ...taskRun, childTasks: newChildTasks };
        return newTaskRun;
    };

    const fetchTaskRunTree = useReactQuery({
        queryKey: ['taskRun', taskRunId],
        queryFn: async () => {
            const result = await fetchFullTree({ id: taskRunId }, 2);
            setSelectedTask(result);
            return result;
        },
    });

    const flattenTasks = (taskRun) => {
        let tasks = [taskRun];
        for (const childTask of taskRun.childTasks) {
            const childTasks = flattenTasks(childTask);
            if (childTasks) {
                tasks = [...tasks, ...childTasks];
            }
        }
        return tasks;
    };

    if (fetchTaskRunTree.isLoading || fetchTaskRunTree.isError) {
        return <p>{fetchTaskRunTree.isLoading ? 'Loading...' : `Error: ${fetchTaskRunTree.error.message}`}</p>;
    }

    const rootTaskRun = fetchTaskRunTree.data;
    const tasks = _.sortBy(flattenTasks(rootTaskRun), ['createdAt']);

    return (
        <TaskContext.Provider value={{ selectedTask, setSelectedTask, rootTaskRun, fetchTaskRunTree }}>
            <div className="flex flex-col gap-4 p-4">
                <TaskRunBreadcrumbs taskRun={rootTaskRun} />
                <div className="flex items-start gap-4">
                    <Panel name="Timeline" className="flex-2">
                        <TasksTimeline tasks={tasks} relativeTo={rootTaskRun.createdAt} />
                    </Panel>
                    {selectedTask && <TaskDetails taskRun={selectedTask} />}
                </div>
                {selectedTask && (
                    <Panel name="Logs">
                        <TaskLogs taskRun={selectedTask} />
                    </Panel>
                )}
            </div>
        </TaskContext.Provider>
    );
}

function Panel({ name, className, children }) {
    return (
        <div className={cn('flex flex-col gap-4', className)}>
            <div className="text-2xl font-bold">{name}</div>
            <div className="rounded bg-neutral-100 p-4">{children}</div>
        </div>
    );
}

function TaskRunBreadcrumbs({ taskRun }) {
    const { refetch: refetchTaskRunBreadcrumb } = useQuery(GET_TASK_RUN_BREADCRUMB, { skip: true });

    const breadcrumbsQuery = useReactQuery({
        queryKey: ['taskRun', taskRun.id],
        queryFn: async () => {
            let ancestorTaskRuns = [taskRun];
            let currentTaskRun = taskRun;
            while (currentTaskRun.parentTaskUuid) {
                const { data } = await refetchTaskRunBreadcrumb({ uuid: currentTaskRun.parentTaskUuid });
                currentTaskRun = data.getTaskRun;
                ancestorTaskRuns.push(currentTaskRun);
            }
            return ancestorTaskRuns.reverse();
        },
    });

    if (breadcrumbsQuery.isLoading || breadcrumbsQuery.isError) {
        return <p>{breadcrumbsQuery.isLoading ? 'Loading...' : `Error: ${breadcrumbsQuery.error.message}`}</p>;
    }

    const breadcrumbs = breadcrumbsQuery.data;

    return (
        <div className="flex flex-col gap-2 pb-4 text-neutral-500">
            <LinkTo url="/">Filament</LinkTo>
            {breadcrumbs.map((taskRun, index) => (
                <div className="flex items-center gap-2 pl-4" key={taskRun.id}>
                    <span>/</span>
                    <Tooltip delayDuration={500}>
                        <TooltipTrigger>
                            <StateBadge state={taskRun.state} since={taskRun.stateSince} />
                        </TooltipTrigger>
                        <TooltipContent>{dayjs(taskRun.stateSince).format('YYYY-MM-DD HH:mm:ss')}</TooltipContent>
                    </Tooltip>
                    <TaskLink taskRun={taskRun} />
                </div>
            ))}
        </div>
    );
}

function TaskDetails({ taskRun }) {
    const { fetchTaskRunTree } = useContext(TaskContext);
    const [cancelMutate, cancelMutation] = useMutation(CANCEL_TASK_RUN, {
        variables: { id: taskRun.id },
        onCompleted: () => {
            fetchTaskRunTree.refetch();
        },
    });
    return (
        <Panel name="Details" className="flex-1">
            <div className="grid grid-cols-[80px_1fr] gap-x-4">
                <div className="text-right text-neutral-500">Task</div>
                <div className="break-all">
                    <TaskLink taskRun={taskRun} />
                </div>
                <div className="text-right text-neutral-500">State</div>
                <div>
                    <StateBadge state={taskRun.state} since={taskRun.stateSince} />
                </div>
                <div className="text-right text-neutral-500">Created</div>
                <div>
                    <HumanTime timestamp={taskRun.createdAt} />
                </div>
                <div className="text-right text-neutral-500">Duration</div>
                <div>{getDurationHumanReadable(getTaskDuration(taskRun))} </div>
                <div className="text-right text-neutral-500">Heartbeat</div>
                <div>
                    <HumanTime timestamp={taskRun.heartbeat} />
                </div>
                <div className="text-right text-neutral-500">Run Count</div>
                <div>{taskRun.runCount}</div>
                <div className="text-right text-neutral-500">Parameters</div>
                <div>{taskRun.parametersJson ? <ExpandableMessage message={taskRun.parametersJson} /> : 'N/A'}</div>
                <div className="text-right text-neutral-500">Result</div>
                <div>{taskRun.resultJson ? <ExpandableMessage message={taskRun.resultJson} /> : 'N/A'}</div>
                <div className="text-right text-neutral-500">Actions</div>
                <div>
                    <LinkTo
                        onClick={() => cancelMutate()}
                        disabled={cancelMutation.isLoading || isTerminalState(taskRun.state)}
                    >
                        [Cancel]
                    </LinkTo>
                </div>
            </div>
        </Panel>
    );
}

export default TaskRunPage;
