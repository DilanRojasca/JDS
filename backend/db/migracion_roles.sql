-- =======================================================================
-- MIGRACION: roles de miembro (Miembro / Administrador / Auditor)
-- Para bases DS_Votaciones que YA existen (sin recrearlas ni perder datos).
-- Si vas a recrear la BD con schema.sql, no necesitas este script.
-- Es idempotente: se puede ejecutar varias veces.
-- =======================================================================
USE DS_Votaciones;
GO

IF COL_LENGTH('Miembros', 'Rol') IS NULL
    ALTER TABLE Miembros ADD Rol NVARCHAR(20) NOT NULL DEFAULT 'Miembro';
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = 'CK_Miembros_Rol' AND parent_object_id = OBJECT_ID('Miembros')
)
    ALTER TABLE Miembros ADD CONSTRAINT CK_Miembros_Rol CHECK (Rol IN ('Miembro', 'Administrador', 'Auditor'));
GO

-- Despues de migrar, todos los miembros existentes quedan como 'Miembro'.
-- Para promover a alguien a administrador o auditor:
--   UPDATE Miembros SET Rol = 'Administrador' WHERE Identificacion = '<documento>';
