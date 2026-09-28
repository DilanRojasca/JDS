from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Connection, text
from sqlalchemy.exc import DBAPIError

from app.db import get_connection
from app.schemas import (
    MiembroSesion,
    OpcionResultado,
    OpcionVoto,
    ResultadoVotacion,
    VotacionDetalle,
    VotacionResumen,
    VotoConfirmacion,
    VotoCrear,
)
from app.security import get_current_member

router = APIRouter(prefix="/votaciones", tags=["votaciones"])


def _exigir_votacion_de_mi_organizacion(
    conn: Connection, votacion_id: int, actual: MiembroSesion
) -> None:
    """404 si la votacion no existe o es de otra organizacion.

    Se responde igual en ambos casos para no revelar que ids existen en
    otras organizaciones.
    """
    org_id = conn.execute(
        text("SELECT OrganizacionId FROM Votaciones WHERE VotacionId = :votacion_id"),
        {"votacion_id": votacion_id},
    ).scalar()
    if org_id is None or org_id != actual.organizacion_id:
        raise HTTPException(status_code=404, detail="Votación no encontrada")


@router.get("", response_model=list[VotacionResumen])
def listar_votaciones(
    conn: Connection = Depends(get_connection),
    actual: MiembroSesion = Depends(get_current_member),
) -> list[VotacionResumen]:
    rows = conn.execute(
        text(
            """
            SELECT VotacionId, Titulo, Estado, FechaApertura, FechaCierre, QuorumRequerido
            FROM Votaciones
            WHERE OrganizacionId = :organizacion_id
            ORDER BY FechaApertura DESC
            """
        ),
        {"organizacion_id": actual.organizacion_id},
    ).mappings()

    return [
        VotacionResumen(
            votacion_id=row["VotacionId"],
            titulo=row["Titulo"],
            estado=row["Estado"],
            fecha_apertura=row["FechaApertura"],
            fecha_cierre=row["FechaCierre"],
            quorum_requerido=row["QuorumRequerido"],
        )
        for row in rows
    ]


@router.get("/{votacion_id}", response_model=VotacionDetalle)
def obtener_votacion(
    votacion_id: int,
    conn: Connection = Depends(get_connection),
    actual: MiembroSesion = Depends(get_current_member),
) -> VotacionDetalle:
    _exigir_votacion_de_mi_organizacion(conn, votacion_id, actual)
    votacion = conn.execute(
        text(
            """
            SELECT VotacionId, Titulo, Descripcion, Estado, FechaApertura, FechaCierre, QuorumRequerido
            FROM Votaciones
            WHERE VotacionId = :votacion_id
            """
        ),
        {"votacion_id": votacion_id},
    ).mappings().first()

    if votacion is None:
        raise HTTPException(status_code=404, detail="Votación no encontrada")

    opciones = conn.execute(
        text("SELECT OpcionId, TextoOpcion FROM OpcionesVoto WHERE VotacionId = :votacion_id"),
        {"votacion_id": votacion_id},
    ).mappings()

    return VotacionDetalle(
        votacion_id=votacion["VotacionId"],
        titulo=votacion["Titulo"],
        descripcion=votacion["Descripcion"],
        estado=votacion["Estado"],
        fecha_apertura=votacion["FechaApertura"],
        fecha_cierre=votacion["FechaCierre"],
        quorum_requerido=votacion["QuorumRequerido"],
        opciones=[
            OpcionVoto(opcion_id=o["OpcionId"], texto_opcion=o["TextoOpcion"]) for o in opciones
        ],
    )


