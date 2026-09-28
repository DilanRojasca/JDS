const API_BASE = "http://localhost:8000";
const TOKEN_KEY = "votacoop_token";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

// ---- Sesion (token guardado en localStorage, sobrevive a recargar la pagina) ----

export const getToken = (): string | null => {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
};

const setToken = (token: string) => {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* almacenamiento bloqueado: la sesion durara hasta recargar */
  }
};

export const clearToken = () => {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* nada que limpiar */
  }
};

// La API responde 401 cuando el token vence o deja de ser valido; App se
// registra aqui para volver a la pantalla de login.
let onUnauthorized: (() => void) | null = null;
export const setUnauthorizedHandler = (fn: (() => void) | null) => {
  onUnauthorized = fn;
};

export interface Organizacion {
  organizacion_id: number;
  nombre: string;
}

export interface Miembro {
  miembro_id: number;
  nombre: string;
  peso_voto: number;
}

export interface MiembroSesion extends Miembro {
  organizacion_id: number;
  organizacion_nombre: string;
}

export interface LoginRespuesta {
  access_token: string;
  token_type: string;
  miembro: MiembroSesion;
}

export interface VotacionResumen {
  votacion_id: number;
  titulo: string;
  estado: string;
  fecha_apertura: string;
  fecha_cierre: string;
  quorum_requerido: number;
}

export interface OpcionVoto {
  opcion_id: number;
  texto_opcion: string;
}

export interface VotacionDetalle extends VotacionResumen {
  descripcion: string | null;
  opciones: OpcionVoto[];
}

export interface OpcionResultado {
  opcion_id: number;
  texto_opcion: string;
  peso: number;
  votos: number;
}

export interface ResultadoVotacion {
  votacion_id: number;
  titulo: string;
  quorum_requerido: number;
  peso_total_votado: number;
  quorum_alcanzado: boolean;
  estado: string;
  fecha_apertura: string;
  fecha_cierre: string;
  peso_total_padron: number;
  miembros_total: number;
  miembros_votantes: number;
  opciones: OpcionResultado[];
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  conSesion = true,
): Promise<T> {
  const token = conSesion ? getToken() : null;
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (!res.ok) {
    if (res.status === 401 && conSesion) {
      clearToken();
      onUnauthorized?.();
    }
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    // En errores de validacion (422) FastAPI devuelve detail como lista.
    const mensaje = typeof body.detail === "string" ? body.detail : `Error ${res.status}`;
    throw new ApiError(mensaje, res.status);
  }
  return res.json() as Promise<T>;
}

export async function login(identificacion: string, password: string): Promise<LoginRespuesta> {
  const r = await apiFetch<LoginRespuesta>(
    "/auth/login",
    { method: "POST", body: JSON.stringify({ identificacion, password }) },
    false, // sin sesion: un 401 aqui es "credenciales malas", no "sesion vencida"
  );
  setToken(r.access_token);
  return r;
}

export const obtenerMe = () => apiFetch<MiembroSesion>("/auth/me");

export const listarOrganizaciones = () => apiFetch<Organizacion[]>("/organizaciones");

export const listarMiembros = (organizacionId: number) =>
  apiFetch<Miembro[]>(`/organizaciones/${organizacionId}/miembros`);

export const listarVotaciones = () => apiFetch<VotacionResumen[]>("/votaciones");

export const obtenerVotacion = (votacionId: number) =>
  apiFetch<VotacionDetalle>(`/votaciones/${votacionId}`);

export const obtenerResultado = (votacionId: number) =>
  apiFetch<ResultadoVotacion>(`/votaciones/${votacionId}/resultado`);

// El miembro que vota lo determina el servidor a partir del token.
export const registrarVoto = (votacionId: number, opcionId: number) =>
  apiFetch<{ mensaje: string }>(`/votaciones/${votacionId}/votos`, {
    method: "POST",
    body: JSON.stringify({ opcion_id: opcionId }),
  });
