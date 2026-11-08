import { useEffect, useState } from "react";
import { ApiError, listarAuditoria, type EventoAuditoria } from "../api";

const ETIQUETAS: Record<string, string> = {
  login: "Inicio de sesión",
  set_password: "Definición de contraseña",
  votar: "Voto registrado",
  crear_votacion: "Votación creada",
  cerrar_votacion: "Votación cerrada (manual)",
  crear_miembro: "Miembro creado",
  apertura_automatica: "Votación abierta (automático)",
  cierre_automatico: "Votación cerrada (automático)",
};

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleString("es-CO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function AuditoriaView() {
  const [eventos, setEventos] = useState<EventoAuditoria[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listarAuditoria()
      .then(setEventos)
      .catch((e) => setError(e instanceof ApiError ? e.message : "No se pudo conectar con el servidor."))
      .finally(() => setCargando(false));
  }, []);

  if (cargando) return <p>Cargando...</p>;
  if (error) return <p className="error-text">{error}</p>;

  if (eventos.length === 0) {
    return (
      <p className="empty-state">
        Sin eventos registrados todavía (o la auditoría no está configurada: ver MONGODB_URI en
        backend/.env).
      </p>
    );
  }

  return (
    <div className="panel">
      <table className="auditoria-tabla">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Acción</th>
            <th>Miembro</th>
            <th>Detalle</th>
          </tr>
        </thead>
        <tbody>
          {eventos.map((e, i) => (
            <tr key={i}>
              <td>{formatFecha(e.fecha)}</td>
              <td>{ETIQUETAS[e.accion] ?? e.accion}</td>
              <td>{e.miembro_id ?? "sistema"}</td>
              <td>{Object.entries(e.detalle).map(([k, v]) => `${k}: ${v}`).join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
