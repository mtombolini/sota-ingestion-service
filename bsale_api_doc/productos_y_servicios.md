* **Productos y servicios**

Version: 📄 CL# Productos y servicios

Listar productos, variantes, cantidades, crear productos.

Cómo funciona la interfaz de Bsale, mira éstos videos:

* Creación un producto [Ver](https://www.youtube.com/watch?v=eY3YBu3b-j0)

info

 **Un producto puede tener 1 o más variantes** . Ej, (Nombre Producto) Poleron Blanco, (Nombre Variantes) Talla L, Talla M, Talla S.  **La variante se debe crear una vez creado el producto** . Para vender un producto/variante creado, se debe indicar en el arreglo `details` del documento.

## Estructura JSON

Al realizar una petición `HTTP`, el servicio retornara un JSON con la siguiente estructura:

Response /v1/products/92.json

```js
{
"href":"https://api.bsale.io/v1/products/92.json",
"id":92,
"name":null,
"description":null,
"classification":0,
"ledgerAccount":null,
"costCenter":null,
"allowDecimal":0,
"stockControl":1,
"printDetailPack":0,
"state":99,
"prestashopProductId":0,
"presashopAttributeId":0,
"product_type":{
"href":"https://api.bsale.io/v1/product_types/1.json",
"id":"1"
},
"product_taxes":{
"href":"https://api.bsale.io/v1/products/92/product_taxes.json"
}
}
```

### Atributos

| Atributo                       | Descripción                                                                                 | Tipo dato |
| ------------------------------ | -------------------------------------------------------------------------------------------- | --------- |
| **href**                 | url del producto                                                                             | String    |
| **id**                   | identificador único del producto                                                            | Integer   |
| **name**                 | nombre del producto                                                                          | String    |
| **description**          | descripción del producto                                                                    | String    |
| **classification**       | indica la clase del producto 0 es producto, 1 es servicio y 3 si es un pack o promocion      | Integer   |
| **ledgerAccount**        | cuenta contable del producto                                                                 | String    |
| **costCenter**           | centro de costo del producto                                                                 | String    |
| **allowDecimal**         | indica si el producto permite trabajar con decimales, ej, productos pesables. No(0) o Si (1) | Boolean   |
| **stockControl**         | indica si el producto controlara stock No(0) o Si (1)                                        | Boolean   |
| **printDetailPack**      | indica si se muestra el detalle del pack No(0) o Si (1)                                      | Boolean   |
| **state**                | estado del producto activo(0) o inactivo (1)                                                 | Boolean   |
| **prestashopProductId**  | identificador del producto en prestashop en el caso de existir la integración*legacy*     |           |
| **presashopAttributeId** | identificador del producto en prestashop en el caso de existir la integración*legacy*     |           |
| **product_type**         | nodo que indica la relación con el tipo de producto                                         |           |
| **product_taxes**        | nodo que indica los impuestos asociados al producto                                          |           |

## GET lista de productos

* GET `/v1/products.json` retornará todos los productos.

#### Parámetros

* **limit** , limita la cantidad de items de una respuesta JSON, por defecto el limit es 25, el máximo permitido es 50.
* **offset** , permite paginar los items de una respuesta JSON, por defecto el offset es 0.
* **fields** , solo devolver atributos específicos de un recurso
* **expand** , permite expandir instancias y colecciones para traer relaciones en una sola petición.
* **name** , Permite filtrar por nombre del producto.
* **ledgeraccount** , filtra por cuenta contable de los productos.
* **costcenter** , filtra centro de costo de los productos.
* **producttypeid** , filtra por tipo de producto.
* **state** , boolean (0 o 1) indica si los productos están activos(0) inactivos (1).

#### Ejemplos

* `GET /v1/products.json?limit=10&offset=0`
* `GET /v1/products.json?fields=[name,ledgeraccount,description]`
* `GET /v1/products.json?producttypeid=1`
* `GET /v1/products.json?expand=[product_type]`
* `GET /v1/products.json?classification=3`

Response /products.json

```json
{
"href":"https://api.bsale.io/v1/products.json",
"count":693,
"limit":3,
"offset":0,
"items":[
{
"href":"https://api.bsale.io/v1/products/731.json",
"id":731,
"name":"11% Avalúo Fiscal Depto 515,",
"description":null,
"classification":1,
"ledgerAccount":"",
"costCenter":"",
"allowDecimal":0,
"stockControl":0,
"printDetailPack":0,
"state":0,
"prestashopProductId":0,
"presashopAttributeId":0,
"product_type":{
"href":"https://api.bsale.io/v1/product_types/1.json",
"id":"1"
},
"product_taxes":{
"href":"https://api.bsale.io/v1/products/731/product_taxes.json"
}
},
{
"href":"https://api.bsale.io/v1/products/474.json",
"id":474,
"name":"24 clases 3 veces a la semana",
"description":null,
"classification":3,
"ledgerAccount":"",
"costCenter":"",
"allowDecimal":0,
"stockControl":0,
"printDetailPack":0,
"state":0,
"prestashopProductId":0,
"presashopAttributeId":0,
"product_type":{
"href":"https://api.bsale.io/v1/product_types/1.json",
"id":"1"
},
"product_taxes":{
"href":"https://api.bsale.io/v1/products/474/product_taxes.json"
}
},
{
"href":"https://api.bsale.io/v1/products/703.json",
"id":703,
"name":"2x1",
"description":null,
"classification":3,
"ledgerAccount":null,
"costCenter":null,
"allowDecimal":0,
"stockControl":0,
"printDetailPack":0,
"state":0,
"prestashopProductId":0,
"presashopAttributeId":0,
"product_type":{
"href":"https://api.bsale.io/v1/product_types/1.json",
"id":"1"
},
"product_taxes":{
"href":"https://api.bsale.io/v1/products/703/product_taxes.json"
}
}
],
"next":"https://api.bsale.io/v1/products.json?limit=3&offset=3"
}
```

## GET un producto

* GET `/v1/products/62.json<span> </span>`retornará un producto específico.

#### Parámetros

* **expand** , permite expandir instancias y colecciones para traer relaciones en una sola petición.

#### Ejemplos

* `GET /v1/products/150.json?expand=[product_type]`

Response /products/150.json

```json
{
"href":"https://api.bsale.io/v1/products/150.json",
"id":150,
"name":"polera",
"description":"",
"classification":0,
"ledgerAccount":"",
"costCenter":"",
"allowDecimal":0,
"stockControl":1,
"printDetailPack":0,
"state":0,
"prestashopProductId":0,
"presashopAttributeId":0,
"product_type":{
"href":"https://api.bsale.io/v1/product_types/1.json",
"id":"1"
},
"product_taxes":{
"href":"https://api.bsale.io/v1/products/150/product_taxes.json"
}
}
```

## GET variantes de un producto

* GET `/v1/products/62/variants.json` retorna las variantes de un producto.

Response /products/:id/variants.json

```json
{
"href":"https://api.bsale.io/v1/variants.json",
"count":3,
"limit":25,
"offset":0,
"items":[
{
"href":"https://api.bsale.io/v1/variants/500.json",
"id":500,
"description":"gap",
"unlimitedStock":0,
"allowNegativeStock":0,
"state":0,
"barCode":"1351176376",
"code":"1351176376",
"imagestionCenterCost":0,
"imagestionAccount":0,
"imagestionConceptCod":0,
"imagestionProyectCod":0,
"imagestionCategoryCod":0,
"imagestionProductId":0,
"serialNumber":0,
"prestashopCombinationId":0,
"prestashopValueId":0,
"product":{
"href":"https://api.bsale.io/v1/products/150.json",
"id":"150"
},
"attribute_values":{
"href":"https://api.bsale.io/v1/variants/500/attribute_values.json"
},
"costs":{
"href":"https://api.bsale.io/v1/variants/500/costs.json"
}
},
{
"href":"https://api.bsale.io/v1/variants/499.json",
"id":499,
"description":"L",
"unlimitedStock":0,
"allowNegativeStock":0,
"state":0,
"barCode":"1351176361",
"code":"1351176361",
"imagestionCenterCost":0,
"imagestionAccount":0,
"imagestionConceptCod":0,
"imagestionProyectCod":0,
"imagestionCategoryCod":0,
"imagestionProductId":0,
"serialNumber":0,
"prestashopCombinationId":0,
"prestashopValueId":0,
"product":{
"href":"https://api.bsale.io/v1/products/150.json",
"id":"150"
},
"attribute_values":{
"href":"https://api.bsale.io/v1/variants/499/attribute_values.json"
},
"costs":{
"href":"https://api.bsale.io/v1/variants/499/costs.json"
}
},
{
"href":"https://api.bsale.io/v1/variants/498.json",
"id":498,
"description":"verde",
"unlimitedStock":0,
"allowNegativeStock":0,
"state":0,
"barCode":"1351176256",
"code":"1351176256",
"imagestionCenterCost":0,
"imagestionAccount":0,
"imagestionConceptCod":0,
"imagestionProyectCod":0,
"imagestionCategoryCod":0,
"imagestionProductId":0,
"serialNumber":0,
"prestashopCombinationId":0,
"prestashopValueId":0,
"product":{
"href":"https://api.bsale.io/v1/products/150.json",
"id":"150"
},
"attribute_values":{
"href":"https://api.bsale.io/v1/variants/498/attribute_values.json"
},
"costs":{
"href":"https://api.bsale.io/v1/variants/498/costs.json"
}
}
]
}
```

## GET impuestos de un producto

* GET `/v1/products/150/product_taxes.json` Retornará impuestos asociados al producto.

Response /products/150/product_taxes.json

```json
{
"href":"https://api.bsale.io/v1/products/150/product_taxes.json",
"count":2,
"limit":25,
"offset":0,
"items":[
{
"href":"https://api.bsale.io/v1/products/150/product_taxes/159.json",
"id":"159",
"tax":{
"href":"https://api.bsale.io/v1/taxes/1.json",
"id":"1"
}
}
]
}
```

#### GET un impuesto de un producto

* GET `/v1/products/150/product_taxes/159.json` Retornará un impuesto asociado al producto.

Response /products/150/product_taxes/159.json

```json
{
"href":"https://api.bsale.io/v1/products/150/product_taxes/159.json",
"id":"159",
"tax":{
"href":"https://api.bsale.io/v1/taxes/1.json",
"id":"1"
}
}
```

## GET cantidad de productos

* GET `/v1/products/count.json` Retornará la cantidad de registros de productos

```json
{
"count":53
}
```

* **state** , boolean (0 o 1) indica si los productos están activos(0) inactivos (1).

## POST un producto

* POST `/v1/products.json`

Se debe enviar un Json con la siguiente estructura.

### Ejemplo JSON

#### Envío

```json
{
"name":"Calcetines",
"allowDecimal":0,
"stockControl":1,
"productTypeId":1
}
```

* **name** , nombre del producto (String).
* **description** , descripción del producto (String).
* **classification** , indica la clase del producto 0 es producto, 1 es servicio (Integer)
* **stockControl** , indica si el producto controlara stock No(0) o Si (1) (Boolean).
* **productTypeId** , Id del tipo de producto (Integer)
* **serialNumber** , indica si el producto controla o no series. No (0) o Si (1) (Integer)
* **isLot** , indica si la serie se podrá repetir. No (0) o Si (1) (Integer)
* **taxes** , Arreglo que referencia los [id&#39;s de impuesto](https://docs.bsale.dev/CL/impuestos#get-lista-de-impuestos) asociados al producto.

tip

Si no se definen impuestos en la creación del producto, se asignarán los configurados por defecto en Bsale.

#### Respuesta

```json
{
"stockControl":1,
"name":"Calcetines",
"ledgerAccount":"",
"href":"https://api.bsale.io/v1/products/97.json",
"prestashopProductId":0,
"presashopAttributeId":0,
"costCenter":"",
"printDetailPack":0,
"product_type":{
"href":"https://api.bsale.io/v1/product_types/1.json",
"id":"1"
},
"classification":1,
"description":"",
"id":97,
"state":0,
"allowDecimal":0
}
```

## PUT un producto

* PUT `/v1/products/97.json`

Se debe enviar un Json con la siguiente estructura.

### Ejemplo JSON

#### Envío

```json
{
"id":"97",
"productTypeId":10,
"allowDecimal":1,
"name":"Calcetines de Mujer"
}
```

#### Respuesta

```json
{
"stockControl":1,
"name":"Calcetines de Mujer",
"ledgerAccount":"Calcetas",
"href":"https://api.bsale.io/v1/products/97.json",
"prestashopProductId":0,
"presashopAttributeId":0,
"costCenter":"23",
"printDetailPack":0,
"product_type":{
"href":"https://api.bsale.io/v1/product_types/1.json",
"id":"1"
},
"classification":1,
"description":"Multiples colores de calcetines",
"id":97,
"state":0,
"allowDecimal":0
}
```

## POST un Pack

* POST `/v2/products/pack.json`

Se debe enviar un Json con la siguiente estructura.

### Ejemplo JSON

#### Envío

```json
{
"productTypeId":1,
"basePrice":10000,
"name":"Pack de ejemplo - api - 5",
"barCode":"90101001015",
"code":"90101001015",
"priceWithTax":0,
"printDetailPack":1,
"packDetails":[
{
"multipleVariant":0,
"productPromoId":0,
"quantity":2,
"variantPromoId":8901
}
]
}
```

* **productTypeId** , Id tipo de producto asociado al pack (Integer).
* **basePrice** , Valor base del pack (Integer)
* **name** , descripción del pack (String).
* **barCode** , Código de barra del pack (String).
* **code** , SKU del pack (String)
* **priceWithTax** , Indica si basePrice es un valor bruto. No (0) o Si (1) (Boolean)
* **printDetailPack** , Desea imprimir el detalle del pack en los documentos. No (0) o Si (1) (Boolean)
* **packDetails.multipleVariant** , Pack soportará multiples variantes. No (0) o Si (1) (Boolean)
* **packDetails.productPromoId** , Id producto asociado al pack
* **packDetails.quantity** , Cantidad de producto incluido en el pack
* **packDetails.variantPromoId** , Id variante asociado al pack

tip

Bsale soporta la creación de pack "cerrados" y "abiertos". Los cerrados, son los que se indica la variante y cantidad a utilizar. Los abiertos son aquellos que se les indica solamente el producto, el cual podrá seleccionar las variantes al vender.

#### Respuesta

```json
{
"code":"201",
"data":{
"id":2564,
"name":"Pack de ejemplo - Documentación",
"classification":3,
"printPackDetail":1,
"state":1,
"productTypeId":1,
"brandId":0,
"sku":"90101001015",
"barCode":"90101001015",
"packDetail":[
{
"id":29,
"productId":0,
"variantId":8901,
"quantity":2,
"state":0,
"packId":2564,
"multipleVariant":0,
"packInfo":{}
}
]
}
}
```

## DELETE un producto virtualmente

* DELETE `/v1/products/97.json` Cambia el estado del producto.

danger

El producto no estará visible mediante interfaz y tendrá un `state` 1

```json
{
"href":"https://api.bsale.io/v1/products/97.json",
"id":97,
"name":"Calcetines",
"description":"Multiples colores de calcetines",
"classification":1,
"ledgerAccount":"Calcetas",
"costCenter":"23",
"allowDecimal":0,
"stockControl":1,
"printDetailPack":0,
"state":1,
"prestashopProductId":0,
"presashopAttributeId":0,
"product_type":{
"href":"https://api.bsale.io/v1/product_types/1.json",
"id":"1"
}
}
```

[PreviousWebhooks](https://docs.bsale.dev/documentos/webhooks)[NextTipos de productos y servicios](https://docs.bsale.dev/tipos-de-productos-y-servicios)

* [Estructura JSON](https://docs.bsale.dev/productos-y-servicios#estructura-json)
  * [Atributos](https://docs.bsale.dev/productos-y-servicios#atributos)
* [GET lista de productos](https://docs.bsale.dev/productos-y-servicios#get-lista-de-productos)
* [GET un producto](https://docs.bsale.dev/productos-y-servicios#get-un-producto)
* [GET variantes de un producto](https://docs.bsale.dev/productos-y-servicios#get-variantes-de-un-producto)
* [GET impuestos de un producto](https://docs.bsale.dev/productos-y-servicios#get-impuestos-de-un-producto)
* [GET cantidad de productos](https://docs.bsale.dev/productos-y-servicios#get-cantidad-de-productos)
* [POST un producto](https://docs.bsale.dev/productos-y-servicios#post-un-producto)
  * [Ejemplo JSON](https://docs.bsale.dev/productos-y-servicios#ejemplo-json)
* [PUT un producto](https://docs.bsale.dev/productos-y-servicios#put-un-producto)
  * [Ejemplo JSON](https://docs.bsale.dev/productos-y-servicios#ejemplo-json-1)
* [POST un Pack](https://docs.bsale.dev/productos-y-servicios#post-un-pack)
  * [Ejemplo JSON](https://docs.bsale.dev/productos-y-servicios#ejemplo-json-2)
* [DELETE un producto virtualmente](https://docs.bsale.dev/productos-y-servicios#delete-un-producto-virtualmente)
