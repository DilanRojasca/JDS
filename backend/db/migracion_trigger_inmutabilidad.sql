-- =======================================================================
-- MIGRACION: trigger de inmutabilidad post-cierre sobre Votos
-- Para bases DS_Votaciones que YA existen (sin recrearlas ni perder datos).
-- Si vas a recrear la BD con schema.sql, no necesitas este script.
-- Es idempotente: se puede ejecutar varias veces.
-- =======================================================================
USE DS_Votaciones;
GO

IF OBJECT_ID('trg_Votos_ImpedirCambioSiCerrada', 'TR') IS NOT NULL
    DROP TRIGGER trg_Votos_ImpedirCambioSiCerrada;
GO

CREATE TRIGGER trg_Votos_ImpedirCambioSiCerrada
ON Votos
AFTER UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1
        FROM deleted d
        JOIN Votaciones v ON v.VotacionId = d.VotacionId
        WHERE v.Estado = 'Cerrada'
    )
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 51002, 'No se pueden modificar ni eliminar votos de una votación cerrada.', 1;
    END
END;
GO
