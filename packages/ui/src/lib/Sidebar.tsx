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
    <aside className="h-full w-64 flex flex-col border-r border-cl-blue/10 bg-cl-dark-2/90 backdrop-blur-xl relative overflow-hidden">
      {/* Background circuit grid */}
      <div className="absolute inset-0 opacity-20" style={{
        backgroundImage:
          "linear-gradient(rgba(33,150,243,0.06) 1px, transparent 1px)," +
          "linear-gradient(90deg, rgba(33,150,243,0.06) 1px, transparent 1px)",
        backgroundSize: "30px 30px"
      }} />

      {/* Logo area */}
      <div className="relative z-10 flex items-center gap-3 px-5 py-5 border-b border-cl-blue/10">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ background: "linear-gradient(135deg, #1565C0, #00BCD4)" }}>
          <img src="/logo.svg" alt="CognitoLab" className="w-7 h-7" />
        </div>
        <div>
          <span className="font-bold text-white text-base tracking-wide">CognitoLab</span>
          <p className="text-xs text-cl-blue-4/70 leading-none mt-0.5">by Cognito Inc.</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="relative z-10 flex-1 space-y-1 px-3 py-4 overflow-y-auto">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              clsx("nav-link", isActive && "active")
            }
          >
            {item.icon && (
              <span className="w-5 h-5 flex-shrink-0 opacity-80">{item.icon}</span>
            )}
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      {footer && (
        <div className="relative z-10 border-t border-cl-blue/10 p-3">
          {footer}
        </div>
      )}

      {/* Bottom glow */}
      <div className="absolute bottom-0 left-0 right-0 h-32 pointer-events-none"
        style={{ background: "linear-gradient(to top, rgba(21,101,192,0.08) 0%, transparent 100%)" }} />
    </aside>
  );
};
