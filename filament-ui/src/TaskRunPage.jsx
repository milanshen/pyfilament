import { useQuery } from '@apollo/client';
import { useQuery as useReactQuery } from '@tanstack/react-query';
import _ from 'lodash';
import { useState } from 'react';
import { useParams } from 'react-router-dom';

import TasksTimeline from '@/TasksTimeline';
import Panel from '@/components/Panel';
import TaskContext from '@/components/TaskContext';
import TaskLogs from '@/components/TaskLogs';
import TaskRunBreadcrumbs from '@/components/TaskRunBreadcrumbs';
import TaskRunDetails from '@/components/TaskRunDetails';
import { GET_TASK_RUN } from '@/queries';

export default function TaskRunPage() {
    const { taskRunId } = useParams();
    const { refetch: refetchTaskRun } = useQuery(GET_TASK_RUN, { skip: true });
    const [selectedTask, setSelectedTask] = useState(null);

    const fetchFullTree = async (variables, depth = 1) => {
        const { data } = await refetchTaskRun(variables);
        const taskRun = data.getTaskRun;
        const newChildTaskPromises = [];
        if (depth > 0) {
            for (const childTask of taskRun.childTasks) {
                const childDataPromise = fetchFullTree({ id: childTask.id }, depth - 1);
                newChildTaskPromises.push(childDataPromise);
            }
        }
        const newChildTasks = await Promise.all(newChildTaskPromises);
        let newTaskRun = { ...taskRun, childTasks: newChildTasks };
        return newTaskRun;
    };

    let initialFetchVariables = {};
    if (taskRunId.match(/^[0-9]+$/)) {
        initialFetchVariables.id = taskRunId;
    } else {
        initialFetchVariables.taskUuid = taskRunId;
    }

    const fetchTaskRunTree = useReactQuery({
        queryKey: ['taskRun', taskRunId],
        queryFn: async () => {
            const result = await fetchFullTree(initialFetchVariables, 1);
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
                    {selectedTask && <TaskRunDetails taskRun={selectedTask} />}
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
