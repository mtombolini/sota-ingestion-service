* **Configuración**
* **Tipos de documentos**

Version: 📄 CL# Tipos de documentos

Listar y editar tipos de documentos configuradas en Bsale.

info

Para que un tipo de documento pueda ser referenciado, es importante que su  **estado sea 0** . (`state=0`)

## Estructura JSON

Al realizar una petición `HTTP`, el servicio retornara un JSON con la siguiente estructura:

Response /document_types/1.json

```js
{
"href":"https://api.bsale.io/v1/document_types/1.json",
"id":1,
"name":"NOTA VENTA",
"initialNumber":1,
"codeSii":"",
"isElectronicDocument":0,
"breakdownTax":1,
"use":0,
"isSalesNote":1,
"isExempt":0,
"restrictsTax":0,
"useClient":1,
"messageBodyFormat":null,
"thermalPrinter":1,
"state":0,
"copyNumber":3,
"isCreditNote":0,
"continuedHigh":0,
"ledgerAccount":null,
"ipadPrint":0,
"ipadPrintHigh":"0"
}
```

### Atributos

| Atributo                       | Descripción                                                                                              | Tipo dato |
| ------------------------------ | --------------------------------------------------------------------------------------------------------- | --------- |
| **href**                 | url del Tipos de documentos                                                                               | String    |
| **id**                   | identificador único del Tipos de documentos                                                              | Integer   |
| **name**                 | nombre del del tipo de documento                                                                          | String    |
| **initialNumber**        | folio inicial del tipo de documento                                                                       | Integer   |
| **codeSii**              | código tributario del tipo de documento                                                                  | String    |
| **isElectronicDocument** | indica si el tipo de documento es electrónico No(0) o Si(1)                                              | Boolean   |
| **breakdownTax**         | indica si el tipo de documento desglosa impuesto No(0) o Si(1)                                            | Boolean   |
| **use**                  | indica si el uso que se le da al tipo de documento venta(0), devolución(1), despacho(2), liquidación(3) | Integer   |
| **isSalesNote**          | indica si el tipo de documento es una nota de venta No(0) o Si(1)                                         | Boolean   |
| **isExempt**             | indica si el tipo de documento es exento No(0) o Si(1)                                                    | Boolean   |
| **restrictsTax**         | indica si el tipo de documento restringe impuestos No(0) o Si(1)                                          | Boolean   |
| **useClient**            | indica si el tipo de documento requiere un cliente No(0) o Si(1)                                          | Boolean   |
| **messageBodyFormat**    | formato del tipo de documento                                                                             | String    |
| **thermalPrinter**       | indica si el tipo de documento es impreso en impresora térmica No(0) o Si(1)                             | Boolean   |
| **state**                | estado del tipo de documento activo(0) o inactivo (1)                                                     | Boolean   |
| **copyNumber**           | numero de copias del tipo de documento                                                                    | Integer   |
| **isCreditNote**         | indica si el tipo de documento es una nota de crédito No(0) o Si(1)                                      | Boolean   |
| **continuedHigh**        | indica si el tipo de documento se imprime con alto continuo No(0) o Si(1)                                 | Boolean   |
| **ledgerAccount**        | cuenta contable del tipo de documento                                                                     | String    |
| **ipadPrint**            | configuración para Ipad                                                                                  | Boolean   |
| **ipadPrintHigh**        | configuración para Ipad                                                                                  | Boolean   |

## GET lista de Tipos de documentos

* GET `/v1/document_types.json` retornará todos los Tipos de documentos.

#### Parámetros

* **limit** , limita la cantidad de items de una respuesta JSON, por defecto el limit es 25, el máximo permitido es 50.
* **offset** , permite paginar los items de una respuesta JSON, por defecto el offset es 0.
* **fields** , solo devolver atributos específicos de un recurso
* **expand** , permite expandir instancias y colecciones para traer relaciones en una sola petición.
* **name** , Permite filtrar por nombre del tipo de documento.
* **codesii** , filtra por el código tributario del tipo de documento (String).
* **ledgeraccount** , filtra por la cuenta contable del tipo de documento.
* **booktypeid** , filtra por el tipo de libro que pertenece (Integer).
* **iselectronicdocument** , permite filtrar si el tipo de documento es electrónico No(0) o Si(1) (Boolean).
* **issalesnote** , permite filtrar si el tipo de documento es una nota de venta No(0) o Si(1) (Boolean).
* **state** , boolean (0 o 1) indica si los tipos de documento están activos(0) inactivos(1).

info

