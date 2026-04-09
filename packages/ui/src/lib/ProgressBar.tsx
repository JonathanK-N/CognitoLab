import React from "react";
import clsx from "clsx";

type ProgressBarProps = {
  value: number; // 0-100
  color?: "blue" | "cyan" | "green" | "amber" | "indigo" | "emerald";
  className?: string;
};

const fillMap: Record<string, string> = {
  blue:    "from-cl-blue to-cl-blue-3",
  cyan:    "from-cl-cyan to-cl-cyan-3",
  green:   "from-emerald-600 to-emerald-400",
  amber:   "from-amber-600 to-amber-400",
  indigo:  "from-cl-blue to-cl-blue-3",
  emerald: "from-emerald-600 to-emerald-400",
};

export const ProgressBar: React.FC<ProgressBarProps> = ({ value, color = "blue", className }) => (
  <div className={clsx("progress-bar-bg", className)}>
    <div
      className={clsx("progress-bar-fill bg-gradient-to-r", fillMap[color] ?? fillMap.blue)}
      style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
    />
  </div>
);
