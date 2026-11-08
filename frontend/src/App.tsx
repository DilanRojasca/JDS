import { useCallback, useEffect, useState } from "react";
import "./App.css";
import {
  ApiError,
  cerrarVotacion,
  clearToken,
  getToken,
  listarVotaciones,
  obtenerMe,
  setUnauthorizedHandler,
  type MiembroSesion,
  type VotacionResumen,
} from "./api";
import { AdminPanelView } from "./components/AdminPanelView";
import { AuditoriaView } from "./components/AuditoriaView";
import { CambiarPasswordView } from "./components/CambiarPasswordView";
import { LoginView } from "./components/LoginView";
import { Sidebar, type SidebarItem } from "./components/Sidebar";
import { SuperadminView } from "./components/SuperadminView";
import { VotacionesList } from "./components/VotacionesList";
import { VotarView } from "./components/VotarView";
import { ResultadosView } from "./components/ResultadosView";
import { IconAdmin, IconAuditoria, IconMenu, IconOrganizaciones, IconVotaciones } from "./icons";

type Vista =
  | { tipo: "lista" }
  | { tipo: "votar"; votacionId: number }
  | { tipo: "resultados"; votacionId: number }
  | { tipo: "admin" }
  | { tipo: "auditoria" }
  | { tipo: "superadmin" };

const TITULOS: Record<Vista["tipo"], string> = {
  lista: "Votaciones",
  votar: "Votaciones",
  resultados: "Votaciones",
  admin: "Administración",
  auditoria: "Auditoría",
  superadmin: "Organizaciones",
};

const MENSAJE_CONEXION =
  'No se pudo conectar con la API. ¿Está corriendo "python -m uvicorn app.main:app --reload" en backend/?';

