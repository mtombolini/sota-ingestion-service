Sí. El **Servicio 2 — Ingestion Service** es una pieza crítica en SotA, porque en la práctica gran parte del valor del sistema depende de que los datos entren **bien, a tiempo, normalizados y trazables**. Si esta capa está mal diseñada, todo lo demás se contamina: forecast, recomendaciones, scores y optimización.

**Yo lo pensaría como un ** **subsistema de integración y estandarización operacional** **, no solo como un ETL simple.**

# **1. Rol real del Ingestion Service**

Su misión no es “traer datos”.

Su misión es:

* conectarse a sistemas externos heterogéneos
* extraer datos operacionales relevantes
* validarlos y limpiarlos
* **transformarlos al ****modelo canónico de SotA**
* detectar cambios y eventos importantes
* dejar los datos listos para consumo por el core y por los motores analíticos

En otras palabras: es la **frontera controlada** entre el mundo caótico de los ERPs/sistemas legados y el modelo limpio de SotA.

---

# **2. Qué tipos de fuentes debería soportar**

En este tipo de producto, yo asumiría desde el inicio que los clientes tendrán combinaciones distintas. Por eso el servicio debe ser **conector-agnóstico**.

## **Fuentes típicas**

* ERP: SAP, Softland, Defontana, Manager, otro ERP propio
* POS / retail systems
* WMS
* TMS o sistemas logísticos
* archivos CSV/Excel
* SFTP
* APIs REST / SOAP
* vistas SQL directas
* portales de proveedores
* archivos manuales cargados por usuario
* eventualmente GPS/fleet APIs

---

# **3. Qué datos debería ingerir**

No todo al principio. Hay que partir por los datasets que alimentan directamente los casos de uso.

## **Prioridad alta**

* stock actual por sucursal/bodega/SKU
* ventas o salidas históricas
* catálogo de productos
* catálogo de sucursales/bodegas
* catálogo de proveedores
* relación proveedor-SKU
* órdenes de compra históricas
* recepciones y lead times reales
* movimientos de inventario entre locaciones

## **Prioridad media**

* costos logísticos
* flota y capacidades
* horarios operativos
* precios históricos por proveedor
* rechazos / devoluciones / calidad
* tiempos de respuesta a cotizaciones

## **Prioridad baja al inicio**

* clima
* indicadores externos
* índices sectoriales
* señales enriquecidas no operacionales

---

# **4. Cómo estructuraría el servicio**

Yo lo dividiría internamente en 5 capas.

## **4.1 Connector Layer**

Un set de conectores por tipo de fuente.

Cada conector sabe:

* cómo autenticarse
* cómo leer datos
* con qué frecuencia
* qué tablas/endpoints/archivos consultar
* cómo paginar o continuar cargas
* cómo manejar errores propios de esa fuente

Ejemplos:

* sap_connector
* softland_connector
* csv_dropzone_connector
* sftp_connector
* postgres_read_connector
* rest_api_connector

La idea es que todos expongan una interfaz común.

---

## **4.2 Raw Landing Layer**

Primero guardas los datos **tal como llegaron**.

Esto es importante. No transformaría inmediatamente sin persistir raw.

### **Por qué**

Porque te sirve para:

* auditoría
* replay de cargas
* debugging
* comparar cambios
* corregir mappings sin pedir de nuevo la data
* trazabilidad frente al cliente

### **Qué guardar**

* payload original
* source system
* source object
* fecha/hora extracción
* job id
* hash/checksum
* tenant
* estado

Esto puede vivir:

* en object storage para payloads grandes
* y con metadata en Postgres

---

## **4.3 Validation & Normalization Layer**

Acá conviertes el dato externo al modelo SotA.

Por ejemplo:

### **ERP externo**

```
centro = "CD_001"
material = "SKU-9981"
stock_libre = 340
um = "UN"
```

### **Modelo canónico SotA**

```
{
  "tenant_id": "dist_nacional",
  "location_external_id": "CD_001",
  "location_type": "warehouse",
  "sku_external_id": "SKU-9981",
  "quantity_on_hand": 340,
  "uom": "unit",
  "snapshot_at": "2026-03-07T03:00:00Z",
  "source_system": "sap"
}
```

Acá también se resuelven:

* unidades de medida
* naming inconsistente
* códigos duplicados
* fechas
* monedas
* estructuras de sucursales/bodegas
* equivalencias de proveedor/producto

---

## **4.4 Canonical Persistence Layer**

Una vez limpio, el dato se escribe en tablas canónicas de SotA.

Ejemplo:

* stock_snapshots
* sales_transactions
* purchase_orders_raw_normalized
* supplier_sku_map
* inventory_movements
* receipts
* lead_time_observations

Esta capa ya no depende del ERP específico.

---

## **4.5 Change Detection / Event Emission Layer**

Después de persistir, el servicio detecta eventos relevantes.

