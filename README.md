# VotaCoop — Plataforma de Votación y Gobernanza para Organizaciones

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
- **Historial / Auditoría**: bitácora de eventos relevantes (apertura, cierre, cambios administrativos) para trazabilidad.

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