@router.get("/{votacion_id}/resultado", response_model=ResultadoVotacion)
def obtener_resultado(
    votacion_id: int,
    conn: Connection = Depends(get_connection),
    actual: MiembroSesion = Depends(get_current_member),
) -> ResultadoVotacion:
    _exigir_votacion_de_mi_organizacion(conn, votacion_id, actual)
    row = conn.execute(
        text("SELECT * FROM vw_ResultadosYQuorum WHERE VotacionId = :votacion_id"),
        {"votacion_id": votacion_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Votación no encontrada")

    # Desglose por opcion (peso ponderado y conteo de votos). No viene de
    # vw_ResultadosYQuorum -- esa vista solo trae el agregado para el quorum.
    opciones_rows = conn.execute(
        text(
            """
            SELECT ov.OpcionId, ov.TextoOpcion,
                   ISNULL(SUM(m.PesoVoto), 0) AS Peso,
                   COUNT(v.VotoId) AS Votos
            FROM OpcionesVoto ov
            LEFT JOIN Votos v ON v.OpcionId = ov.OpcionId
            LEFT JOIN Miembros m ON m.MiembroId = v.MiembroId
            WHERE ov.VotacionId = :votacion_id
            GROUP BY ov.OpcionId, ov.TextoOpcion
            ORDER BY ov.OpcionId
            """
        ),
        {"votacion_id": votacion_id},
    ).mappings().all()

    padron_row = conn.execute(
        text(
            """
            SELECT COUNT(*) AS Total, ISNULL(SUM(PesoVoto), 0) AS PesoTotal
            FROM Miembros
            WHERE OrganizacionId = (SELECT OrganizacionId FROM Votaciones WHERE VotacionId = :votacion_id)
            """
        ),
        {"votacion_id": votacion_id},
    ).mappings().first()

    votantes_row = conn.execute(
        text("SELECT COUNT(DISTINCT MiembroId) AS Votantes FROM Votos WHERE VotacionId = :votacion_id"),
        {"votacion_id": votacion_id},
    ).mappings().first()

    return ResultadoVotacion(
        votacion_id=row["VotacionId"],
        titulo=row["Titulo"],
        quorum_requerido=row["QuorumRequerido"],
        peso_total_votado=row["PesoTotalVotado"],
        quorum_alcanzado=bool(row["QuorumAlcanzado"]),
        estado=row["Estado"],
        fecha_apertura=row["FechaApertura"],
        fecha_cierre=row["FechaCierre"],
        peso_total_padron=padron_row["PesoTotal"],
        miembros_total=padron_row["Total"],
        miembros_votantes=votantes_row["Votantes"],
        opciones=[
            OpcionResultado(
                opcion_id=o["OpcionId"],
                texto_opcion=o["TextoOpcion"],
                peso=o["Peso"],
                votos=o["Votos"],
            )
            for o in opciones_rows
        ],
    )


@router.post("/{votacion_id}/votos", response_model=VotoConfirmacion, status_code=201)
def registrar_voto(
    votacion_id: int,
    voto: VotoCrear,
    conn: Connection = Depends(get_connection),
    actual: MiembroSesion = Depends(get_current_member),
) -> VotoConfirmacion:
    # Quien vota es el dueño del token, nunca un id enviado por el cliente.
    # La validación de ventana de tiempo, pertenencia de la opción y el
    # bloqueo de doble voto (constraint UNIQUE) viven en sp_RegistrarVoto,
    # no aquí: esta capa solo traduce el resultado del SP a HTTP.
    try:
        with conn.begin():
            # Dentro del begin(): una consulta previa fuera de el abriria una
            # transaccion implicita y conn.begin() fallaria.
            _exigir_votacion_de_mi_organizacion(conn, votacion_id, actual)
            result = conn.execute(
                text("EXEC sp_RegistrarVoto @VotacionId=:vid, @MiembroId=:mid, @OpcionId=:oid"),
                {"vid": votacion_id, "mid": actual.miembro_id, "oid": voto.opcion_id},
            )
            mensaje = result.mappings().first()
    except DBAPIError as exc:
        detalle = str(exc.orig)
        if "fuera de la ventana" in detalle or "está cerrada" in detalle:
            raise HTTPException(status_code=409, detail="La votación no está abierta") from exc
        if "no pertenece a esta votación" in detalle:
            raise HTTPException(status_code=400, detail="Opción de voto inválida") from exc
        if "UQ_Voto_Miembro_Votacion" in detalle or "duplicate key" in detalle.lower():
            raise HTTPException(status_code=409, detail="Este miembro ya votó en esta votación") from exc
        raise HTTPException(status_code=500, detail="No se pudo registrar el voto") from exc

    return VotoConfirmacion(mensaje=mensaje["Mensaje"] if mensaje else "Voto registrado exitosamente")
