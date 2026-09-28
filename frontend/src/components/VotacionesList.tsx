import type { VotacionResumen } from "../api";

interface Props {
  votaciones: VotacionResumen[];
  onSeleccionar: (id: number, estado: string) => void;
  onVerResultados: (id: number) => void;
}

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleString("es-CO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function VotacionesList({ votaciones, onSeleccionar, onVerResultados }: Props) {
  if (votaciones.length === 0) {
    return <p className="empty-state">No hay votaciones registradas todavía.</p>;
  }

  return (
    <div className="votaciones-list">
      {votaciones.map((v) => (
        <div key={v.votacion_id} className={`votacion-card estado-${v.estado.toLowerCase()}`}>
          <button className="votacion-card-main" onClick={() => onSeleccionar(v.votacion_id, v.estado)}>
            <div className="votacion-card-header">
              <span className={`badge badge-${v.estado.toLowerCase()}`}>{v.estado}</span>
              <span className="votacion-fecha">Cierra: {formatFecha(v.fecha_cierre)}</span>
            </div>
            <h3>{v.titulo}</h3>
            <span className="votacion-quorum">Quórum requerido: {v.quorum_requerido.toFixed(2)}</span>
          </button>
          <button
            className="link-button votacion-resultados-link"
            onClick={() => onVerResultados(v.votacion_id)}
          >
            Ver resultados →
          </button>
        </div>
      ))}
    </div>
  );
}