* Consultar códigos SII [Ver](https://ayuda.bsale.app/support/solutions/articles/151000005963-c%C3%B3digos-tributarios-de-chile)

#### Ejemplos

* `GET /v1/document_types.json?limit=10&offset=0`
* `GET /v1/document_types.json?fields=[codesii,ledgeraccount,state]`
* `GET /v1/document_types.json?expand=[book_type]`
* `GET /v1/document_types.json?codesii=33`
* `GET /v1/document_types.json?state=0`

Response /document_types.json

```json
{
"href":"https://api.bsale.io/v1/document_types.json",
"count":3,
"limit":25,
"offset":0,
"items":[
{
"href":"https://api.bsale.io/v1/document_types/2.json",
"id":2,
"name":"FACTURA EXENTA O NO AFECTA ELECTRONICA",
"initialNumber":1,
"codeSii":"34",
"isElectronicDocument":1,
"breakdownTax":1,
"use":0,
"isSalesNote":0,
"isExempt":1,
"restrictsTax":0,
"useClient":1,
"messageBodyFormat":"",
"thermalPrinter":1,
"state":0,
"copyNumber":2,
"isCreditNote":0,
"continuedHigh":0,
"ledgerAccount":null,
"ipadPrint":0,
"ipadPrintHigh":"0",
"book_type":{
"href":"https://api.bsale.io/v1/book_types/1.json",
"id":"1"
}
},
{
"href":"https://api.bsale.io/v1/document_types/3.json",
"id":3,
"name":"NOTA CREDITO ELECTRONICA",
"initialNumber":43,
"codeSii":"61",
"isElectronicDocument":1,
"breakdownTax":1,
"use":1,
"isSalesNote":0,
"isExempt":0,
"restrictsTax":0,
"useClient":1,
"messageBodyFormat":"",
"thermalPrinter":1,
"state":0,
"copyNumber":0,
"isCreditNote":1,
"continuedHigh":0,
"ledgerAccount":null,
"ipadPrint":0,
"ipadPrintHigh":"0",
"book_type":{
"href":"https://api.bsale.io/v1/book_types/1.json",
"id":"1"
}
},
{
"href":"https://api.bsale.io/v1/document_types/1.json",
"id":1,
"name":"NOTA VENTA",
"initialNumber":1,
"codeSii":"",
"isElectronicDocument":0,
"breakdownTax":1,
"use":0,
"isSalesNote":1,
"isExempt":0,
"restrictsTax":0,
"useClient":1,
"messageBodyFormat":null,
"thermalPrinter":1,
"state":0,
"copyNumber":3,
"isCreditNote":0,
"continuedHigh":0,
"ledgerAccount":null,
"ipadPrint":0,
"ipadPrintHigh":"0"
}
]
}
```

## GET un tipo de documento

* GET `/v1/document_types/1.json` retornará un tipo de documento específico.

#### Parámetros

* **expand** , permite expandir instancias y colecciones.

#### Ejemplos

* `GET /v1/document_types/1.json?expand=[book_type]`

Response /document_types/1.json

```json
{
"href":"https://api.bsale.io/v1/document_types/1.json",
"id":1,
"name":"NOTA VENTA",
"initialNumber":1,
"codeSii":"",
"isElectronicDocument":0,
"breakdownTax":1,
"use":0,
"isSalesNote":1,
"isExempt":0,
"restrictsTax":0,
"useClient":1,
"messageBodyFormat":null,
"thermalPrinter":1,
"state":0,
"copyNumber":3,
"isCreditNote":0,
"continuedHigh":0,
"ledgerAccount":null,
"ipadPrint":0,
"ipadPrintHigh":"0"
}
```

## GET cantidad de tipos de documentos

* GET `/v1/document_types/count.json` Retornará cantidades de registros.
* **state** , boolean (0 o 1) indica si los clientess están activos(0) inactivos (1).

```json
{
"count":13
}
```

## GET CAF actual de un tipo de documento

* GET `/v1/document_types/caf.json` Retornará el archivo CAF.

info

CAF, proviene de " **Código de Asignación de Folios** ". [Ver](https://www.sii.cl/preguntas_frecuentes/catastro/001_012_2020.htm#:~:text=%C2%BFQu%C3%A9%20significa%20el%20C%C3%B3digo%20de,Documentos%20Tributarios%20Electr%C3%B3nicos%20(DTE)%3F&text=El%20CAF%20en%20los%20DTE,procedimientos%20establecidos%20por%20el%20SII.)

#### Parámetros

* **codesii** , filtra por el código tributario del tipo de documento (String).
* **documenttypeid** , filtra por el identificador del tipo de documento (Integer).
* **nextnumber** , filtra por el próximo folio que se desea utilizar (integer).

#### Ejemplos

* `GET /v1/document_types/caf.json?codesii=33`
* `GET /v1/document_types/caf.json?documenttypeid=1`
* `GET /v1/document_types/caf.json?codesii=33&nextnumber=51`

```json
{
"startDate":1522292400,
"expirationDate":1546225200,
"startNumber":5,
"endNumber":5,
"lastNumberUsed":0,
"numbersAvailable":2,
"expired":false
}
```

* **startDate** , fecha en que inicia el caf (integer).
* **expirationDate** , fecha en que vence el caf (integer).
* **startNumber** , folio inicial del caf (integer).
* **endNumber** , folio final del caf (integer).
* **lastNumberUsed** , ultimo folio utilizado para el tipo de documento (integer).
* **numbersAvailable** , folios disponibles para el tipo de documento (Integer).
* **expired** , indica si el caf esta expirado (Boolean)

## GET folios disponibles de un tipo de documento

* GET `/v1/document_types/number_availables.json` Retornará registros de números de folios.

#### Parámetros

* **codesii** , filtra por el código tributario del tipo de documento (String).
* **documenttypeid** , filtra por el identificador del tipo de documento (Integer).

#### Ejemplos

* `GET /v1/document_types/number_availables.json?codesii=33`
* `GET /v1/document_types/number_availables.json?documenttypeid=1`

```json
{
"numbers_available":2574,
"last":32119
}
```

* **numbers_available** , folios disponibles para el tipo de documento (Integer).
* **last** , ultimo folio utilizado para el tipo de documento (integer).

## PUT un tipo de documento

* PUT `/v1/document_types.json`

note

Solo es posible editar "Nombre del documento", "Estado" y "Si requiere datos de cliente"

#### Envío

```json
{
"name":"Documento Boleta",
"state":1,
"useClient":1
}
```

#### Respuesta

```json
{
"href":"https://api.bsale.io/v1/document_types/10.json",
"id":10,
"name":"Documento Boleta",
"initialNumber":1,
"codeSii":"35",
"isElectronicDocument":0,
"breakdownTax":0,
"use":0,
"isSalesNote":0,
"isExempt":0,
"restrictsTax":1,
"useClient":1,
"messageBodyFormat":null,
"thermalPrinter":1,
"state":1,
"copyNumber":0,
"isCreditNote":0,
"continuedHigh":1,
"ledgerAccount":"",
"ipadPrint":0,
"ipadPrintHigh":0,
"restrictClientType":2,
"useMaxDays":0,
"maxDays":-1,
"book_type":{
"href":"https://api.bsale.io/v1/book_types/1.json",
"id":"1"
}
}
```

[PreviousMonedas](https://docs.bsale.dev/monedas)[NextTipos de despacho](https://docs.bsale.dev/tipos-de-despacho)

* [Estructura JSON](https://docs.bsale.dev/tipos-de-documentos#estructura-json)
  * [Atributos](https://docs.bsale.dev/tipos-de-documentos#atributos)
* [GET lista de Tipos de documentos](https://docs.bsale.dev/tipos-de-documentos#get-lista-de-tipos-de-documentos)
* [GET un tipo de documento](https://docs.bsale.dev/tipos-de-documentos#get-un-tipo-de-documento)
* [GET cantidad de tipos de documentos](https://docs.bsale.dev/tipos-de-documentos#get-cantidad-de-tipos-de-documentos)
* [GET CAF actual de un tipo de documento](https://docs.bsale.dev/tipos-de-documentos#get-caf-actual-de-un-tipo-de-documento)
* [GET folios disponibles de un tipo de documento](https://docs.bsale.dev/tipos-de-documentos#get-folios-disponibles-de-un-tipo-de-documento)
* [PUT un tipo de documento](https://docs.bsale.dev/tipos-de-documentos#put-un-tipo-de-documento)

Docs

* [Primeros pasos](https://docs.bsale.dev/get-started)

Enlaces

* [Sitio web Bsale Developers](https://www.bsale.dev/)
* [Canal Slack](https://join.slack.com/t/bsaledev/shared_invite/zt-3il0156pc-FRyHloRiaQTNDuKL9n_DCw)
* [Ticket de ayuda](https://ayuda.bsale.app/support/tickets/new)

Más

* [Bsale 🇨🇱](https://www.bsale.cl/)
* [Bsale 🇵🇪](https://www.bsale.com.pe/)
* [Bsale ](https://www.bsale.com.mx/)