Ejemplos:

* cambió el stock de SKU X en sucursal Y
* llegó una nueva OC recepcionada
* aumentó el lead time observado de proveedor Z
* hubo una venta anómala
* un SKU quedó sin supplier mapping válido

Y emite eventos internos tipo:

* stock.snapshot.updated
* sales.transactions.ingested
* purchase.order.received
* supplier.leadtime.observed
* product.master.updated

Estos eventos luego disparan:

* recálculo de forecast
* recálculo de recomendaciones
* alertas
* scoring
* invalidación de cache

---

# **5. Patrón operativo que usaría**

Yo usaría un patrón de pipeline así:

```
Extract -> Land Raw -> Validate -> Normalize -> Persist Canonical -> Emit Events
```

No haría integraciones “directo a tablas finales” desde el primer día.

Eso suele ser frágil y difícil de auditar.

---

# **6. Dos modos de ingesta**

El servicio debería soportar dos modos.

## **6.1 Batch / Scheduled ingestion**

Para fuentes que no exponen eventos o donde basta sincronización periódica.

Ejemplos:

* stock cada 15 min
* ventas cada hora
* catálogos cada noche
* órdenes de compra cada 2 horas

Este será probablemente el modo principal al inicio.

---

## **6.2 Event-driven ingestion**

Cuando el sistema origen puede emitir cambios en tiempo real.

Ejemplos:

* webhook por nueva OC
* webhook por recepción
* evento por cambio de estado logístico

Esto da más frescura, pero al principio no lo asumiría como requisito base para todos los clientes.

---

# **7. Modelo de jobs**

Yo no lo haría como una sola tarea genérica.

Lo haría como **jobs tipados**, trazables y reintentables.

## **Tipos de job**

* sync_product_catalog
* sync_branch_master
* sync_stock_snapshot
* sync_sales_transactions
* sync_purchase_orders
* sync_receipts
* sync_supplier_catalog
* sync_inventory_movements

Cada job debería registrar:

* tenant
* fuente
* rango temporal
* inicio / fin
* cantidad de registros
* cantidad insertados / actualizados / rechazados
* errores
* correlación con payload raw

---

# **8. Qué problemas reales debe resolver**

Este servicio debe anticipar problemas muy típicos.

## **8.1 Datos incompletos**

Ejemplo:

* ventas sin branch id
* stock sin timestamp
* SKU inexistente en maestro

Solución:

* reglas de validación
* quarantine bucket / dead-letter
* marcar registros inválidos sin romper toda la carga

---

## **8.2 Duplicados**

Muy común en cargas incrementales.

Solución:

* claves naturales
* hashes
* upserts idempotentes
* ventanas de deduplicación

---

## **8.3 Cambios de maestros**

Ejemplo:

* un mismo SKU cambia de código
* una sucursal se renombra
* un proveedor se fusiona

Solución:

* tablas de mapeo
* versionado de identidad externa vs interna
* master data governance mínimo

---

## **8.4 Latencia y consistencia**

No todo llega al mismo tiempo.

Ejemplo:

* ventas llegan hoy
* stock llega con 4 horas de retraso
* recepciones se actualizan al día siguiente

Solución:

* modelar timestamps de negocio y de ingesta por separado:
  * business_effective_at
  * ingested_at

Eso es clave.

---

# **9. Modelo de datos interno del ingestion service**

Yo agregaría tablas técnicas específicas, separadas del core de negocio.

## **Tablas técnicas sugeridas**

* integration_connections
* integration_connectors
* integration_jobs
* integration_job_runs
* integration_raw_objects
* integration_errors
* integration_mappings
* integration_watermarks
* integration_event_outbox

### **Qué guardan**

* configuración de conexión
* credenciales referenciadas por secret id
* última fecha/id sincronizado
* estado de salud del conector
* errores por fuente
* mappings de campos
* historial de corridas

---

# **10. Watermarks e incremental loads**

Esto es muy importante.

No quieres recargar todo siempre.

Entonces cada pipeline debe soportar **carga incremental** con watermarks.

## **Ejemplos**

* última fecha de movimiento leída
* último ID de transacción procesado
* último archivo consumido
* última modificación detectada

Así el conector sabe desde dónde continuar.

Ejemplo:

```
tenant: distribuidora_nacional
source: softland
object: sales_transactions
last_successful_watermark: 2026-03-07T00:00:00
```

---

# **11. Mappings configurables**

Un punto muy relevante: no haría el servicio rígido a una sola estructura de cliente.

Idealmente SotA debería permitir configurar mappings, por ejemplo:

* **columna origen **COD_ARTICULO** -> **sku_external_id
* **columna origen **BOD** -> **location_external_id
* **columna origen **STOCK_ACTUAL** -> **quantity_on_hand

Lo mismo para:

* unidades
* monedas
* estados
* tipos de documento

