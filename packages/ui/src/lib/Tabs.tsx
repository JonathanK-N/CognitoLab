import React from "react";
import clsx from "clsx";

export type TabItem = { id: string; label: string; content: React.ReactNode };

type TabsProps = {
  tabs: TabItem[];
  selected: string;
  onSelect(id: string): void;
};

export const Tabs: React.FC<TabsProps> = ({ tabs, selected, onSelect }) => (
  <div>
    <div className="flex gap-1 border-b border-cl-blue/10 mb-4">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onSelect(tab.id)}
          className={clsx(
            "px-4 py-2.5 text-sm font-medium border-b-2 transition-all",
            selected === tab.id
              ? "border-cl-blue-3 text-cl-blue-3 bg-cl-blue/5"
              : "border-transparent text-slate-500 hover:text-slate-300"
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
    <div>{tabs.find((t) => t.id === selected)?.content}</div>
  </div>
);

export const Tab: React.FC<{ children: React.ReactNode }> = ({ children }) => <>{children}</>;
