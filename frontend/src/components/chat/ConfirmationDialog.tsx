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
    <Card className="border-primary">
      <CardHeader>
        <CardTitle className="text-lg">Confirmation Required</CardTitle>
        <CardDescription>{question}</CardDescription>
      </CardHeader>
      {context && Object.keys(context).length > 0 && (
        <CardContent className="text-sm">
          <div className="space-y-1">
            {Object.entries(context).map(([key, value]) => (
              <div key={key} className="flex gap-2">
                <span className="font-medium">{key}:</span>
                <span className="text-muted-foreground">{String(value)}</span>
              </div>
            ))}
          </div>
        </CardContent>
      )}
      <CardFooter className="flex gap-2 justify-end">
        <Button variant="outline" onClick={onReject}>
          No
        </Button>
        <Button onClick={onConfirm}>Yes</Button>
      </CardFooter>
    </Card>
  );
}
