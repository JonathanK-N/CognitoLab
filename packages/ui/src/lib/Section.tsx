import React from "react";
import clsx from "clsx";

type SectionProps = {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
};

export const Section: React.FC<SectionProps> = ({ title, description, children, className }) => (
  <section className={clsx("space-y-3", className)}>
    <div>
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      {description && <p className="text-sm text-slate-500">{description}</p>}
    </div>
    <div>{children}</div>
  </section>
);
