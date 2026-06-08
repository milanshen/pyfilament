import { useState } from 'react';
import { CgSpinner } from 'react-icons/cg';
import { TbExclamationCircle } from 'react-icons/tb';
import { useNavigate } from 'react-router-dom';

import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

function LinkTo({ url = null, onClick = null, disabled = false, isDownload = false, children }) {
    const navigate = useNavigate();

    const [isLoading, setIsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState(null);

    const handleClick = async (event) => {
        if (onClick) {
            const result = onClick(event);
            if (result instanceof Promise) {
                setIsLoading(true);
                setErrorMessage(null);
                try {
                    await result;
                } catch (error) {
                    setErrorMessage(error.message);
                } finally {
                    setIsLoading(false);
                }
            }
        } else if (url) {
            if (event.metaKey || event.ctrlKey || event.shiftKey) {
                return;
            } else if (!isDownload) {
                event.preventDefault();
                navigate(url);
            }
        }
    };

    return (
        <div
            onClick={handleClick}
            className={cn('flex items-center gap-2', {
                'cursor-pointer text-blue-500 select-none hover:underline': !disabled,
                'cursor-not-allowed text-neutral-500 line-through': disabled,
            })}
        >
            <a href={url}>{children}</a>
            {isLoading && <CgSpinner className="animate-spin" />}
            {errorMessage && (
                <Tooltip>
                    <TooltipTrigger>
                        <TbExclamationCircle />
                    </TooltipTrigger>
                    <TooltipContent>{errorMessage}</TooltipContent>
                </Tooltip>
            )}
        </div>
    );
}

export { LinkTo };