Eso evita hardcodear toda la lógica por cliente.

---

# **12. Validaciones que sí o sí pondría**

## **De esquema**

* tipos de dato
* columnas obligatorias
* formatos de fecha
* nullability

## **De negocio**

* stock no negativo, salvo casos explícitos
* venta con SKU válido
* OC con proveedor existente
* branch dentro del tenant
* cantidades coherentes
* lead times razonables

## **De consistencia**

* misma unidad de medida
* producto activo
* proveedor-SKU válido
* branch habilitada para despacho/recepción

---

# **13. Estrategia de errores**

Nunca dejaría que una falla menor bote toda la ingesta.

## **Haría esto**

* errores por registro cuando sea posible
* errores fatales por lote cuando la estructura esté rota
* reintentos automáticos
* dead-letter / quarantine para registros inválidos
* panel de observabilidad de integraciones

Estados típicos:

* pending
* running
* partial_success
* success
* failed
* quarantined

---

# **14. Seguridad del servicio**

Como tocará ERPs y data sensible, este servicio debe ser muy sobrio en seguridad.

## **Mínimos**

* credenciales en secret manager
* cifrado en tránsito
* conexiones salientes controladas
* whitelisting si aplica
* rotación de secretos
* masking de datos sensibles en logs
* segregación por tenant

Y, muy importante, no permitir que conectores escriban libremente en tablas de negocio sin pasar por validación.

---

# **15. Tecnologías concretas que usaría**


## **Opción  — Ingestion service en Python**

Mi preferencia si la ingesta y transformación será relevante.

### **Stack**

* FastAPI para endpoints administrativos
* workers con Celery o RQ
* pandas o polars para transformación
* SQLAlchemy
* Redis como broker/cache
* Postgres
* S3/object storage

Ventaja:

* más natural para pipelines de datos
* más alineado con servicios de forecast/ML

Yo probablemente haría:

* **Core backend en NestJS**
* **Ingestion + AI/optimization en Python**

Eso deja una separación bastante lógica.

---

# **16. Cómo lo imagino operando en SotA**

Ejemplo realista:

## **Caso: stock por sucursal**

1. Scheduler dispara **sync_stock_snapshot** cada 15 min
2. Conector Softland consulta stock actualizado
3. Respuesta raw se guarda
4. Se validan columnas, branch ids, SKU ids, UOM
5. Se normaliza al modelo canónico
6. Se hace upsert en **stock_snapshots**
7. Se detectan cambios significativos
8. **Se emite **stock.snapshot.updated
9. Recommendation engine recalcula SKUs afectados
10. Frontend muestra nueva alerta o recomendación

---

## **Caso: recepciones y lead times**

1. Cada 2 horas se sincronizan recepciones de OC
2. Se cruza fecha emisión vs fecha recepción
3. Se calcula lead time observado
4. **Se persiste en **lead_time_observations
5. Se actualiza supplier scoring
6. Purchase engine ajusta buffers de seguridad

Ese tipo de acoplamiento es donde el ingestion service realmente genera valor.

---

# **17. Qué dejaría fuera del MVP inicial**

Para no sobrediseñar, inicialmente no metería:

* CDC compleja sobre bases del cliente
* streaming real-time sofisticado
* data lake formal
* motor visual de mappings ultra enterprise
* integración con demasiadas fuentes simultáneas
* reconciliación automática demasiado avanzada

Partiría con:

* batch jobs
* conectores concretos
* modelo canónico
* raw persistence
* validación seria
* incremental loads
* observabilidad

Eso ya es robusto.

---

# **18. Definición breve y precisa**

Si tuviera que describir el Servicio 2 en una línea técnica:

**El Ingestion Service es una capa desacoplada de conectividad, normalización y publicación de eventos que transforma datos operacionales heterogéneos de ERP/POS/WMS en un modelo canónico confiable para el core transaccional y los motores de inteligencia de SotA.**

---

# **19. Mi recomendación concreta para SotA**

Para este proyecto, yo lo diseñaría así:

* **servicio independiente**
* **Python**
* **jobs batch + incremental**
* **raw zone + canonical zone**
* **mappings configurables por cliente**
* **Postgres + object storage + Redis**
* **event outbox para disparar recalculos**
* **errores quarantinables, no destructivos**
* **observabilidad por conector, job y dataset**

Y funcionalmente arrancaría con 6 pipelines:

1. catálogo de productos
2. sucursales/bodegas
3. stock snapshot
4. ventas históricas / transacciones
5. órdenes de compra + recepciones
6. proveedores + supplier-SKU map

Esos seis ya permiten construir una primera versión bastante seria de recomendaciones de compra y traslado.

**Puedo ahora aterrizar esto a un nivel más técnico y hacerte una de estas dos cosas: un ****diagrama de componentes del Ingestion Service** o un  **diseño de tablas y jobs concretos para implementarlo** **.**
