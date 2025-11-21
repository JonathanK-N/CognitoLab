import React from "react";
import clsx from "clsx";

type CardProps = {
  title?: string;
  subtitle?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
};

export const Card: React.FC<CardProps> = ({ title, subtitle, right, children, className }) => (
  <div className={clsx("rounded-xl border border-slate-200 bg-white shadow-sm", className)}>
    {(title || subtitle || right) && (
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
        <div>
          {title && <h3 className="text-base font-semibold text-slate-900">{title}</h3>}
          {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
        </div>
        {right}
      </div>
    )}
    <div className="px-4 py-3">{children}</div>
  </div>
);
