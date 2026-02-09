import { useQuery } from '@apollo/client';
import _ from 'lodash';
import { useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';

import ExpandableMessage from '@/components/ExpandableMessage';
import HumanTime from '@/components/HumanTime';
import { LinkTo } from '@/components/LinkTo';
import RunDialogButton from '@/components/RunDialogButton';
import StateBadge from '@/components/StateBadge';
import TaskContext from '@/components/TaskContext';
import TaskLink from '@/components/TaskLink';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

import { GET_TASK_RUNS, GET_TASK_TYPE } from './queries';
import { getStates } from './utils/states';

function TaskTypePage() {
    const { taskTypeId } = useParams();
    const [searchParams] = useSearchParams();
    const days = searchParams.get('days') || 3;
    const [stateFilter, setStateFilter] = useState('all');

    const getTaskTypeQuery = useQuery(GET_TASK_TYPE, { variables: { id: taskTypeId } });
    const getTaskRunsQuery = useQuery(GET_TASK_RUNS, {
        variables: {
            taskTypeId,
            states: getStates(stateFilter),
            days: parseInt(days),
        },
    });

    if (getTaskTypeQuery.loading || getTaskRunsQuery.loading) {
        return <p>Loading...</p>;
    }

    if (getTaskTypeQuery.error || getTaskRunsQuery.error) {
        return <p>Error: {getTaskTypeQuery.error?.message || getTaskRunsQuery.error?.message}</p>;
    }

    const taskType = getTaskTypeQuery.data.getTaskType;
    const taskRuns = _.sortBy(getTaskRunsQuery.data.getTaskRuns, ['createdAt']).reverse();

    return (
        <TaskContext.Provider value={{ rootTaskType: taskType }}>
            <div className="flex flex-col gap-4 p-4">
                <div className="flex flex-col gap-2 pb-4 text-neutral-500">
                    <LinkTo url="/">Filament</LinkTo>
                    <div className="flex items-center gap-2 pl-4">
                        <span>/</span>
                        <TaskLink taskType={taskType} />
                    </div>
                </div>
                <div className="flex justify-between">
                    <div className="text-2xl font-bold">Task Runs</div>
                    <div className="flex items-center gap-2">
                        <RunDialogButton taskType={taskType} />
                        <Select value={stateFilter} onValueChange={setStateFilter}>
                            <SelectTrigger>
                                <SelectValue placeholder="state" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectGroup>
                                    <SelectItem value="all">All</SelectItem>
                                    <SelectItem value="incomplete">Incomplete</SelectItem>
                                    <SelectItem value="success">Success</SelectItem>
                                    <SelectItem value="failure">Failure</SelectItem>
                                </SelectGroup>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
                <div className="flex flex-col gap-4">
                    {taskRuns.map((taskRun) => (
                        <div key={taskRun.id} className="flex items-start gap-4 rounded bg-gray-100 p-4">
                            <div className="flex min-w-0 flex-1 gap-4">
                                <div className="flex-none">
                                    <TaskLink taskRun={taskRun} />
                                </div>
                                <div className="min-w-0 flex-1">
                                    {taskRun.parametersJson && (
                                        <ExpandableMessage message={taskRun.parametersJson} enableExpand={true} />
                                    )}
                                </div>
                            </div>
                            <div className="flex flex-none items-center gap-4">
                                <div className="w-[160px] text-right">
                                    <HumanTime timestamp={taskRun.createdAt} />
                                </div>
                                <StateBadge state={taskRun.state} since={taskRun.stateSince} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </TaskContext.Provider>
    );
}

export default TaskTypePage;
