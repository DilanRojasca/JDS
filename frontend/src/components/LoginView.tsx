import { useState, type FormEvent } from "react";
import { ApiError, login, type MiembroSesion } from "../api";

interface Props {
  onLogin: (miembro: MiembroSesion) => void;
  aviso?: string | null;
}

export function LoginView({ onLogin, aviso }: Props) {
  const [identificacion, setIdentificacion] = useState("");
  const [password, setPassword] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      const { miembro } = await login(identificacion.trim(), password);
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

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={enviar}>
        <div className="login-brand">VotaCoop</div>
        <p className="login-subtitle">Inicia sesión para participar en las votaciones.</p>

        {aviso && !error && <p className="aviso-text">{aviso}</p>}

        <div className="field">
          <label htmlFor="identificacion">Identificación</label>
          <input
            id="identificacion"
            type="text"
            autoComplete="username"
            autoFocus
            required
            value={identificacion}
            onChange={(e) => setIdentificacion(e.target.value)}
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
        </div>

        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}

        <button
          className="primary-button"
          type="submit"
          disabled={enviando || !identificacion.trim() || !password}
        >
          {enviando ? "Ingresando..." : "Ingresar"}
        </button>
      </form>
    </div>
  );
}
