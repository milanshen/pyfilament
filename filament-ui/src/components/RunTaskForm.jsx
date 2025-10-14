import Form from '@rjsf/shadcn';
import validator from '@rjsf/validator-ajv8';
import { useEffect, useState } from 'react';

import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

export default function RunTaskForm({ taskType, taskRun = null, className = null, onChange = null }) {
    const schema = JSON.parse(taskType.parametersSpec);

    const [formData, setFormData] = useState(taskRun ? JSON.parse(taskRun.parametersJson) : {});
    const [jsonString, setJsonString] = useState(JSON.stringify(formData, null, 2));
    const [isJsonStringValid, setIsJsonStringValid] = useState(true);

    useEffect(() => {
        setFormData(taskRun ? JSON.parse(taskRun.parametersJson) : {});
        setJsonString(JSON.stringify(formData, null, 2));
    }, [taskRun]);

    const uiSchema = {
        'ui:submitButtonOptions': {
            norender: true,
        },
    };

    const onFormDataChange = (e) => {
        setFormData(e.formData);
        setJsonString(JSON.stringify(e.formData, null, 2));
        onChange?.(e.formData);
    };

    const onJsonStringChange = (e) => {
        setJsonString(e.target.value);
        try {
            setFormData(JSON.parse(e.target.value));
            setIsJsonStringValid(true);
        } catch (e) {
            setIsJsonStringValid(false);
        }
    };

    if (!taskType.parametersSpec) {
        return <div>No input schema found for task type {taskType.funcAddress}</div>;
    }

    return (
        <div className={cn('relative flex overflow-hidden', className)}>
            <div className="min-h-0 min-w-0 flex-1 overflow-y-auto">
                <div className="flex w-full flex-col gap-4 p-4 break-all">
                    <Form
                        className="flex flex-col gap-4"
                        schema={schema}
                        validator={validator}
                        formData={formData}
                        onChange={onFormDataChange}
                        uiSchema={uiSchema}
                    />
                </div>
            </div>
            <div className="min-h-0 min-w-0 flex-1 overflow-y-auto">
                <div className="box-border flex flex-col gap-4 p-4">
                    <Textarea
                        className="box-border w-auto whitespace-pre-wrap"
                        value={jsonString}
                        onChange={onJsonStringChange}
                    />
                    {!isJsonStringValid && <div className="text-red-500">Invalid JSON</div>}
                </div>
            </div>
        </div>
    );
}
