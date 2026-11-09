import { useState, type FormEvent } from "react";
import { ApiError, login, olvidePassword, type MiembroSesion } from "../api";

interface Props {
  onLogin: (miembro: MiembroSesion) => void;
  aviso?: string | null;
}

export function LoginView({ onLogin, aviso }: Props) {
  const [nombre, setNombre] = useState("");
  const [password, setPassword] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mostrarRecuperar, setMostrarRecuperar] = useState(false);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      const { miembro } = await login(nombre.trim(), password);
      onLogin(miembro);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo conectar con el servidor. ¿Está corriendo la API?",
      );
    } finally {
      setEnviando(false);
    }
  }

  if (mostrarRecuperar) {
    return <RecuperarPasswordView onVolver={() => setMostrarRecuperar(false)} />;
  }

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={enviar}>
        <div className="login-brand">VotaCoop</div>
        <p className="login-subtitle">Inicia sesión para participar en las votaciones.</p>

        {aviso && !error && <p className="aviso-text">{aviso}</p>}

        <div className="field">
          <label htmlFor="nombre">Nombre completo</label>
          <input
            id="nombre"
            type="text"
            autoComplete="username"
            autoFocus
            required
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <p className="field-help">
            Si es tu primer ingreso, usa tu número de documento como contraseña.
          </p>
        </div>

        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}

        <button
          className="primary-button"
          type="submit"
          disabled={enviando || !nombre.trim() || !password}
        >
          {enviando ? "Ingresando..." : "Ingresar"}
        </button>

        <button
          type="button"
          className="link-button"
          onClick={() => setMostrarRecuperar(true)}
        >
          ¿Olvidaste tu contraseña?
        </button>
      </form>
    </div>
  );
}

function RecuperarPasswordView({ onVolver }: { onVolver: () => void }) {
  const [nombre, setNombre] = useState("");
  const [identificacion, setIdentificacion] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      const r = await olvidePassword(nombre.trim(), identificacion.trim());
      setMensaje(r.mensaje);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo conectar con el servidor. ¿Está corriendo la API?",
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={enviar}>
        <div className="login-brand">VotaCoop</div>
        <p className="login-subtitle">
          Indica tu nombre completo y tu número de documento. Si coinciden con un miembro
          registrado, podrás volver a entrar usando tu documento como contraseña temporal.
        </p>

        <div className="field">
          <label htmlFor="r-nombre">Nombre completo</label>
          <input
            id="r-nombre"
            type="text"
            autoFocus
            required
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="r-identificacion">Número de documento</label>
          <input
            id="r-identificacion"
            type="text"
            required
            value={identificacion}
            onChange={(e) => setIdentificacion(e.target.value)}
          />
        </div>

        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}
        {mensaje && <p className="success-text">{mensaje}</p>}

        <button
          className="primary-button"
          type="submit"
          disabled={enviando || !nombre.trim() || !identificacion.trim() || mensaje !== null}
        >
          {enviando ? "Enviando..." : "Recuperar acceso"}
        </button>

        <button type="button" className="link-button" onClick={onVolver}>
          ← Volver a iniciar sesión
        </button>
      </form>
    </div>
  );
}
