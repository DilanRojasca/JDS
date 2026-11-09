-- =======================================================================
-- MIGRACION: roles de miembro (Miembro / Administrador / Auditor)
-- Para bases DS_Votaciones que YA existen (sin recrearlas ni perder datos).
-- Si vas a recrear la BD con schema.sql, no necesitas este script.
-- Es idempotente: se puede ejecutar varias veces.
-- =======================================================================
USE DS_Votaciones;
GO

IF COL_LENGTH('Miembros', 'Rol') IS NULL
    ALTER TABLE Miembros ADD Rol NVARCHAR(25) NOT NULL DEFAULT 'Miembro';
GO

-- La columna pudo haber quedado mas corta en una corrida previa de esta
-- migracion (NVARCHAR(20) no alcanza para 'Superadministrador').
ALTER TABLE Miembros ALTER COLUMN Rol NVARCHAR(25) NOT NULL;
GO

-- Se elimina y recrea el CHECK en vez de intentar "ALTER"-lo: SQL Server no
-- permite modificar la condicion de un check existente, solo soltarlo y
-- volver a crearlo. Idempotente: si ya incluye 'Superadministrador' no hace
-- falta tocarlo, pero recrearlo de todas formas no tiene costo.
IF EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = 'CK_Miembros_Rol' AND parent_object_id = OBJECT_ID('Miembros')
)
    ALTER TABLE Miembros DROP CONSTRAINT CK_Miembros_Rol;
GO

ALTER TABLE Miembros ADD CONSTRAINT CK_Miembros_Rol
    CHECK (Rol IN ('Miembro', 'Administrador', 'Auditor', 'Superadministrador'));
GO

-- Despues de migrar, todos los miembros existentes quedan como 'Miembro'.
-- Para promover a alguien:
--   UPDATE Miembros SET Rol = 'Administrador' WHERE Identificacion = '<documento>';
-- El Superadministrador no esta limitado a una organizacion pero igual
-- necesita pertenecer a una (OrganizacionId NOT NULL): cualquiera sirve.
