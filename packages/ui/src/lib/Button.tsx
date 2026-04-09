import React from "react";
import clsx from "clsx";

type Variant = "primary" | "secondary" | "ghost" | "cyan" | "danger";
type Size = "sm" | "md" | "lg";

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
};

const variantClasses: Record<Variant, string> = {
  primary:   "btn-primary",
  cyan:      "btn-cyan",
  secondary: "bg-cl-dark-4 hover:bg-cl-dark-5 text-slate-200 border border-white/10 transition-all hover:border-white/20",
  ghost:     "btn-ghost",
  danger:    "bg-rose-700/80 hover:bg-rose-600 text-white border border-rose-500/30 transition-all",
};

const sizeClasses: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-2.5 text-base",
};

export const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  loading,
  className,
  children,
  ...props
}) => {
  return (
    <button
      className={clsx(
        "rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 justify-center",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {loading && (
        <span className="h-3.5 w-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
      )}
      {children}
    </button>
  );
};
