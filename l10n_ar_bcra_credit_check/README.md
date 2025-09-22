BCRA Credit Check
Este módulo para Odoo permite consultar automáticamente el estado crediticio y los cheques rechazados de los clientes en la Central de Deudores del BCRA (Banco Central de la República Argentina) utilizando su CUIT/CUIL.

Características principales
Consulta en línea del informe crediticio del cliente mediante la API del BCRA.

Visualización del estado y detalle crediticio en la ficha del cliente.

Detección y listado de cheques rechazados.

Actualización automática mensual mediante tarea programada (cron).

Información disponible también en los pagos de clientes.

Instalación
Clona o descarga este repositorio en tu carpeta de addons de Odoo.

Instala el módulo desde la interfaz de Odoo.

Uso
En la ficha del cliente
Accede a la pestaña "Informe BCRA" dentro del formulario del cliente.

Haz clic en el botón "Consultar Informe BCRA" para obtener la información.

Se mostrará:

Estado crediticio.

Última fecha de actualización.

Detalle de deudas.

Cheques rechazados.

En pagos
Al seleccionar un cliente, se mostrará su situación crediticia y si tiene cheques rechazados.

Tarea programada
El módulo incluye una tarea cron activa que ejecuta mensualmente la actualización del estado crediticio de todos los clientes con CUIT/CUIL válido.

Dependencias
base

account

Seguridad y conexión
El módulo realiza llamadas a la API pública del BCRA usando requests.

No requiere autenticación adicional, pero ignora validación SSL (verify=False).

Autores
Horacio Montaño

Francisco Sulé

Licencia
AGPL-3

