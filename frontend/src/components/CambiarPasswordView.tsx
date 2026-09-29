import { useState, type FormEvent } from "react";
import { ApiError, cambiarPassword } from "../api";

interface Props {
  nombre: string;
  onCambiada: () => void;
}

const LONGITUD_MINIMA = 8;

export function CambiarPasswordView({ nombre, onCambiada }: Props) {
  const [nueva, setNueva] = useState("");
  const [repetir, setRepetir] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (nueva.length < LONGITUD_MINIMA) {
      setError(`La contraseña debe tener al menos ${LONGITUD_MINIMA} caracteres.`);
      return;
    }
    if (nueva !== repetir) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setEnviando(true);
    try {
      await cambiarPassword(nueva);
      onCambiada();
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
          Hola, {nombre}. Este es tu primer ingreso: define una contraseña propia antes de
          continuar. Tu documento deja de servir como contraseña una vez la definas.
        </p>

        <div className="field">
          <label htmlFor="nueva">Nueva contraseña</label>
          <input
            id="nueva"
            type="password"
            autoComplete="new-password"
            autoFocus
            required
            minLength={LONGITUD_MINIMA}
            value={nueva}
            onChange={(e) => setNueva(e.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="repetir">Repite la contraseña</label>
          <input
            id="repetir"
            type="password"
            autoComplete="new-password"
            required
            minLength={LONGITUD_MINIMA}
            value={repetir}
            onChange={(e) => setRepetir(e.target.value)}
          />
        </div>

        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}

        <button className="primary-button" type="submit" disabled={enviando || !nueva || !repetir}>
          {enviando ? "Guardando..." : "Guardar contraseña"}
        </button>
      </form>
    </div>
  );
}
