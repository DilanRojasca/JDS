# JDS — Plataforma de Votación y Gobernanza para Organizaciones

Sistema de votación electrónica diseñado para asambleas de copropietarios, cooperativas y organizaciones con estructuras de gobernanza participativa, donde cada miembro posee un peso de voto proporcional a su participación (ej. coeficiente de copropiedad, aportes societarios, etc.).

## Participantes y roles iniciales

| Usuario GitHub | Rol |
|---|---|
| [@sevg-dot](https://github.com/sevg-dot) | Frontend / UI-UX / QA |
| [@JulianRamirez43](https://github.com/JulianRamirez43) | Backend / QA |
| [@DilanRojasca](https://github.com/DilanRojasca) | Product Owner / Full Stack |


## Descripción del problema (alcance)

Muchas organizaciones con estructuras de gobernanza colectiva (copropiedades, cooperativas, juntas de acción comunal, asociaciones) todavía gestionan sus votaciones de forma manual o con herramientas genéricas (hojas de cálculo, formularios sueltos) que no garantizan trazabilidad, no validan quórum de forma confiable, y son vulnerables a doble voto o manipulación de resultados después del cierre.

El proyecto busca construir una plataforma que permita:
- Convocar votaciones formales dentro de una organización, con una ventana de tiempo definida (apertura y cierre).
- Calcular automáticamente si se alcanzó el quórum mínimo requerido antes de considerar válida una votación.
- Registrar el voto de cada miembro respetando su peso de voto (no todos los votos valen igual).
- Garantizar que un miembro no pueda votar dos veces en la misma votación, incluso bajo solicitudes concurrentes.
- Bloquear cualquier modificación de los resultados una vez la votación ha cerrado formalmente.
- Dejar un historial auditable de todas las votaciones realizadas por la organización.

## Posibles usuarios del sistema

- **Miembro / votante**: persona con derecho a voto dentro de la organización (copropietario, socio, cooperado).
- **Administrador de la organización**: convoca votaciones, define quórum y ventana de tiempo, gestiona el padrón de miembros y sus pesos de voto.
- **Auditor / veedor**: rol de solo lectura con acceso al historial de votaciones y resultados para fines de transparencia.
- **Superadministrador del sistema**: gestiona múltiples organizaciones dentro de la misma plataforma (si se decide manejar multi-tenant).

## Lista preliminar de entidades

- **Organización**: entidad que agrupa a los miembros y convoca las votaciones.
- **Miembro**: persona perteneciente a una organización, con un peso de voto asociado.
- **Votación**: evento de votación con título, descripción, quórum mínimo requerido, fecha/hora de apertura y de cierre, y estado (pendiente, abierta, cerrada, anulada).
- **Opción de voto**: alternativas disponibles dentro de una votación (ej. "A favor", "En contra", "Abstención", o candidatos en el caso de elecciones).
- **Voto**: registro individual del voto emitido por un miembro en una votación, vinculado a la opción elegida y con marca de tiempo.
- **Resultado**: resumen calculado de una votación una vez cerrada (totales por opción, porcentaje de participación, si se alcanzó quórum).
- **Historial / Auditoría**: bitácora de eventos relevantes (apertura, cierre, cambios administrativos) para trazabilidad. Implementada en MongoDB Atlas, no en SQL Server (ver [sección dedicada](#segunda-base-de-datos-mongodb-atlas-auditoría) más abajo).

## Reglas de negocio

1. **No doble voto**: un miembro no puede emitir más de un voto en la misma votación, incluso si intenta hacerlo mediante solicitudes simultáneas (control de concurrencia a nivel de transacción/base de datos, no solo validación en el frontend).

2. **Validez por quórum**: una votación solo se considera válida si, al momento de su cierre, la suma de los pesos de voto de los miembros participantes alcanza o supera el quórum mínimo definido al momento de la convocatoria. Si no se alcanza, la votación se marca como "sin quórum" y sus resultados no tienen efecto vinculante.

3. **Inmutabilidad post-cierre**: una vez que una votación pasa a estado "cerrada" (ya sea porque venció su ventana de tiempo o fue cerrada manualmente por el administrador), ningún voto puede ser creado, modificado o eliminado, y los resultados calculados quedan fijos de forma permanente.

4. **Voto ponderado por participación**: el valor de cada voto no es uniforme; se calcula en función del peso asignado al miembro (ej. su coeficiente de copropiedad), por lo que el sistema debe calcular resultados en función de la suma de pesos y no solo del conteo de votantes.

5. **Ventana de tiempo estricta**: un voto solo puede registrarse si la fecha/hora actual está dentro del rango [apertura, cierre] definido para esa votación; el sistema debe rechazar automáticamente cualquier intento de voto fuera de esa ventana.

## ¿Por qué el proyecto es suficientemente complejo?

- Requiere **control de concurrencia real**: múltiples miembros pueden intentar votar al mismo tiempo, y el sistema debe garantizar consistencia (evitar condiciones de carrera que permitan doble voto) mediante transacciones, bloqueos o restricciones a nivel de base de datos.
- Involucra **integridad referencial y reglas de negocio no triviales** que no pueden delegarse completamente a la capa de aplicación (ej. inmutabilidad post-cierre, cálculo de quórum ponderado), lo que justifica el uso de constraints, triggers o procedimientos almacenados.
- Maneja **datos temporales críticos** (ventanas de apertura/cierre) que afectan directamente la validez de las operaciones permitidas sobre otras tablas.
- Requiere **consultas de agregación** para calcular resultados y estadísticas de participación en tiempo real o al cierre de cada votación.
- Necesita **trazabilidad y auditoría**, lo que implica modelar historación de datos y no solo su estado actual.
- Potencialmente **multi-tenant** (varias organizaciones en la misma base de datos), lo que agrega una capa adicional de aislamiento y modelado de datos.

## Autenticación (login)

**Comportamiento:**

- El miembro inicia sesión con su **Nombre completo** (usuario) y una **contraseña**. El nombre no es único: si hay homónimos, la cuenta real se resuelve por la contraseña correcta (cada candidato se valida por separado; la ambigüedad la rompe la clave, no el nombre).
- **Primer ingreso:** todo miembro nuevo tiene `PasswordHash` en `NULL` y puede entrar usando su **número de documento** (`Identificacion`) como contraseña temporal. Al hacerlo, la API responde con `debe_cambiar_password: true` y bloquea el resto de los endpoints (403) hasta que llame a `POST /auth/set-password` con una contraseña propia (mínimo 8 caracteres). Una vez definida, el documento deja de servir como contraseña.
  - Esto es una elección deliberada de UX sobre seguridad: el documento no es secreto (aparece en actas, listas de asamblea, etc.), así que solo habilita una única sesión de "onboarding" cuyo único fin es fijar una contraseña real; no queda disponible como credencial permanente.
- Las contraseñas (la temporal exceptuada) se guardan solo como hash bcrypt (`Miembros.PasswordHash`).
- Al ingresar, la API entrega un token JWT (vigencia 8 h, configurable con `JWT_EXPIRE_MINUTES`) que el frontend envía como `Authorization: Bearer ...`.
- Todos los endpoints exigen token, excepto `GET /health` y `POST /auth/login`. `GET /auth/me` y `POST /auth/set-password` funcionan incluso con `debe_cambiar_password: true`; el resto de la API no.
- **Quién vota lo decide el token, no el cliente**: `POST /votaciones/{id}/votos` recibe solo `opcion_id`; el `miembro_id` sale de la sesión. Ningún miembro puede votar a nombre de otro.
- **Aislamiento por organización**: un miembro solo ve y vota en votaciones de su organización (una votación ajena responde 404).
- Login fallido responde siempre lo mismo (“Nombre o contraseña incorrectos”), exista o no ese nombre.
- **Límite de intentos**: tras 5 intentos fallidos consecutivos con el mismo nombre, el login responde `429` durante 15 minutos (incluso si después se manda la contraseña correcta). Un login exitoso reinicia el contador. Es un límite en memoria del proceso (`backend/app/rate_limit.py`), no una tabla ni un servicio externo.
- **Contraseña olvidada**: `POST /auth/olvide-password` con `nombre` + `identificacion` (el mismo documento del primer ingreso) borra la contraseña del miembro y lo regresa al flujo de "primer ingreso": puede volver a entrar con su documento como clave temporal y la API le exige definir una nueva. Responde siempre el mismo mensaje, coincidan o no los datos, para no filtrar qué identificaciones existen.

**Puesta en marcha:**

1. `pip install -r requirements.txt` (en `backend/`).
2. Crear `backend/.env` a partir de `.env.example` y definir `JWT_SECRET` (obligatorio, mínimo 32 caracteres): `python -c "import secrets; print(secrets.token_hex(32))"`. Sin él la API no arranca.
3. Base de datos:
   - **BD nueva:** ejecutar `db/schema.sql` y luego `db/seed.sql`. Los 5 miembros del seed entran con su nombre (p. ej. `Marta Gómez`) y su documento (p. ej. `52104887`) como clave temporal; la API los obliga a definir una clave propia en ese primer login.
   - **BD ya existente:** ejecutar `db/migracion_login.sql` y `db/migracion_roles.sql` (ambos idempotentes). Los miembros con `PasswordHash NULL` ya pueden usar el flujo de arriba sin pasos adicionales; `python -m scripts.set_password <identificacion>` sigue disponible para que un administrador asigne una clave a mano si hace falta. Todos los miembros existentes quedan con `Rol = 'Miembro'`; para promover a alguien a `Administrador` o `Auditor`, ver el comentario al final de `db/migracion_roles.sql`.

**Pruebas:** `pip install -r requirements-dev.txt` y `python -m pytest` (usan SQLite en memoria; no requieren SQL Server).

La `Identificacion` es única en toda la plataforma (un mismo miembro no puede estar en dos organizaciones).

## Roles

Cada miembro tiene un `Rol` (`Miembros.Rol`): `Miembro`, `Administrador`, `Auditor` o `Superadministrador`.

- **Miembro**: vota y consulta las votaciones y resultados de su organización. Es el rol por defecto.
- **Administrador**: además de lo anterior, convoca votaciones (`POST /votaciones`), las cierra manualmente antes de su vencimiento (`POST /votaciones/{id}/cerrar`) y da de alta nuevos miembros (`POST /organizaciones/{id}/miembros`). Solo administra su propia organización.
- **Auditor**: rol de solo lectura con acceso adicional al historial de auditoría (`GET /auditoria`); no vota ni administra.
- **Superadministrador**: el único rol que no está limitado a una sola organización. Da de alta organizaciones nuevas (`POST /organizaciones`), ve el listado completo de organizaciones (`GET /organizaciones` le devuelve todas en vez de solo la propia), y puede consultar el padrón (`GET /organizaciones/{id}/miembros`) y la auditoría (`GET /auditoria?organizacion_id=...`) de cualquiera de ellas. No crea ni cierra votaciones de organizaciones ajenas: esa sigue siendo tarea del `Administrador` de cada una.

`GET /auth/me` devuelve el `rol` del miembro autenticado; el frontend usa ese campo para mostrar u ocultar las pestañas "Administración", "Auditoría" y "Organizaciones" (esta última solo para `Superadministrador`).

## Cierre automático de votaciones por ventana de tiempo

Un job en segundo plano (APScheduler, `backend/app/scheduler.py`) corre cada 30 segundos y:

- Pasa una votación de `Pendiente` a `Abierta` cuando `FechaApertura` ya llegó.
- Pasa una votación de `Pendiente`/`Abierta` a `Cerrada` cuando `FechaCierre` ya pasó.

Esto solo mantiene el campo `Estado` honesto para el frontend y los reportes: `sp_RegistrarVoto` ya rechaza cualquier voto fuera de la ventana de tiempo independientemente del `Estado`, así que la integridad del voto no depende de este job. Se desactiva con `ENABLE_SCHEDULER=false` en `.env` (por ejemplo, si se corren varias instancias de la API contra la misma base de datos, para que no compitan ejecutando el mismo job); también está desactivado en las pruebas (`tests/conftest.py`).

## Segunda base de datos: MongoDB Atlas (auditoría)

El proyecto usa **dos bases de datos** con roles distintos:

- **SQL Server**: toda la lógica transaccional (organizaciones, miembros, votaciones, votos). Es la única fuente de verdad para esas reglas de negocio.
- **MongoDB Atlas**: historial de auditoría — un log de eventos (`login`, `set_password`, `votar`, `crear_votacion`, `cerrar_votacion`, `crear_miembro`, `apertura_automatica`, `cierre_automatico`) con esquema variable según el tipo de evento. Encaja con un modelo de documentos porque es append-only y no participa en ninguna transacción ni regla de negocio (no se usa para calcular quórum, resultados, ni para impedir doble voto).

El logging de auditoría es **best-effort** (`backend/app/mongo.py`): si `MONGODB_URI` no está configurado, o Mongo no responde, la API funciona con total normalidad y el evento simplemente no queda registrado (se registra un warning en los logs, nunca se devuelve un error al cliente).

**Puesta en marcha:**

1. Crear un cluster en [MongoDB Atlas](https://www.mongodb.com/atlas) (el free tier M0 alcanza).
2. En **Database Access**, crear un usuario de base de datos con permisos de lectura/escritura (distinto de tu cuenta de Atlas).
3. En **Network Access**, permitir la IP desde la que corre la API (o `0.0.0.0/0` solo para desarrollo).
4. Copiar la cadena de conexión ("Connect" → "Drivers") y pegarla en `backend/.env`:
   ```
   MONGODB_URI=mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/
   MONGODB_DB=ds_votaciones_auditoria
   ```
5. No se requiere crear la colección a mano: `pymongo` la crea sola al insertar el primer evento.

`GET /auditoria` (rol Administrador o Auditor) devuelve el historial de la organización del miembro autenticado, más reciente primero.

## Endpoints de administración

Todos requieren rol `Administrador` y operan sobre la organización del miembro autenticado (no se puede administrar otra organización, aunque se conozca su id):

- `POST /votaciones`: crea una votación en estado `Pendiente`, con sus opciones de voto (mínimo 2). `fecha_cierre` debe ser posterior a `fecha_apertura`.
- `POST /votaciones/{id}/cerrar`: cierre manual anticipado (409 si ya estaba cerrada). El cierre por vencimiento normal de la ventana de tiempo lo hace el scheduler automático, sin necesidad de llamar a este endpoint.
- `POST /organizaciones/{id}/miembros`: da de alta un miembro nuevo (409 si la identificación ya existe). El miembro creado entra por primera vez con su documento como contraseña temporal, igual que los del seed inicial.

El único endpoint de administración que no requiere `Administrador` sino `Superadministrador` es:

- `POST /organizaciones`: crea una organización nueva (solo `{ "nombre": "..." }`; todavía sin miembros ni votaciones).

## Uso de IA

Este proyecto adopta **Spec-Driven Development (SDD)** como metodología de trabajo con asistentes de IA: la especificación es la fuente de verdad, y el código es un artefacto derivado de esa especificación, no al revés.

Política de uso:

- Antes de generar cualquier código, se escribe una **especificación clara y estructurada** del requerimiento (comportamiento esperado, entidades involucradas, reglas de negocio, criterios de validación), la cual es discutida y acordada por el equipo.
- El asistente de IA genera el código **a partir de esa especificación**, no de prompts sueltos ni de "vibe coding". Si la especificación cambia, el código se regenera o ajusta a partir de la especificación actualizada, manteniéndola como documento vivo.
- Todo código producido por IA debe ser **revisado, entendido y validado por el equipo** contra la especificación correspondiente antes de integrarse (human-in-the-loop); no se aceptan cambios que el equipo no pueda explicar o justificar contra el spec.
- No se comparte información sensible, credenciales, ni datos personales de terceros con herramientas de IA externas.
- Las decisiones de arquitectura y modelado de datos son responsabilidad del equipo; la especificación y su validación son el punto de control, no la IA en sí misma.
- Se documenta en los commits o PRs cuándo un cambio proviene de una especificación trabajada con asistencia de IA, para mantener trazabilidad entre spec → implementación.

## Licencia

Este proyecto se distribuye bajo la licencia [MIT](https://opensource.org/licenses/MIT).
