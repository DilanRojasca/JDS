-- =======================================================================
-- MIGRACION: login de miembros
-- Para bases DS_Votaciones que YA existen (sin recrearlas ni perder datos).
-- Si vas a recrear la BD con schema.sql, no necesitas este script.
-- Es idempotente: se puede ejecutar varias veces.
-- =======================================================================
USE DS_Votaciones;
GO

IF COL_LENGTH('Miembros', 'PasswordHash') IS NULL
    ALTER TABLE Miembros ADD PasswordHash NVARCHAR(255) NULL;
GO

-- Falla si ya hay dos miembros con la misma Identificacion: en ese caso
-- corrige los duplicados a mano y vuelve a ejecutar.
IF NOT EXISTS (
    SELECT 1 FROM sys.key_constraints
    WHERE name = 'UQ_Miembros_Identificacion' AND parent_object_id = OBJECT_ID('Miembros')
)
    ALTER TABLE Miembros ADD CONSTRAINT UQ_Miembros_Identificacion UNIQUE (Identificacion);
GO

-- Despues de migrar, cada miembro con PasswordHash NULL ya puede entrar solo
-- con su Nombre y su Identificacion/documento como clave temporal; la API lo
-- obliga a definir una clave propia en el primer login (POST /auth/set-password).
-- Para asignarle una clave a mano en vez de eso (por ejemplo, si el
-- documento de alguien quedo expuesto), sigue disponible:
--   python -m scripts.set_password <identificacion>
