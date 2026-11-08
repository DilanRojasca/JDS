import { useState, type FormEvent } from "react";
import {
  ApiError,
  crearMiembro,
  crearVotacion,
  type MiembroSesion,
  type Rol,
} from "../api";

interface Props {
  miembro: MiembroSesion;
  onVotacionCreada: () => void;
}

function aIsoLocal(valorInputDatetime: string): string {
  // <input type="datetime-local"> entrega "2026-01-01T10:00" (sin zona);
  // se envia tal cual, la API lo interpreta como hora local del servidor.
  return valorInputDatetime;
}

export function AdminPanelView({ miembro, onVotacionCreada }: Props) {
  // ---- crear votacion ----
  const [titulo, setTitulo] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [quorum, setQuorum] = useState("");
  const [apertura, setApertura] = useState("");
  const [cierre, setCierre] = useState("");
  const [opciones, setOpciones] = useState(["A favor", "En contra"]);
  const [enviandoVotacion, setEnviandoVotacion] = useState(false);
  const [errorVotacion, setErrorVotacion] = useState<string | null>(null);
  const [okVotacion, setOkVotacion] = useState<string | null>(null);

  // ---- crear miembro ----
  const [identificacion, setIdentificacion] = useState("");
  const [nombre, setNombre] = useState("");
  const [pesoVoto, setPesoVoto] = useState("");
  const [rol, setRol] = useState<Rol>("Miembro");
  const [enviandoMiembro, setEnviandoMiembro] = useState(false);
  const [errorMiembro, setErrorMiembro] = useState<string | null>(null);
  const [okMiembro, setOkMiembro] = useState<string | null>(null);

  function actualizarOpcion(i: number, valor: string) {
    setOpciones((prev) => prev.map((o, idx) => (idx === i ? valor : o)));
  }

  function agregarOpcion() {
    setOpciones((prev) => [...prev, ""]);
  }

  function quitarOpcion(i: number) {
    setOpciones((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function enviarVotacion(e: FormEvent) {
    e.preventDefault();
    setErrorVotacion(null);
    setOkVotacion(null);

    const opcionesLimpias = opciones.map((o) => o.trim()).filter(Boolean);
    if (opcionesLimpias.length < 2) {
      setErrorVotacion("Se necesitan al menos 2 opciones de voto.");
      return;
    }

    setEnviandoVotacion(true);
    try {
      await crearVotacion({
        titulo,
        descripcion: descripcion.trim() || undefined,
        quorum_requerido: Number(quorum),
        fecha_apertura: aIsoLocal(apertura),
        fecha_cierre: aIsoLocal(cierre),
        opciones: opcionesLimpias,
      });
      setOkVotacion(`Votación "${titulo}" creada.`);
      setTitulo("");
      setDescripcion("");
      setQuorum("");
      setApertura("");
      setCierre("");
      setOpciones(["A favor", "En contra"]);
      onVotacionCreada();
    } catch (err) {
      setErrorVotacion(err instanceof ApiError ? err.message : "No se pudo conectar con el servidor.");
    } finally {
      setEnviandoVotacion(false);
    }
  }

  async function enviarMiembro(e: FormEvent) {
    e.preventDefault();
    setErrorMiembro(null);
    setOkMiembro(null);

    setEnviandoMiembro(true);
    try {
      await crearMiembro(miembro.organizacion_id, {
        identificacion: identificacion.trim(),
        nombre: nombre.trim(),
        peso_voto: Number(pesoVoto),
        rol,
      });
      setOkMiembro(`Miembro "${nombre}" creado. Entra con su documento (${identificacion}) como clave temporal.`);
      setIdentificacion("");
      setNombre("");
      setPesoVoto("");
      setRol("Miembro");
    } catch (err) {
      setErrorMiembro(err instanceof ApiError ? err.message : "No se pudo conectar con el servidor.");
    } finally {
      setEnviandoMiembro(false);
    }
  }

  return (
    <div className="admin-panel">
      <section className="panel">
        <h2>Nueva votación</h2>
        <form onSubmit={enviarVotacion}>
          <div className="field">
            <label htmlFor="titulo">Título</label>
            <input id="titulo" required value={titulo} onChange={(e) => setTitulo(e.target.value)} />
          </div>

          <div className="field">
            <label htmlFor="descripcion">Descripción (opcional)</label>
            <input id="descripcion" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
          </div>

          <div className="field">
            <label htmlFor="quorum">Quórum requerido (suma de pesos)</label>
            <input
              id="quorum"
              type="number"
              step="0.01"
              min="0.01"
              required
              value={quorum}
              onChange={(e) => setQuorum(e.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="apertura">Apertura</label>
            <input
              id="apertura"
              type="datetime-local"
              required
              value={apertura}
              onChange={(e) => setApertura(e.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="cierre">Cierre</label>
            <input
              id="cierre"
              type="datetime-local"
              required
              value={cierre}
              onChange={(e) => setCierre(e.target.value)}
            />
          </div>

          <div className="field">
            <label>Opciones de voto</label>
            {opciones.map((o, i) => (
              <div key={i} className="opcion-input-row">
                <input
                  required
                  value={o}
                  onChange={(e) => actualizarOpcion(i, e.target.value)}
                  placeholder={`Opción ${i + 1}`}
                />
                {opciones.length > 2 && (
                  <button type="button" className="link-button" onClick={() => quitarOpcion(i)}>
                    Quitar
                  </button>
                )}
              </div>
            ))}
            <button type="button" className="link-button" onClick={agregarOpcion}>
              + Agregar opción
            </button>
          </div>

          {errorVotacion && <p className="error-text">{errorVotacion}</p>}
          {okVotacion && <p className="success-text">{okVotacion}</p>}

          <button className="primary-button" type="submit" disabled={enviandoVotacion}>
            {enviandoVotacion ? "Creando..." : "Crear votación"}
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Nuevo miembro</h2>
        <form onSubmit={enviarMiembro}>
          <div className="field">
            <label htmlFor="identificacion">Identificación (documento)</label>
            <input
              id="identificacion"
              required
              value={identificacion}
              onChange={(e) => setIdentificacion(e.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="nombre-miembro">Nombre completo</label>
            <input id="nombre-miembro" required value={nombre} onChange={(e) => setNombre(e.target.value)} />
          </div>

          <div className="field">
            <label htmlFor="peso-voto">Peso de voto</label>
            <input
              id="peso-voto"
              type="number"
              step="0.01"
              min="0.01"
              required
              value={pesoVoto}
              onChange={(e) => setPesoVoto(e.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="rol-miembro">Rol</label>
            <select id="rol-miembro" value={rol} onChange={(e) => setRol(e.target.value as Rol)}>
              <option value="Miembro">Miembro</option>
              <option value="Administrador">Administrador</option>
              <option value="Auditor">Auditor</option>
            </select>
          </div>

          <p className="field-help">
            El miembro nuevo entra por primera vez con su nombre y su documento como contraseña
            temporal; la API lo obligará a definir una clave propia.
          </p>

          {errorMiembro && <p className="error-text">{errorMiembro}</p>}
          {okMiembro && <p className="success-text">{okMiembro}</p>}

          <button className="primary-button" type="submit" disabled={enviandoMiembro}>
            {enviandoMiembro ? "Creando..." : "Crear miembro"}
          </button>
        </form>
      </section>
    </div>
  );
}
