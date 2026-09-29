import { useState, type FormEvent } from "react";
import { ApiError, login, type MiembroSesion } from "../api";

interface Props {
  onLogin: (miembro: MiembroSesion) => void;
  aviso?: string | null;
}

export function LoginView({ onLogin, aviso }: Props) {
  const [nombre, setNombre] = useState("");
  const [password, setPassword] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      </form>
    </div>
  );
}
