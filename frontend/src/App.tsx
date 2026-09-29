import { useCallback, useEffect, useState } from "react";
import "./App.css";
import {
  ApiError,
  clearToken,
  getToken,
  listarVotaciones,
  obtenerMe,
  setUnauthorizedHandler,
  type MiembroSesion,
  type VotacionResumen,
} from "./api";
import { CambiarPasswordView } from "./components/CambiarPasswordView";
import { LoginView } from "./components/LoginView";
import { VotacionesList } from "./components/VotacionesList";
import { VotarView } from "./components/VotarView";
import { ResultadosView } from "./components/ResultadosView";

type Vista =
  | { tipo: "lista" }
  | { tipo: "votar"; votacionId: number }
  | { tipo: "resultados"; votacionId: number };

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

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">VotaCoop</div>
        <div className="org-name">{sesion.organizacion_nombre}</div>
        <div className="header-user">
          <span>
            {sesion.nombre}{" "}
            <span className="header-user-peso">(peso {sesion.peso_voto.toFixed(2)})</span>
          </span>
          <button className="logout-button" onClick={cerrarSesion}>
            Cerrar sesión
          </button>
        </div>
      </header>

      <main className="app-main">
        {cargando && <p>Cargando...</p>}
        {error && <p className="error-text">{error}</p>}

        {!cargando && !error && vista.tipo === "lista" && (
          <>
            <h1>Votaciones</h1>
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
      </main>
    </div>
  );
}

export default App;
