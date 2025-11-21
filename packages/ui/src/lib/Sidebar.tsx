import React from "react";
import { NavLink } from "react-router-dom";
import clsx from "clsx";

export type SidebarItem = {
  label: string;
  to: string;
  icon?: React.ReactNode;
};

type SidebarProps = {
  items: SidebarItem[];
  footer?: React.ReactNode;
};

export const Sidebar: React.FC<SidebarProps> = ({ items, footer }) => {
  return (
    <aside className="h-full w-64 border-r border-slate-200 bg-white flex flex-col">
      <div className="px-4 py-3 text-lg font-semibold text-slate-900">CognitoLab</div>
      <nav className="flex-1 space-y-1 px-2">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-50",
                isActive ? "bg-indigo-100 text-indigo-700" : "text-slate-700"
              )
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>
      {footer && <div className="border-t border-slate-200 p-3">{footer}</div>}
    </aside>
  );
};
