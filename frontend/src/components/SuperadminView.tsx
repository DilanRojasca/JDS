import { useEffect, useState, type FormEvent } from "react";
import {
  ApiError,
  crearOrganizacion,
  listarMiembros,
  listarOrganizaciones,
  type Miembro,
  type Organizacion,
} from "../api";

export function SuperadminView() {
  const [organizaciones, setOrganizaciones] = useState<Organizacion[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [nombreOrg, setNombreOrg] = useState("");
  const [creando, setCreando] = useState(false);
  const [errorCrear, setErrorCrear] = useState<string | null>(null);

  const [orgSeleccionada, setOrgSeleccionada] = useState<Organizacion | null>(null);
  const [miembros, setMiembros] = useState<Miembro[] | null>(null);
  const [cargandoMiembros, setCargandoMiembros] = useState(false);

  function cargarOrganizaciones() {
    listarOrganizaciones()
      .then(setOrganizaciones)
      .catch((e) => setError(e instanceof ApiError ? e.message : "No se pudo conectar con el servidor."))
      .finally(() => setCargando(false));
  }

  // cargando arranca en true (useState(true)): no hace falta volver a
  // ponerlo aqui, asi el efecto no llama a setState de forma sincronica.
  useEffect(() => {
    cargarOrganizaciones();
  }, []);

  async function enviarOrganizacion(e: FormEvent) {
    e.preventDefault();
    setErrorCrear(null);
    setCreando(true);
    try {
      await crearOrganizacion(nombreOrg.trim());
      setNombreOrg("");
      cargarOrganizaciones();
    } catch (err) {
      setErrorCrear(err instanceof ApiError ? err.message : "No se pudo conectar con el servidor.");
    } finally {
      setCreando(false);
    }
  }

  function verMiembros(org: Organizacion) {
    setOrgSeleccionada(org);
    setMiembros(null);
    setCargandoMiembros(true);
    listarMiembros(org.organizacion_id)
      .then(setMiembros)
      .catch(() => setMiembros([]))
      .finally(() => setCargandoMiembros(false));
  }

  return (
    <div className="admin-panel">
      <section className="panel">
        <h2>Nueva organización</h2>
        <form onSubmit={enviarOrganizacion}>
          <div className="field">
            <label htmlFor="nombre-org">Nombre</label>
            <input
              id="nombre-org"
              required
              value={nombreOrg}
              onChange={(e) => setNombreOrg(e.target.value)}
            />
          </div>
          {errorCrear && <p className="error-text">{errorCrear}</p>}
          <button className="primary-button" type="submit" disabled={creando || !nombreOrg.trim()}>
            {creando ? "Creando..." : "Crear organización"}
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Organizaciones</h2>
        {cargando && <p>Cargando...</p>}
        {error && <p className="error-text">{error}</p>}
        {!cargando && !error && (
          <table className="auditoria-tabla">
            <thead>
              <tr>
                <th>Id</th>
                <th>Nombre</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {organizaciones.map((o) => (
                <tr key={o.organizacion_id}>
                  <td>{o.organizacion_id}</td>
                  <td>{o.nombre}</td>
                  <td>
                    <button className="link-button" onClick={() => verMiembros(o)}>
                      Ver miembros
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {orgSeleccionada && (
        <section className="panel">
          <h2>Miembros de {orgSeleccionada.nombre}</h2>
          {cargandoMiembros && <p>Cargando...</p>}
          {!cargandoMiembros && miembros && miembros.length === 0 && (
            <p className="empty-state">Sin miembros registrados.</p>
          )}
          {!cargandoMiembros && miembros && miembros.length > 0 && (
            <table className="auditoria-tabla">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Peso de voto</th>
                  <th>Rol</th>
                </tr>
              </thead>
              <tbody>
                {miembros.map((m) => (
                  <tr key={m.miembro_id}>
                    <td>{m.nombre}</td>
                    <td>{m.peso_voto.toFixed(2)}</td>
                    <td>{m.rol}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}
