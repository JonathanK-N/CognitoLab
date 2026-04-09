import React from "react";
import clsx from "clsx";

type CardProps = {
  title?: string;
  subtitle?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
};

export const Card: React.FC<CardProps> = ({ title, subtitle, right, children, className, glow }) => (
  <div className={clsx(
    "rounded-2xl",
    "bg-cl-dark-2/80 backdrop-blur-md",
    "border border-cl-blue/15",
    "shadow-card",
    glow && "animate-border-glow",
    className
  )}>
    {(title || subtitle || right) && (
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div>
          {title    && <h3 className="text-sm font-semibold text-slate-100">{title}</h3>}
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        {right}
      </div>
    )}
    <div className="px-5 py-4">{children}</div>
  </div>
);
