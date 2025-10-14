import { useMutation } from '@apollo/client';
import { useContext } from 'react';

import ExpandableMessage from '@/components/ExpandableMessage';
import HumanTime from '@/components/HumanTime';
import { LinkTo } from '@/components/LinkTo';
import Panel from '@/components/Panel';
import RunDialogButton from '@/components/RunDialogButton';
import StateBadge from '@/components/StateBadge';
import TaskContext from '@/components/TaskContext';
import TaskLink from '@/components/TaskLink';
import { CANCEL_TASK_RUN } from '@/queries';
import { getDurationHumanReadable, getTaskDuration, isTerminalState } from '@/utils';

export default function TaskRunDetails({ taskRun }) {
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
                <div className="flex items-center gap-2">
                    <LinkTo
                        onClick={() => cancelMutate()}
                        disabled={cancelMutation.isLoading || isTerminalState(taskRun.state)}
                    >
                        [Cancel]
                    </LinkTo>
                    <RunDialogButton taskType={taskRun.taskType} taskRun={taskRun} buttonText="Retry" />
                </div>
            </div>
        </Panel>
    );
}
