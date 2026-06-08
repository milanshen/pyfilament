import { Checkbox } from '@/components/ui/checkbox';

export default function CheckboxLabel({ children, checked, onCheckedChange, ...props }) {
    onCheckedChange = onCheckedChange || (() => {});
    return (
        <div className="flex items-center gap-2" onClick={() => onCheckedChange(!checked)}>
            <Checkbox checked={checked} />
            <label>{children}</label>
        </div>
    );
}
