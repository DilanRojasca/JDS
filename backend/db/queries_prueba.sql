-- =======================================================================
-- Queries de prueba manual -- correr en DBeaver contra DS_Votaciones
-- =======================================================================
USE DS_Votaciones;

-- 1. Ver todas las votaciones (estado, fechas, quorum requerido)
SELECT VotacionId, Titulo, Estado, QuorumRequerido, FechaApertura, FechaCierre
FROM Votaciones
ORDER BY VotacionId;

-- 2. Ver las opciones de una votacion puntual
SELECT OpcionId, TextoOpcion
FROM OpcionesVoto
WHERE VotacionId = 1;

-- 3. Ver los votos ya registrados, con nombre del miembro y opcion elegida
SELECT
    Vo.VotoId,
    M.Nombre AS Miembro,
    M.PesoVoto,
    O.TextoOpcion AS OpcionElegida,
    Vo.FechaHora
FROM Votos Vo
JOIN Miembros M ON M.MiembroId = Vo.MiembroId
JOIN OpcionesVoto O ON O.OpcionId = Vo.OpcionId
WHERE Vo.VotacionId = 1
ORDER BY Vo.FechaHora;

-- 4. La vista de resultados y quorum (lo que consume el endpoint /resultado)
SELECT * FROM vw_ResultadosYQuorum;

SELECT * FROM vw_ResultadosYQuorum WHERE VotacionId = 1;

-- 5. Padron de miembros de la organizacion (para saber que MiembroId usar al probar)
SELECT MiembroId, Nombre, PesoVoto
FROM Miembros
WHERE OrganizacionId = 1
ORDER BY Nombre;

-- =======================================================================
-- 6. Probar el procedimiento sp_RegistrarVoto directamente (sin pasar por la API)
--    Cambia @MiembroId y @OpcionId por unos que existan y que NO hayan votado ya.
-- =======================================================================
EXEC sp_RegistrarVoto @VotacionId = 1, @MiembroId = 3, @OpcionId = 2;

-- 6a. Caso de error esperado: el mismo miembro intenta votar dos veces
--     (deberia fallar por la constraint UQ_Voto_Miembro_Votacion)
EXEC sp_RegistrarVoto @VotacionId = 1, @MiembroId = 3, @OpcionId = 1;

-- 6b. Caso de error esperado: una opcion que no pertenece a esa votacion
EXEC sp_RegistrarVoto @VotacionId = 1, @MiembroId = 4, @OpcionId = 999;

-- 7. Despues de probar votos nuevos, volver a mirar la vista para ver el quorum actualizado
SELECT * FROM vw_ResultadosYQuorum WHERE VotacionId = 1;

-- =======================================================================
-- 8. (Opcional) Deshacer los votos de prueba insertados en el paso 6,
--    para dejar la base como estaba antes de la prueba manual.
--    Ojo: borra TODOS los votos de la votacion 1, no solo los de prueba.
-- =======================================================================
-- DELETE FROM Votos WHERE VotacionId = 1;
