import { useNavigate } from 'react-router-dom';

import { cn } from '@/lib/utils';

function LinkTo({ url = null, onClick = null, disabled = false, children }) {
    const navigate = useNavigate();
    onClick = onClick
        ? onClick
        : url
          ? (event) => {
                // Check if any modifier keys are pressed
                if (event.metaKey || event.ctrlKey || event.shiftKey) {
                    return;
                } else {
                    event.preventDefault();
                    navigate(url);
                }
            }
          : () => {};
    return (
        <div
            onClick={onClick}
            className={cn({
                'cursor-pointer text-blue-500 select-none hover:underline': !disabled,
                'cursor-not-allowed text-neutral-500 line-through': disabled,
            })}
        >
            <a href={url}>{children}</a>
        </div>
    );
}

export { LinkTo };
