import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface ConfirmationDialogProps {
  question: string;
  context?: Record<string, any>;
  onConfirm: () => void;
  onReject: () => void;
}

export function ConfirmationDialog({
  question,
  context,
  onConfirm,
  onReject,
}: ConfirmationDialogProps) {
  return (
    <Card className="border-primary max-w-md p-4">
      <div className="space-y-2">
        <div className="space-y-1">
          <h3 className="text-base font-semibold">Confirmation Required</h3>
          <p className="text-sm text-muted-foreground">{question}</p>
        </div>
        {context && Object.keys(context).length > 0 && (
          <div className="text-xs space-y-0.5">
            {Object.entries(context).map(([key, value]) => (
              <div key={key} className="flex gap-2">
                <span className="font-medium">{key}:</span>
                <span className="text-muted-foreground">{String(value)}</span>
              </div>
            ))}
          </div>
        )}
        <div className="flex gap-2 justify-end pt-2">
          <Button variant="outline" onClick={onReject} size="sm" className="h-8 px-3">
            No
          </Button>
          <Button onClick={onConfirm} size="sm" className="h-8 px-3">Yes</Button>
        </div>
      </div>
    </Card>
  );
}
