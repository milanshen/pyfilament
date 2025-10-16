import { useState } from 'react';

import JSONExpandableMessage from '@/components/JSONExpandableMessage';
import { LinkTo } from '@/components/LinkTo';
import { Dialog, DialogContent } from '@/components/ui/dialog';

function ExpandableMessage({ message, enableDialog = true, enableExpand = false }) {
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <div>
            {isExpanded ? (
                <JSONExpandableMessage message={message} isExpanded={true} />
            ) : (
                <div className="line-clamp-5 break-all">{message}</div>
            )}
            <div className="flex justify-end gap-2">
                {enableDialog && <LinkTo onClick={() => setIsDialogOpen(true)}>[Open]</LinkTo>}
                {enableExpand && (
                    <LinkTo onClick={() => setIsExpanded(!isExpanded)}>{isExpanded ? '[Collapse]' : '[Expand]'}</LinkTo>
                )}
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent className="max-h-[640px] max-w-[800px] overflow-y-auto sm:max-w-[800px]">
                    <JSONExpandableMessage message={message} isExpanded={true} />
                </DialogContent>
            </Dialog>
        </div>
    );
}

export default ExpandableMessage;
