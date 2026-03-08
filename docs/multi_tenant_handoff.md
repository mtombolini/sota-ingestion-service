# Multi-tenant Control Plane Handoff

## Estado del roadmap
Las fases 1, 2, 3 y 4 del roadmap original quedaron implementadas sobre el estado actual del repo.

## Lo que ya existe

### 1. Tenant como cuenta operativa
- `Tenant` es la cuenta/cliente del sistema.
- El panel y el backend operan scopeados por `tenant_id`.
- La UI tiene selector de cuenta y todos los fetches relevantes salen filtrados por tenant.

### 2. Connection metadata y health persistido
- `IntegrationConnection` persiste:
  - `name`
  - `mode`
  - `environment`
  - `status`
  - `provider_account_id`
  - `config_payload`
  - `is_primary`
  - `priority`
  - `last_checked_at`
  - `last_check_ok`
  - `last_check_message`
- El panel separa claramente:
  - guardar configuracion
  - probar conexion
  - activar jobs
  - sync inicial

### 3. Provider registry
- Se introdujo `app/providers/registry.py`.
- La logica de Bsale ya no esta hardcodeada en el router admin.
- El provider `bsale` vive como definicion concreta en `app/providers/bsale.py`.
- El servicio de ingesta construye el runtime connector via registry + secret store.
- El endpoint `GET /admin/providers` expone metadata de providers para la UI.

### 4. Secrets, auditoria y onboarding
- `secret_ref` ya puede apuntar a secretos gestionados por `integration_secrets`.
- Se agrego `LocalEncryptedSecretStore`.
- Hay compatibilidad hacia atras con secretos legacy en texto plano: si `secret_ref` no es una referencia gestionada, se interpreta como valor raw.
- Se agrego `admin_audit_logs` y endpoint `GET /admin/audit`.
- El panel ahora muestra onboarding por conexion con checklist y progreso.

## Endpoints nuevos o relevantes
- `GET /admin/providers`
- `GET /admin/overview`
- `POST /admin/connectors`
- `PATCH /admin/connectors/{id}`
- `POST /admin/connectors/{id}/check`
- `POST /admin/connectors/{id}/primary`
- `GET /admin/connectors/{id}/jobs`
- `POST /admin/connectors/{id}/jobs/activate`
- `POST /admin/connectors/{id}/sync`
- `GET /admin/audit`
- Compatibilidad mantenida:
  - `PATCH /admin/connectors/{id}/mode`
  - `GET /connectors/bsale`
  - `PATCH /connectors/bsale`

## Cambios de esquema relevantes
- `0002_phase1_phase2_connections`
- `0003_phase3_phase4`

### Nuevas tablas
- `integration_secrets`
- `admin_audit_logs`

### Nuevas columnas clave
- `integration_connections.environment`
- `integration_connections.provider_account_id`
- `integration_connections.config_payload`
- `integration_connections.is_primary`
- `integration_connections.priority`
- `integration_mappings.connection_id`

## UI actual
La UI ya no es solo un debug panel plano. Ahora tiene:
- overview operativo por tenant
- selector de cuenta
- registry visible de providers
- wizard de alta de conexion
- tarjetas de conexion con onboarding
- jobs por conexion
- audit trail
- data canonica y errores por tenant

## Deuda que sigue existiendo
Esto ya no corresponde a las fases 1-4 originales; es backlog nuevo.

### Seguridad operativa
- El secret store local cifra en DB, pero sigue siendo una implementacion local. Falta integrar un backend externo serio si el sistema va a operar en entornos mas exigentes.
- No hay rotacion de secretos ni versionado de secretos.

### Modelo de permisos
- No existe autenticacion real de operadores.
- `actor` en auditoria hoy sale de header `x-actor` o default `ui`.

### Routing de jobs
- Los jobs se provisionan por conexion, pero no existe aun politica avanzada de routing por prioridad o failover entre conexiones del mismo provider.

### Mappings por conexion
- El modelo ya soporta `connection_id` opcional en mappings.
- Falta UI y flujo operacional para administrarlos a ese nivel.

### Providers adicionales
- El registry esta listo, pero solo existe `bsale` como implementacion concreta.

## Orden sugerido para el siguiente agente
Si el siguiente agente sigue desde aca, el orden razonable ya no es "cerrar fases", sino endurecer backlog:
1. autenticacion/autorizacion para admin
2. secret backend externo y rotacion
3. CRUD de mappings por `connection_id`
4. politicas de routing/failover entre conexiones del mismo provider
5. agregar mas providers al registry
