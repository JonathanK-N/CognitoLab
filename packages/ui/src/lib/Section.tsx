import React from "react";
import clsx from "clsx";

type SectionProps = {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
};

export const Section: React.FC<SectionProps> = ({ title, description, children, className }) => (
  <section className={clsx("space-y-4", className)}>
    <div>
      <h2 className="section-title">{title}</h2>
      {description && <p className="section-sub">{description}</p>}
    </div>
    <div>{children}</div>
  </section>
);
