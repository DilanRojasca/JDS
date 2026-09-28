const API_BASE = "http://localhost:8000";

export interface Organizacion {
  organizacion_id: number;
  nombre: string;
}

export interface Miembro {
  miembro_id: number;
  nombre: string;
  peso_voto: number;
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

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const listarOrganizaciones = () => apiFetch<Organizacion[]>("/organizaciones");

export const listarMiembros = (organizacionId: number) =>
  apiFetch<Miembro[]>(`/organizaciones/${organizacionId}/miembros`);

export const listarVotaciones = (organizacionId: number) =>
  apiFetch<VotacionResumen[]>(`/votaciones?organizacion_id=${organizacionId}`);

export const obtenerVotacion = (votacionId: number) =>
  apiFetch<VotacionDetalle>(`/votaciones/${votacionId}`);

export const obtenerResultado = (votacionId: number) =>
  apiFetch<ResultadoVotacion>(`/votaciones/${votacionId}/resultado`);

export const registrarVoto = (votacionId: number, miembroId: number, opcionId: number) =>
  apiFetch<{ mensaje: string }>(`/votaciones/${votacionId}/votos`, {
    method: "POST",
    body: JSON.stringify({ miembro_id: miembroId, opcion_id: opcionId }),
  });
