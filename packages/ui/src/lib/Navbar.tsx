import React from "react";
import clsx from "clsx";

type NavbarProps = {
  right?: React.ReactNode;
  title?: string;
  className?: string;
};

export const Navbar: React.FC<NavbarProps> = ({ right, title, className }) => (
  <header className={clsx(
    "w-full h-14 flex items-center justify-between px-6",
    "bg-cl-dark-2/80 backdrop-blur-md",
    "border-b border-cl-blue/10",
    "relative z-20",
    className
  )}>
    {/* Left: breadcrumb / title */}
    <div className="flex items-center gap-2 text-sm">
      <span className="text-cl-blue-4 font-medium">{title ?? "CognitoLab"}</span>
    </div>

    {/* Right: actions */}
    <div className="flex items-center gap-3">{right}</div>
  </header>
);
