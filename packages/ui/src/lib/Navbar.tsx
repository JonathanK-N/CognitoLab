import React from "react";
import clsx from "clsx";

type NavbarProps = {
  right?: React.ReactNode;
  className?: string;
};

export const Navbar: React.FC<NavbarProps> = ({ right, className }) => (
  <header
    className={clsx(
      "w-full h-16 border-b border-slate-200 bg-white flex items-center justify-between px-4",
      className
    )}
  >
    <div className="font-semibold text-slate-900">CognitoLab</div>
    <div className="flex items-center gap-4">{right}</div>
  </header>
);
