* **Configuración**
* **Webhooks**

Version: 📄 CL# Webhooks instancia

info

Para consumir el recurso de la instancia, se debe usar `https://credential.bsale.io` como **url base**

#### Ejemplo

* `GET /v1/instances/basic/d466gsgs287da0ffbe9dd56eb058095fa13hgs772cb0c1d9e.json`

#### Respuesta

```json
{
"id":129577,
"code":"98765432-1",
"name":"Empresa Bsale Demo SA",
"state":0,
"country":"CL",
"trial":0,
"trialEnd":1493335314
}
```

#### Parámetros

* **id** , Identificador de la instancia en la cual está asociado el `access_token`
* **code** , Rut empresa
* **name** , Nombre empresa
* **state** , Estado empresa
* **country** , País empresa
* **trial** , Empresa prueba 30 días (1), definitiva (0)
* **trialEnd** , fecha unix termino trial

 **Tags:** * [webhooks](https://docs.bsale.dev/tags/webhooks)

[PreviousWebhooks](https://docs.bsale.dev/formas-de-pago/webhooks)[NextTipos de libro](https://docs.bsale.dev/tipos-de-libros)

Docs

* [Primeros pasos](https://docs.bsale.dev/get-started)

Enlaces

* [Sitio web Bsale Developers](https://www.bsale.dev/)
* [Canal Slack](https://join.slack.com/t/bsaledev/shared_invite/zt-3il0156pc-FRyHloRiaQTNDuKL9n_DCw)
* [Ticket de ayuda](https://ayuda.bsale.app/support/tickets/new)
