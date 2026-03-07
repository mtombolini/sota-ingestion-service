* **Introducción**

Version: 📄 CL# Introducción

👋 ¡Te damos la bienvenida a la documentación de la  **API Chile** !

Esta página te ayudará a iniciar con nuestra API así puedas orientarte en los distintos endpoints que se encuentran a tu disposición. Comencemos con esta guía rápida.

### Navegación

El **menú lateral izquierdo** te servirá como guía general para encontrar la documentación según el recurso necesites trabajar. Cada sección tendrá un  **menú lateral derecho** , que te mostrará las partes que componen el recurso.

tip

También puedes consultar nuestras [**preguntas frecuentes**](https://docs.bsale.dev/faq) y [**listado de errores**](https://docs.bsale.dev/faq#400).

### Autentificación

Si leíste los [**primeros pasos**](https://docs.bsale.dev/get-started)📎 sabrás que todos los requests deberán ser autentificados mediante un `access_token`, este token debe indicarse en la cabecera de la petición.

### Peticiones

Las peticiones son `HTTP REST` por lo que se debe especificar el **método** que se va a utilizar, junto al método se debe enviar en la cabecera de la petición el token de acceso que permite la autenticación en la API.

* **GET** , para obtener información de un recurso.
* **POST** , para crear un recurso.
* **PUT** , para modificar un recurso.
* **DELETE** , para eliminar un recurso.

### Ejemplo

El envío es simple, este es un ejemplo de la generación de una boleta electrónica. La **documentación completa** la encuentras en su sección correspondiente, [**"Documentos > Post un documento"**](https://docs.bsale.dev/CL/documentos)

* Request
* Response

```js
{
"documentTypeId":"1",
"officeId":"1",
"emissionDate":1462527931,
"details":[
{
"netUnitValue":10916,
"quantity":1,
"taxes":[
{
"code":14,
"percentage":19
}
],
"comment":"el nombre del producto que voy a vender"
}
]
}
```

### Ayuda

* Si necesitas aprender como trabaja Bsale de forma general puedes revisar [**nuestra base de conocimiento**](https://ayuda.bsale.app/support/home).
* Si tienes una duda puedes comunicarte con nosotros ingresando a la comunidad de [**slack**](https://join.slack.com/t/bsaledev/shared_invite/zt-30lqq3jd2-8fMuWb0sDGBA87vsMuTqSg) 👋

[NextDocumentos](https://docs.bsale.dev/documentos)

* [Navegación](https://docs.bsale.dev/first-steps#navegaci%C3%B3n)
* [Autentificación](https://docs.bsale.dev/first-steps#autentificaci%C3%B3n)
* [Peticiones](https://docs.bsale.dev/first-steps#peticiones)
* [Ejemplo](https://docs.bsale.dev/first-steps#ejemplo)
* [Ayuda](https://docs.bsale.dev/first-steps#ayuda)

Docs

* [Primeros pasos](https://docs.bsale.dev/get-started)

Enlaces

* [Sitio web Bsale Developers](https://www.bsale.dev/)
* [Canal Slack](https://join.slack.com/t/bsaledev/shared_invite/zt-3il0156pc-FRyHloRiaQTNDuKL9n_DCw)
* [Ticket de ayuda](https://ayuda.bsale.app/support/tickets/new)
