import { useEffect, useState } from "react";
import { obtenerResultado, type ResultadoVotacion } from "../api";

interface Props {
  votacionId: number;
  onVolver: () => void;
}

const COLORES_OPCION = ["#1f6b54", "#b3402c", "#8b8577", "#93501e", "#2c5f6f"];

export function ResultadosView({ votacionId, onVolver }: Props) {
  const [resultado, setResultado] = useState<ResultadoVotacion | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setResultado(null);
    setError(null);
    obtenerResultado(votacionId)
      .then(setResultado)
      .catch((e) => setError(e.message));

    const interval = setInterval(() => {
      obtenerResultado(votacionId).then(setResultado).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, [votacionId]);

  if (error) {
    return (
      <div className="panel">
        <button className="link-button" onClick={onVolver}>&larr; Volver</button>
        <p className="error-text">{error}</p>
      </div>
    );
  }

  if (!resultado) return <p>Cargando...</p>;

  const porcentajeQuorum = resultado.quorum_requerido > 0
    ? Math.min(100, (resultado.peso_total_votado / resultado.quorum_requerido) * 100)
    : 0;

  const porcentajePadron = resultado.peso_total_padron > 0
    ? (resultado.peso_total_votado / resultado.peso_total_padron) * 100
    : 0;

  const pesoMaxOpcion = Math.max(1, ...resultado.opciones.map((o) => o.peso));

  return (
    <div className="panel resultado-panel">
      <button className="link-button" onClick={onVolver}>&larr; Volver a votaciones</button>

      <div className="resultado-header">
        <div>
          <span className={`badge badge-${resultado.estado.toLowerCase()}`}>{resultado.estado}</span>
          <h2>{resultado.titulo}</h2>
        </div>
      </div>

      <div className={`quorum-meter ${resultado.quorum_alcanzado ? "ok" : "warn"}`}>
        <div className="quorum-meter-top">
          <div className="quorum-meter-label">
            {resultado.quorum_alcanzado ? (
              <>
                <span className="quorum-icon">✓</span> Quórum alcanzado
              </>
            ) : (
              <>
                <span className="quorum-icon">○</span> Quórum aún no alcanzado
              </>
            )}
          </div>
          <div className="quorum-meter-value">
            {resultado.peso_total_votado.toFixed(2)}{" "}
            <span className="quorum-meter-value-muted">/ {resultado.quorum_requerido.toFixed(2)} requerido</span>
          </div>
        </div>
        <div className="quorum-meter-bar">
          <div className="quorum-meter-fill" style={{ width: `${porcentajeQuorum}%` }} />
          <div className="quorum-meter-threshold" style={{ left: "100%" }} />
        </div>
        <div className="quorum-meter-sub">{porcentajeQuorum.toFixed(0)}% del quórum requerido</div>
      </div>

      <div className="stat-row">
        <div className="stat-tile">
          <span className="stat-label">Miembros que votaron</span>
          <span className="stat-value">
            {resultado.miembros_votantes} <span className="stat-value-muted">/ {resultado.miembros_total}</span>
          </span>
        </div>
        <div className="stat-tile">
          <span className="stat-label">Participación ponderada</span>
          <span className="stat-value">{porcentajePadron.toFixed(1)}%</span>
        </div>
        <div className="stat-tile">
          <span className="stat-label">Peso total del padrón</span>
          <span className="stat-value">{resultado.peso_total_padron.toFixed(2)}</span>
        </div>
      </div>

      <div className="opciones-resultado">
        <h3>Resultado por opción (peso ponderado)</h3>
        {resultado.opciones.map((op, i) => {
          const pct = resultado.peso_total_votado > 0 ? (op.peso / resultado.peso_total_votado) * 100 : 0;
          return (
            <div key={op.opcion_id} className="opcion-resultado-row">
              <div className="opcion-resultado-header">
                <span>{op.texto_opcion}</span>
                <span className="opcion-resultado-meta">
                  {op.peso.toFixed(2)} pts · {op.votos} voto{op.votos === 1 ? "" : "s"} · {pct.toFixed(0)}%
                </span>
              </div>
              <div className="opcion-resultado-bar">
                <div
                  className="opcion-resultado-fill"
                  style={{
                    width: `${(op.peso / pesoMaxOpcion) * 100}%`,
                    background: COLORES_OPCION[i % COLORES_OPCION.length],
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
