import type { ReactNode } from "react";
import type { PageId } from "../types/cube";
import {
  FactoryIcon,
  GridIcon,
  MenuIcon,
  ShieldIcon,
} from "./icons";

type LayoutProps = {
  activePage: PageId;
  children: ReactNode;
  onNavigate: (page: PageId) => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
};

const navigation = [
  { id: "dashboard" as const, label: "Vue globale", icon: GridIcon },
  { id: "production" as const, label: "Production", icon: FactoryIcon },
  { id: "quality" as const, label: "Qualité", icon: ShieldIcon },
];

export function Layout({
  activePage,
  children,
  onNavigate,
  sidebarOpen,
  onToggleSidebar,
}: LayoutProps) {
  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "sidebar--open" : ""}`}>
        <div className="brand">
          <span className="brand__mark">OS</span>
          <span>
            <strong>OpsSight</strong>
            <small>Industrial analytics</small>
          </span>
        </div>

        <nav className="navigation" aria-label="Navigation principale">
          <span className="navigation__label">Pilotage</span>
          {navigation.map(({ id, label, icon: Icon }) => (
            <button
              className={`navigation__item ${
                activePage === id ? "navigation__item--active" : ""
              }`}
              key={id}
              onClick={() => {
                onNavigate(id);
                onToggleSidebar();
              }}
              type="button"
            >
              <Icon />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar__footer">
          <span className="status-dot" />
          <span>
            <strong>Cube connecté</strong>
            <small>Données actualisées</small>
          </span>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          aria-label="Fermer la navigation"
          className="sidebar-overlay"
          onClick={onToggleSidebar}
          type="button"
        />
      )}

      <div className="main-panel">
        <header className="mobile-header">
          <button
            aria-label="Ouvrir la navigation"
            className="icon-button"
            onClick={onToggleSidebar}
            type="button"
          >
            <MenuIcon />
          </button>
          <strong>OpsSight</strong>
          <span className="mobile-header__live">Live</span>
        </header>
        <main className="page">{children}</main>
      </div>
    </div>
  );
}
