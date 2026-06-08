import { cn } from '@/lib/utils';

export default function Panel({ name, className, children }) {
    return (
        <div className={cn('flex flex-col gap-4', className)}>
            <div className="text-2xl font-bold">{name}</div>
            <div className="rounded bg-neutral-100 p-4">{children}</div>
        </div>
    );
}
