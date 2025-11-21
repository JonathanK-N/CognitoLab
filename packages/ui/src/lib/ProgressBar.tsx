import React from "react";
import clsx from "clsx";

type ProgressBarProps = {
  value: number; // 0-100
  color?: "indigo" | "emerald" | "amber" | "rose";
  className?: string;
};

const colorMap: Record<string, string> = {
  indigo: "bg-indigo-600",
  emerald: "bg-emerald-600",
  amber: "bg-amber-500",
  rose: "bg-rose-600"
};

export const ProgressBar: React.FC<ProgressBarProps> = ({ value, color = "indigo", className }) => (
  <div className={clsx("w-full h-2 rounded-full bg-slate-100", className)}>
    <div
      className={clsx("h-2 rounded-full transition-all duration-200", colorMap[color])}
      style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
    />
  </div>
);
