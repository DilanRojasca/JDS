import { useEffect, useState } from "react";
import {
  obtenerVotacion,
  registrarVoto,
  type Miembro,
  type VotacionDetalle,
} from "../api";

interface Props {
  votacionId: number;
  miembro: Miembro;
  onVolver: () => void;
}

export function VotarView({ votacionId, miembro, onVolver }: Props) {
  const [votacion, setVotacion] = useState<VotacionDetalle | null>(null);
  const [opcionId, setOpcionId] = useState<number | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setVotacion(null);
    setOpcionId(null);
    setMensaje(null);
    setError(null);
    obtenerVotacion(votacionId)
      .then(setVotacion)
      .catch((e) => setError(e.message));
  }, [votacionId]);

  async function enviar() {
    if (opcionId === null) return;
    setEnviando(true);
    setError(null);
    try {
      const res = await registrarVoto(votacionId, opcionId);
      setMensaje(res.mensaje);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo registrar el voto");
    } finally {
      setEnviando(false);
    }
  }

  if (error && !votacion) {
    return (
      <div className="panel">
        <button className="link-button" onClick={onVolver}>&larr; Volver</button>
        <p className="error-text">{error}</p>
      </div>
    );
  }

  if (!votacion) return <p>Cargando...</p>;

  return (
    <div className="panel">
      <button className="link-button" onClick={onVolver}>&larr; Volver a votaciones</button>
      <h2>{votacion.titulo}</h2>
      {votacion.descripcion && <p className="descripcion">{votacion.descripcion}</p>}
      <p className="meta">
        Quórum requerido: {votacion.quorum_requerido.toFixed(2)} · Tu peso de voto:{" "}
        {miembro.peso_voto.toFixed(2)} ({miembro.nombre})
      </p>

      {mensaje ? (
        <p className="success-text">{mensaje}</p>
      ) : (
        <>
          <div className="opciones">
            {votacion.opciones.map((op) => (
              <label key={op.opcion_id} className="opcion">
                <input
                  type="radio"
                  name="opcion"
                  checked={opcionId === op.opcion_id}
                  onChange={() => setOpcionId(op.opcion_id)}
                />
                {op.texto_opcion}
              </label>
            ))}
          </div>

          {error && <p className="error-text">{error}</p>}

          <button
            className="primary-button"
            disabled={opcionId === null || enviando}
            onClick={enviar}
          >
            {enviando ? "Enviando..." : "Confirmar voto"}
          </button>
        </>
      )}
    </div>
  );
}
