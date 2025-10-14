import { useMutation } from '@apollo/client';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { LinkTo } from '@/components/LinkTo';
import RunTaskForm from '@/components/RunTaskForm';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { RUN_TASK } from '@/queries';

function RunDialogButton({ taskType, taskRun = null, buttonText = 'Run' }) {
    const navigate = useNavigate();
    const [isRunDialogOpen, setIsRunDialogOpen] = useState(false);
    const [taskRunParameters, setTaskRunParameters] = useState(taskRun ? JSON.parse(taskRun.parametersJson) : {});

    const [runTask, runTaskMutation] = useMutation(RUN_TASK);

    const onRunTask = async () => {
        const response = await runTask({
            variables: { taskTypeId: taskType.id, parametersJson: JSON.stringify(taskRunParameters) },
        });
        setIsRunDialogOpen(false);
        const taskRun = response.data.runTask;
        navigate(`/task-run/${taskRun.id}`);
    };

    return (
        <Dialog open={isRunDialogOpen} onOpenChange={setIsRunDialogOpen}>
            <LinkTo onClick={() => setIsRunDialogOpen(true)}>[{buttonText}]</LinkTo>
            <DialogContent className="min-w-[800px] p-0">
                <div className="flex h-[640px] w-[800px] flex-col gap-4 p-4">
                    <div className="flex-0">Run {taskType.name}</div>
                    <div className="min-h-0 flex-1">
                        <RunTaskForm
                            taskType={taskType}
                            taskRun={taskRun}
                            className="h-full max-w-full"
                            onChange={setTaskRunParameters}
                        />
                    </div>
                    <div className="flex flex-0 justify-end gap-2">
                        <LinkTo onClick={() => setIsRunDialogOpen(false)}>[close]</LinkTo>
                        <LinkTo onClick={onRunTask}>[run]</LinkTo>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

export default RunDialogButton;