function App() {
  const [sesion, setSesion] = useState<MiembroSesion | null>(null);
  // Si hay un token guardado, primero hay que validarlo contra la API.
  const [verificando, setVerificando] = useState(() => getToken() !== null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [votaciones, setVotaciones] = useState<VotacionResumen[]>([]);
  const [vista, setVista] = useState<Vista>({ tipo: "lista" });
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarAbierto, setSidebarAbierto] = useState(false);

  const entrar = useCallback(async (miembro: MiembroSesion) => {
    setSesion(miembro);
    setAviso(null);
    setError(null);
    setVista({ tipo: "lista" });

    // Con clave temporal (el documento) el resto de la API responde 403
    // hasta que el miembro defina una clave propia: no hay votaciones que
    // cargar todavia, CambiarPasswordView se encarga de lo siguiente.
    if (miembro.debe_cambiar_password) return;

    setCargando(true);
    try {
      setVotaciones(await listarVotaciones());
    } catch (e) {
      // Un 401 ya lo maneja el handler de sesion vencida.
      if (!(e instanceof ApiError && e.status === 401)) {
        setError(e instanceof ApiError ? e.message : MENSAJE_CONEXION);
      }
    } finally {
      setCargando(false);
    }
  }, []);

  const cerrarSesion = useCallback(() => {
    clearToken();
    setSesion(null);
    setVotaciones([]);
    setVista({ tipo: "lista" });
    setError(null);
    setAviso(null);
  }, []);

  // Token vencido o invalido en cualquier peticion -> volver al login.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      cerrarSesion();
      setAviso("Tu sesión expiró. Inicia sesión de nuevo.");
    });
    return () => setUnauthorizedHandler(null);
  }, [cerrarSesion]);

  // Al abrir/recargar la pagina: restaurar la sesion si el token sigue valido.
  useEffect(() => {
    if (getToken() === null) return;
    obtenerMe()
      .then(entrar)
      .catch((e) => {
        if (!(e instanceof ApiError && e.status === 401)) setAviso(MENSAJE_CONEXION);
      })
      .finally(() => setVerificando(false));
  }, [entrar]);

  function recargarVotaciones() {
    listarVotaciones()
      .then(setVotaciones)
      .catch(() => {});
  }

  async function cerrarVotacionYRecargar(votacionId: number) {
    try {
      await cerrarVotacion(votacionId);
      recargarVotaciones();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : MENSAJE_CONEXION);
    }
  }

  function navegar(v: Vista) {
    setVista(v);
    setSidebarAbierto(false);
  }

  if (verificando) {
    return <p className="app-loading">Cargando...</p>;
  }

  if (!sesion) {
    return <LoginView onLogin={entrar} aviso={aviso} />;
  }

  if (sesion.debe_cambiar_password) {
    return (
      <CambiarPasswordView
        nombre={sesion.nombre}
        onCambiada={() => entrar({ ...sesion, debe_cambiar_password: false })}
      />
    );
  }

  const enSeccionVotaciones = vista.tipo === "lista" || vista.tipo === "votar" || vista.tipo === "resultados";

  const items: SidebarItem[] = [
    {
      key: "lista",
      label: "Votaciones",
      icon: IconVotaciones,
      activo: enSeccionVotaciones,
      onClick: () => navegar({ tipo: "lista" }),
    },
  ];

  if (sesion.rol === "Administrador") {
    items.push({
      key: "admin",
      label: "Administración",
      icon: IconAdmin,
      activo: vista.tipo === "admin",
      onClick: () => navegar({ tipo: "admin" }),
    });
  }

  if (sesion.rol === "Administrador" || sesion.rol === "Auditor" || sesion.rol === "Superadministrador") {
    items.push({
      key: "auditoria",
      label: "Auditoría",
      icon: IconAuditoria,
      activo: vista.tipo === "auditoria",
      onClick: () => navegar({ tipo: "auditoria" }),
    });
  }

  if (sesion.rol === "Superadministrador") {
    items.push({
      key: "superadmin",
      label: "Organizaciones",
      icon: IconOrganizaciones,
      activo: vista.tipo === "superadmin",
      onClick: () => navegar({ tipo: "superadmin" }),
    });
  }

  return (
    <div className="app-shell">
      <Sidebar
        sesion={sesion}
        items={items}
        abierto={sidebarAbierto}
        onCerrar={() => setSidebarAbierto(false)}
        onLogout={cerrarSesion}
      />

      <div className="app-content">
        <div className="mobile-topbar">
          <button
            className="mobile-menu-button"
            onClick={() => setSidebarAbierto(true)}
            aria-label="Abrir menú"
          >
            <IconMenu />
          </button>
          <span className="mobile-topbar-brand">VotaCoop</span>
        </div>

        <main className="app-main">
          {cargando && <p>Cargando...</p>}
          {error && <p className="error-text">{error}</p>}

          {!cargando && !error && vista.tipo === "lista" && (
            <>
              <h1>{TITULOS[vista.tipo]}</h1>
              <VotacionesList
                votaciones={votaciones}
                onSeleccionar={(id, estado) =>
                  setVista(
                    estado === "Cerrada" || estado === "Anulada"
                      ? { tipo: "resultados", votacionId: id }
                      : { tipo: "votar", votacionId: id }
                  )
                }
                onVerResultados={(id) => setVista({ tipo: "resultados", votacionId: id })}
                esAdmin={sesion.rol === "Administrador"}
                onCerrar={cerrarVotacionYRecargar}
              />
            </>
          )}

          {vista.tipo === "votar" && (
            <VotarView
              votacionId={vista.votacionId}
              miembro={sesion}
              onVolver={() => {
                recargarVotaciones();
                setVista({ tipo: "lista" });
              }}
            />
          )}

          {vista.tipo === "resultados" && (
            <ResultadosView
              votacionId={vista.votacionId}
              onVolver={() => setVista({ tipo: "lista" })}
            />
          )}

          {vista.tipo === "admin" && sesion.rol === "Administrador" && (
            <>
              <h1>{TITULOS[vista.tipo]}</h1>
              <AdminPanelView miembro={sesion} onVotacionCreada={recargarVotaciones} />
            </>
          )}

          {vista.tipo === "auditoria" &&
            (sesion.rol === "Administrador" || sesion.rol === "Auditor" || sesion.rol === "Superadministrador") && (
              <>
                <h1>{TITULOS[vista.tipo]}</h1>
                <AuditoriaView />
              </>
            )}

          {vista.tipo === "superadmin" && sesion.rol === "Superadministrador" && (
            <>
              <h1>{TITULOS[vista.tipo]}</h1>
              <SuperadminView />
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
