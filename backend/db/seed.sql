-- Datos de ejemplo para desarrollo local. No usar en producción.
USE DS_Votaciones;
GO

INSERT INTO Organizaciones (Nombre) VALUES ('Conjunto Residencial Los Robles');
DECLARE @OrgId INT = SCOPE_IDENTITY();

-- Clave de desarrollo de TODOS los miembros del seed: votacoop123
-- (login con la Identificacion como usuario). Solo para desarrollo local.
DECLARE @DevHash NVARCHAR(255) = '$2b$12$YXr7kq5sqykEaO8XWYSfle4/wfm7OP5O4m/UnlP3eTUtdHoBFTofe';

INSERT INTO Miembros (OrganizacionId, Identificacion, Nombre, PesoVoto, PasswordHash) VALUES
    (@OrgId, '52104887', 'Marta Gómez', 2.4500, @DevHash),
    (@OrgId, '80211334', 'Andrés Peña', 1.8200, @DevHash),
    (@OrgId, '43998221', 'Lucía Torres', 3.1000, @DevHash),
    (@OrgId, '79345102', 'Julián Ramírez', 1.5000, @DevHash),
    (@OrgId, '61772905', 'Sofía Vega', 2.0600, @DevHash);

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
