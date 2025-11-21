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
    <div className="flex gap-2 border-b border-slate-200 mb-3">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onSelect(tab.id)}
          className={clsx(
            "px-4 py-2 text-sm font-medium border-b-2",
            selected === tab.id
              ? "border-indigo-600 text-indigo-700"
              : "border-transparent text-slate-600 hover:text-slate-800"
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
