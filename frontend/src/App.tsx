import { useEffect, useState } from "react";
import "./App.css";
import {
  listarMiembros,
  listarOrganizaciones,
  listarVotaciones,
  type Miembro,
  type Organizacion,
  type VotacionResumen,
} from "./api";
import { VotacionesList } from "./components/VotacionesList";
import { VotarView } from "./components/VotarView";
import { ResultadosView } from "./components/ResultadosView";

type Vista =
  | { tipo: "lista" }
  | { tipo: "votar"; votacionId: number }
  | { tipo: "resultados"; votacionId: number };

function App() {
  const [organizacion, setOrganizacion] = useState<Organizacion | null>(null);
  const [miembros, setMiembros] = useState<Miembro[]>([]);
  const [miembroId, setMiembroId] = useState<number | null>(null);
  const [votaciones, setVotaciones] = useState<VotacionResumen[]>([]);
  const [vista, setVista] = useState<Vista>({ tipo: "lista" });
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listarOrganizaciones()
      .then(async (orgs) => {
        if (orgs.length === 0) {
          setError("No hay organizaciones registradas todavía.");
          setCargando(false);
          return;
        }
        const org = orgs[0];
        setOrganizacion(org);
        const [ms, vs] = await Promise.all([
          listarMiembros(org.organizacion_id),
          listarVotaciones(org.organizacion_id),
        ]);
        setMiembros(ms);
        setMiembroId(ms[0]?.miembro_id ?? null);
        setVotaciones(vs);
        setCargando(false);
      })
      .catch((e) => {
        setError(
          e instanceof Error
            ? `No se pudo conectar con la API (${e.message}). ¿Está corriendo "python -m uvicorn app.main:app --reload" en backend/?`
            : "Error desconocido"
        );
        setCargando(false);
      });
  }, []);

  function recargarVotaciones() {
    if (!organizacion) return;
    listarVotaciones(organizacion.organizacion_id).then(setVotaciones);
  }

  const miembroActual = miembros.find((m) => m.miembro_id === miembroId) ?? null;

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">VotaCoop</div>
        {organizacion && <div className="org-name">{organizacion.nombre}</div>}
        {miembros.length > 0 && (
          <select
            className="miembro-select"
            value={miembroId ?? ""}
            onChange={(e) => setMiembroId(Number(e.target.value))}
          >
            {miembros.map((m) => (
              <option key={m.miembro_id} value={m.miembro_id}>
                {m.nombre} (peso {m.peso_voto.toFixed(2)})
              </option>
            ))}
          </select>
        )}
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

        {vista.tipo === "votar" && miembroActual && (
          <VotarView
            votacionId={vista.votacionId}
            miembro={miembroActual}
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
