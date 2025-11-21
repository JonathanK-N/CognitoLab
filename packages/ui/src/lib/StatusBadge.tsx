import React from "react";
import clsx from "clsx";

type Status = "success" | "warning" | "info" | "danger" | "neutral";

const colors: Record<Status, string> = {
  success: "bg-emerald-100 text-emerald-800",
  warning: "bg-amber-100 text-amber-800",
  info: "bg-blue-100 text-blue-800",
  danger: "bg-rose-100 text-rose-800",
  neutral: "bg-slate-100 text-slate-800"
};

export const StatusBadge: React.FC<{ status?: Status; children: React.ReactNode }> = ({
  status = "neutral",
  children
}) => (
  <span
    className={clsx(
      "inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold capitalize",
      colors[status]
    )}
  >
    {children}
  </span>
);
