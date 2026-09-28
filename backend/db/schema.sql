-- =======================================================================
-- PROYECTO: Plataforma de Votación y Gobernanza (DS)
-- MOTOR: SQL Server (SSMS)
-- ITERACIÓN: 1 - Esquema Base, Transacciones, Procedimientos y Vistas
-- =======================================================================

DROP DATABASE IF EXISTS DS_Votaciones;
GO

CREATE DATABASE DS_Votaciones;
GO

USE DS_Votaciones;
GO

-- 1. CREACIÓN DE TABLAS (Esquema Base)
-- -----------------------------------------------------------------------

CREATE TABLE Organizaciones (
    OrganizacionId INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL,
    FechaCreacion DATETIME DEFAULT GETDATE()
);

CREATE TABLE Miembros (
    MiembroId INT IDENTITY(1,1) PRIMARY KEY,
    OrganizacionId INT NOT NULL FOREIGN KEY REFERENCES Organizaciones(OrganizacionId),
    Identificacion NVARCHAR(50) NOT NULL,
    Nombre NVARCHAR(100) NOT NULL,
    PesoVoto DECIMAL(10, 4) NOT NULL DEFAULT 1.0000
);

CREATE TABLE Votaciones (
    VotacionId INT IDENTITY(1,1) PRIMARY KEY,
    OrganizacionId INT NOT NULL FOREIGN KEY REFERENCES Organizaciones(OrganizacionId),
    Titulo NVARCHAR(200) NOT NULL,
    Descripcion NVARCHAR(MAX),
    QuorumRequerido DECIMAL(10, 4) NOT NULL,
    FechaApertura DATETIME NOT NULL,
    FechaCierre DATETIME NOT NULL,
    Estado NVARCHAR(20) DEFAULT 'Pendiente' CHECK (Estado IN ('Pendiente', 'Abierta', 'Cerrada', 'Anulada'))
);

CREATE TABLE OpcionesVoto (
    OpcionId INT IDENTITY(1,1) PRIMARY KEY,
    VotacionId INT NOT NULL FOREIGN KEY REFERENCES Votaciones(VotacionId),
    TextoOpcion NVARCHAR(100) NOT NULL
);

CREATE TABLE Votos (
    VotoId INT IDENTITY(1,1) PRIMARY KEY,
    VotacionId INT NOT NULL FOREIGN KEY REFERENCES Votaciones(VotacionId),
    MiembroId INT NOT NULL FOREIGN KEY REFERENCES Miembros(MiembroId),
    OpcionId INT NOT NULL FOREIGN KEY REFERENCES OpcionesVoto(OpcionId),
    FechaHora DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_Voto_Miembro_Votacion UNIQUE (VotacionId, MiembroId)
);
GO

-- 2. PROCEDIMIENTO ALMACENADO Y TRANSACCIÓN
-- -----------------------------------------------------------------------

CREATE PROCEDURE sp_RegistrarVoto
    @VotacionId INT,
    @MiembroId INT,
    @OpcionId INT
AS
BEGIN
    SET NOCOUNT ON;

    SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @FechaActual DATETIME = GETDATE();
        DECLARE @FechaApertura DATETIME;
        DECLARE @FechaCierre DATETIME;
        DECLARE @Estado NVARCHAR(20);

        SELECT @FechaApertura = FechaApertura,
               @FechaCierre = FechaCierre,
               @Estado = Estado
        FROM Votaciones
        WHERE VotacionId = @VotacionId;

        IF (@FechaActual < @FechaApertura OR @FechaActual > @FechaCierre OR @Estado = 'Cerrada')
        BEGIN
            THROW 51000, 'Error: La votación se encuentra fuera de la ventana de tiempo permitida o está cerrada.', 1;
        END

        IF NOT EXISTS (SELECT 1 FROM OpcionesVoto WHERE OpcionId = @OpcionId AND VotacionId = @VotacionId)
        BEGIN
            THROW 51001, 'Error: La opción de voto no pertenece a esta votación.', 1;
        END

        INSERT INTO Votos (VotacionId, MiembroId, OpcionId, FechaHora)
        VALUES (@VotacionId, @MiembroId, @OpcionId, @FechaActual);

        COMMIT TRANSACTION;
        SELECT 'Voto registrado exitosamente' AS Mensaje;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRANSACTION;
        END

        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();

        RAISERROR (@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH
END;
GO

-- 3. VISTA (Cálculo de Quorum y Voto Ponderado)
-- -----------------------------------------------------------------------

CREATE VIEW vw_ResultadosYQuorum
AS
SELECT
    V.VotacionId,
    V.Titulo,
    V.QuorumRequerido,
    ISNULL(SUM(M.PesoVoto), 0) AS PesoTotalVotado,
    CASE
        WHEN ISNULL(SUM(M.PesoVoto), 0) >= V.QuorumRequerido THEN 1
        ELSE 0
    END AS QuorumAlcanzado,
    V.Estado,
    V.FechaApertura,
    V.FechaCierre
FROM
    Votaciones V
LEFT JOIN
    Votos Vo ON V.VotacionId = Vo.VotacionId
LEFT JOIN
    Miembros M ON Vo.MiembroId = M.MiembroId
GROUP BY
    V.VotacionId,
    V.Titulo,
    V.QuorumRequerido,
    V.Estado,
    V.FechaApertura,
    V.FechaCierre;
GO
