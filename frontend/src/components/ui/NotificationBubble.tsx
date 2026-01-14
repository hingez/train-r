import { Upload, CheckCircle2, AlertCircle } from 'lucide-react';

interface NotificationBubbleProps {
  status: 'uploading' | 'complete' | 'error' | 'idle';
  current?: number;
  total?: number;
  error?: string;
}

export function NotificationBubble({ status, current, total, error }: NotificationBubbleProps) {
  if (status === 'idle') return null;

  const getContent = () => {
    if (status === 'uploading' && current !== undefined && total !== undefined) {
      return {
        icon: <Upload className="w-4 h-4 animate-pulse" />,
        text: `Uploading workouts... ${current}/${total}`,
        bgColor: 'bg-blue-500',
        textColor: 'text-white'
      };
    }

    if (status === 'complete') {
      return {
        icon: <CheckCircle2 className="w-4 h-4" />,
        text: 'Workouts uploaded',
        bgColor: 'bg-green-500',
        textColor: 'text-white'
      };
    }

    if (status === 'error') {
      return {
        icon: <AlertCircle className="w-4 h-4" />,
        text: error ? `Upload failed: ${error}` : 'Upload failed',
        bgColor: 'bg-red-500',
        textColor: 'text-white'
      };
    }

    return null;
  };

  const content = getContent();
  if (!content) return null;

  return (
    <div className={`${content.bgColor} ${content.textColor} px-3 py-1.5 rounded-full shadow-lg flex items-center gap-2 text-sm font-medium animate-in fade-in slide-in-from-top-2 duration-300`}>
      {content.icon}
      <span>{content.text}</span>
    </div>
  );
}
