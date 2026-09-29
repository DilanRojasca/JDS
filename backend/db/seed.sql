-- Datos de ejemplo para desarrollo local. No usar en producción.
USE DS_Votaciones;
GO

INSERT INTO Organizaciones (Nombre) VALUES ('Conjunto Residencial Los Robles');
DECLARE @OrgId INT = SCOPE_IDENTITY();

-- PasswordHash NULL a proposito: el miembro entra por primera vez con su
-- Nombre (usuario) y su Identificacion/documento como clave temporal, y la
-- API lo obliga a definir una clave propia (POST /auth/set-password) antes
-- de dejarlo usar el resto de la plataforma. Ver verify_documento_temporal
-- en app/security.py y el flujo de login en app/routers/auth.py.
INSERT INTO Miembros (OrganizacionId, Identificacion, Nombre, PesoVoto, PasswordHash) VALUES
    (@OrgId, '52104887', 'Marta Gómez', 2.4500, NULL),
    (@OrgId, '80211334', 'Andrés Peña', 1.8200, NULL),
    (@OrgId, '43998221', 'Lucía Torres', 3.1000, NULL),
    (@OrgId, '79345102', 'Julián Ramírez', 1.5000, NULL),
    (@OrgId, '61772905', 'Sofía Vega', 2.0600, NULL);

INSERT INTO Votaciones (OrganizacionId, Titulo, Descripcion, QuorumRequerido, FechaApertura, FechaCierre, Estado)
VALUES (
    @OrgId,
    'Aprobación de presupuesto de mantenimiento 2027',
    'Ratificación del presupuesto anual para mantenimiento de zonas comunes y fondo de reserva.',
    5.00,
    DATEADD(HOUR, -2, GETDATE()),
    DATEADD(DAY, 5, GETDATE()),
    'Abierta'
);
DECLARE @VotacionId INT = SCOPE_IDENTITY();

INSERT INTO OpcionesVoto (VotacionId, TextoOpcion) VALUES
    (@VotacionId, 'A favor'),
    (@VotacionId, 'En contra'),
    (@VotacionId, 'Abstención');
GO
