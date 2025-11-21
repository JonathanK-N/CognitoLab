import React from "react";
import clsx from "clsx";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
};

const variantClasses: Record<Variant, string> = {
  primary: "bg-indigo-600 hover:bg-indigo-700 text-white shadow",
  secondary: "bg-slate-800 hover:bg-slate-900 text-white",
  ghost: "bg-transparent hover:bg-slate-100 text-slate-800 border border-slate-200",
  danger: "bg-rose-600 hover:bg-rose-700 text-white",
};

const sizeClasses: Record<Size, string> = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-3 text-base",
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
        "rounded-md font-medium transition disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2 justify-center",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {loading && (
        <span className="h-4 w-4 border-2 border-white/60 border-t-transparent rounded-full animate-spin" />
      )}
      {children}
    </button>
  );
};
