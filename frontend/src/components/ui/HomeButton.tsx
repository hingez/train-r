"use client";

import { Home } from "lucide-react";

interface HomeButtonProps {
  onClick: () => void;
}

export function HomeButton({ onClick }: HomeButtonProps) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors rounded-lg hover:bg-muted"
      aria-label="Go to dashboard"
    >
      <Home className="h-4 w-4" />
      <span>Dashboard</span>
    </button>
  );
}
