import React from "react";
import clsx from "clsx";

export const LoadingOverlay: React.FC<{ show: boolean; label?: string }> = ({ show, label }) => {
  if (!show) return null;
  return (
    <div className="absolute inset-0 bg-white/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white shadow border border-slate-200">
        <span className="h-5 w-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium text-slate-700">{label ?? "Chargement"}</span>
      </div>
    </div>
  );
};
