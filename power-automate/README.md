# Correo de aprobación de desmovilización

Asunto recomendado:

```text
[Acción requerida] Aprobar desmovilización SIA {{id_sias}} – {{nomb_area}}
```

El archivo `correo-aprobacion-desmovilizacion.html` está preparado para el cuerpo HTML de **Enviar un correo electrónico (V2)** en Power Automate.

## Tokens

Reemplace cada token con contenido dinámico del flujo:

| Token | Fuente sugerida |
|---|---|
| `{{id_sias}}` | `triggerBody()?['feature']?['attributes']?['id_sias']` |
| `{{obs_desmovilizacion}}` | `triggerBody()?['feature']?['attributes']?['obs']` |
| `{{empresa}}` | Consulta de la SIA productiva |
| `{{nomb_area}}` | Consulta de la SIA productiva |
| `{{nomb_contrato}}` | Consulta de la SIA productiva; usar `Sin contrato informado` si está vacío |
| `{{nombre_gerencia_responsable}}` | Consulta de la SIA productiva |
| `{{termino_de_ejecucion}}` | Consulta de la SIA productiva, con formato `dd/MM/yyyy` |
| `{{termino_de_desmovilizacion}}` | Consulta de la SIA productiva, con formato `dd/MM/yyyy` |
| `{{liberacion_area}}` | Consulta de la SIA productiva |
| `{{uso_permanente}}` | Consulta de la SIA productiva |

Mantenga `id_sias` como texto para conservar los ceros iniciales. El vínculo del botón se construye así:

```text
concat(
  'https://sig.aminerals.cl/portal/apps/dashboards/acc30601d35040169bacad8938c3e5e2#p1=',
  variables('id_sias')
)
```
