import { IconClose, IconLogout } from "../icons";
import type { MiembroSesion } from "../api";

export interface SidebarItem {
  key: string;
  label: string;
  icon: (props: { width?: number; height?: number }) => React.ReactNode;
  activo: boolean;
  onClick: () => void;
}

interface Props {
  sesion: MiembroSesion;
  items: SidebarItem[];
  abierto: boolean;
  onCerrar: () => void;
  onLogout: () => void;
}

function inicial(nombre: string): string {
  return nombre.trim().charAt(0).toUpperCase() || "?";
}

export function Sidebar({ sesion, items, abierto, onCerrar, onLogout }: Props) {
  return (
    <>
      <div className={`sidebar-backdrop ${abierto ? "abierto" : ""}`} onClick={onCerrar} />
      <aside className={`sidebar ${abierto ? "abierto" : ""}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">VC</div>
          <div>
            <div className="sidebar-brand-name">VOTACOOP</div>
            <div className="sidebar-brand-org">{sesion.organizacion_nombre}</div>
          </div>
          <button className="sidebar-close" onClick={onCerrar} aria-label="Cerrar menú">
            <IconClose />
          </button>
        </div>

        <nav className="sidebar-nav">
          {items.map((item) => (
            <button
              key={item.key}
              className={`sidebar-link ${item.activo ? "activo" : ""}`}
              onClick={item.onClick}
            >
              {item.icon({ width: 17, height: 17 })}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-avatar">{inicial(sesion.nombre)}</div>
          <div className="sidebar-user">
            <div className="sidebar-user-name">{sesion.nombre}</div>
            <div className="sidebar-user-meta">{sesion.rol}</div>
          </div>
          <button className="sidebar-logout" onClick={onLogout} aria-label="Cerrar sesión" title="Cerrar sesión">
            <IconLogout width={16} height={16} />
          </button>
        </div>
      </aside>
    </>
  );
}
