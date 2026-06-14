import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  subtitle: string;
  children: ReactNode;
  action?: ReactNode;
};

export function SectionCard({
  title,
  subtitle,
  children,
  action,
}: SectionCardProps) {
  return (
    <section className="section-card">
      <header className="section-card__header">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        {action}
      </header>
      {children}
    </section>
  );
}
