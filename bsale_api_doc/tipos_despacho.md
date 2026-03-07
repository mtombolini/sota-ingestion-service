* **Configuración**
* **Tipos de despacho**

Version: 📄 CL# Tipos de despacho

Listar tipos de despacho en la generación de un documento despacho.

## Estructura JSON

Al realizar una petición `HTTP`, el servicio retornara un JSON con la siguiente estructura:

Response /shipping_types/6.json

```js
{
"href":"https://api.bsale.io/v1/shipping_types/6.json",
"id":6,
"name":"Otros traslados no venta",
"codeSii":6,
"useDestinationOffice":0,
"state":0
}
```

### Atributos

| Atributo                       | Descripción                                                                  | Tipo dato |
| ------------------------------ | ----------------------------------------------------------------------------- | --------- |
| **href**                 | url del Tipos de despacho                                                     | String    |
| **id**                   | identificador único del Tipos de despacho                                    | Integer   |
| **name**                 | nombre del tipo de despacho                                                   | String    |
| **codeSii**              | código sii del tipo de despacho                                              | String    |
| **useDestinationOffice** | indica si el tipo de despacho requiere una sucursal de destino No(0) o Si (1) | Boolean   |
| **state**                | estado del tipo de despacho activo(0) o inactivo (1)                          | Boolean   |

## GET lista de Tipos de despacho

* GET `/v1/shipping_types.json` retornará todos los Tipos de despacho.

#### Parámetros

* **limit** , limita la cantidad de items de una respuesta JSON, por defecto el limit es 25, el máximo permitido es 50.
* **offset** , permite paginar los items de una respuesta JSON, por defecto el offset es 0.
* **fields** , solo devolver atributos específicos de un recurso
* **expand** , permite expandir instancias y colecciones para traer relaciones en una sola petición.
* **name** , Permite filtrar por nombre tipo libro.
* **codesii** , filtra por el código tributario del tipo de despacho.
* **state** , boolean (0 o 1) indica si los tipos de libro están activos(0) inactivos(1).

#### Ejemplos

* `GET /v1/shipping_types.json?limit=10&offset=0`
* `GET /v1/book_types.json?fields=[name,codesii,state]`

Response /shipping_types.json

```json
{
"href":"https://api.bsale.io/v1/shipping_types.json",
"count":9,
"limit":25,
"offset":0,
"items":[
{
"href":"https://api.bsale.io/v1/shipping_types/3.json",
"id":3,
"name":"Consignaciones",
"codeSii":3,
"useDestinationOffice":0,
"state":0
},
{
"href":"https://api.bsale.io/v1/shipping_types/4.json",
"id":4,
"name":"Entrega gratuita",
"codeSii":4,
"useDestinationOffice":0,
"state":0
},
{
"href":"https://api.bsale.io/v1/shipping_types/7.json",
"id":7,
"name":"Guía de devolución",
"codeSii":7,
"useDestinationOffice":0,
"state":0
},
{
"href":"https://api.bsale.io/v1/shipping_types/1.json",
"id":1,
"name":"Operación constituye venta",
"codeSii":1,
"useDestinationOffice":0,
"state":0
},
{
"href":"https://api.bsale.io/v1/shipping_types/6.json",
"id":6,
"name":"Otros traslados no venta",
"codeSii":6,
"useDestinationOffice":0,
"state":0
},
{
"href":"https://api.bsale.io/v1/shipping_types/5.json",
"id":5,
"name":"Traslados internos",
"codeSii":5,
"useDestinationOffice":1,
"state":0
},
{
"href":"https://api.bsale.io/v1/shipping_types/8.json",
"id":8,
"name":"Traslado para exportación. (no venta)",
"codeSii":8,
"useDestinationOffice":0,
"state":0
},
{
"href":"https://api.bsale.io/v1/shipping_types/2.json",
"id":2,
"name":"Ventas por efectuar",
"codeSii":2,
"useDestinationOffice":0,
"state":0
},
{
"href":"https://api.bsale.io/v1/shipping_types/9.json",
"id":9,
"name":"Venta para exportación",
"codeSii":9,
"useDestinationOffice":0,
"state":0
}
]
}
```

## GET un tipo de despacho

* GET `/v1/shipping_types/6.json` retornará un tipo de despacho específico.

Response /shipping_types/6.json

```json
{
"href":"https://api.bsale.io/v1/shipping_types/6.json",
"id":6,
"name":"Otros traslados no venta",
"codeSii":6,
"useDestinationOffice":0,
"state":0
}
```

[PreviousTipos de documentos](https://docs.bsale.dev/tipos-de-documentos)[NextFormas de pago](https://docs.bsale.dev/formas-de-pago)

* [Estructura JSON](https://docs.bsale.dev/tipos-de-despacho#estructura-json)
  * [Atributos](https://docs.bsale.dev/tipos-de-despacho#atributos)
* [GET lista de Tipos de despacho](https://docs.bsale.dev/tipos-de-despacho#get-lista-de-tipos-de-despacho)
* [GET un tipo de despacho](https://docs.bsale.dev/tipos-de-despacho#get-un-tipo-de-despacho)

Docs

* [Primeros pasos](https://docs.bsale.dev/get-started)

Enlaces

* [Sitio web Bsale Developers](https://www.bsale.dev/)
* [Canal Slack](https://join.slack.com/t/bsaledev/shared_invite/zt-3il0156pc-FRyHloRiaQTNDuKL9n_DCw)
* [Ticket de ayuda](https://ayuda.bsale.app/support/tickets/new)

Más
