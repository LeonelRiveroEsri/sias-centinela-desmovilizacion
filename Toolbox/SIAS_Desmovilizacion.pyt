# -*- coding: utf-8 -*-
"""Toolbox ArcGIS Pro para detectar SIAs próximas a vencer (desmovilización).

Reutiliza la lógica de consulta y de estados definida en Notebook/001.ipynb.
"""
import json
import os
import re

import arcpy
import requests

TOOLBOX_DIR = os.path.dirname(os.path.abspath(__file__))
PLANTILLA_CORREO_PATH = os.path.join(
    os.path.dirname(TOOLBOX_DIR),
    "power-automate",
    "correo-aprobacion-desmovilizacion.html",
)

URL_AUTOMATED_CORREO = (
    "https://defaultd96f3d5a3042402a994b05725b2e14.27.environment.api.powerplatform.com:443/"
    "powerautomate/automations/direct/cu/16/workflows/dbfde91a57c240f78e85aff0a1a4a64d/"
    "triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0"
    "&sig=W9sWnMlbZi3cQBNaV4RGLQXf7bOCU4hcJm3jne7_0Do"
)

CORREO_TIMEOUT = 60


def _formatear_fecha(valor):
    import pandas as pd

    fecha = pd.to_datetime(valor, errors="coerce")
    if pd.isna(fecha):
        return "No informado"
    return fecha.strftime("%d-%m-%Y")


def _valor_o_default(valor, default="No informado"):
    if valor is None:
        return default
    texto = str(valor).strip()
    return texto if texto and texto.lower() != "nan" else default


def renderizar_correo(plantilla_html, registro):
    """Reemplaza los tokens {{campo}} de la plantilla con los valores del registro."""
    valores = {
        "id_sias": _valor_o_default(registro.get("id_sias")),
        "empresa": _valor_o_default(registro.get("empresa")),
        "nomb_area": _valor_o_default(registro.get("nomb_area")),
        "nomb_contrato": _valor_o_default(registro.get("nomb_contrato")),
        "nombre_gerencia_responsable": _valor_o_default(registro.get("nombre_gerencia_responsable")),
        "termino_de_ejecucion": _formatear_fecha(registro.get("termino_de_ejecucion")),
        "termino_de_desmovilizacion": _formatear_fecha(registro.get("termino_de_desmovilizacion")),
        "liberacion_area": _valor_o_default(registro.get("liberacion_area")),
        "uso_permanente": _valor_o_default(registro.get("uso_permanente")),
        "obs_desmovilizacion": _valor_o_default(
            registro.get("obs_desmovilizacion"),
            "Debe iniciar el proceso de desmovilización dentro de los plazos establecidos.",
        ),
    }

    def reemplazar(match):
        clave = match.group(1)
        return valores.get(clave, "No informado")

    return re.sub(r"{{\s*(\w+)\s*}}", reemplazar, plantilla_html)


def enviar_correo_automatizado(url_automated, mail, asunto, cuerpo_html, messages):
    payload = {"mail": mail, "body": cuerpo_html, "asunto": asunto}
    try:
        response = requests.post(
            url_automated,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=CORREO_TIMEOUT,
        )
    except requests.exceptions.RequestException as error:
        messages.addWarningMessage(f"Error enviando correo a {mail}: {error}")
        return False

    if response.status_code in (200, 202):
        messages.addMessage(f"Correo enviado a {mail} (HTTP {response.status_code}).")
        return True

    messages.addWarningMessage(
        f"Power Automate respondió con error al notificar a {mail}. "
        f"Status={response.status_code}, Body={response.text}"
    )
    return False


class Toolbox(object):
    def __init__(self):
        self.label = "SIAS Desmovilizacion"
        self.alias = "siasdesmovilizacion"
        self.tools = [SIAsPorVencer]


class SIAsPorVencer(object):
    ITEM_PRODUCTIVO_ID = "d0bf25b15c7f45f8b85deed166cd2046"
    ESTADO_APROBADA = 2

    def __init__(self):
        self.label = "SIAs próximas a vencer"
        self.description = (
            "Consulta el ítem productivo de SIAS en ArcGIS Enterprise y "
            "detecta las SIAs aprobadas (estado = 2) cuyo termino_de_ejecucion "
            "ya se cumplió, replicando el criterio usado en la lista Arcade del "
            "dashboard (arcade/arcade.js). Retorna un JSON sin geometría con "
            "los registros a desmovilizar."
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        portal_url = arcpy.Parameter(
            displayName="URL del portal",
            name="portal_url",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        portal_url.value = "https://sig.aminerals.cl/portal/"

        usuario = arcpy.Parameter(
            displayName="Usuario",
            name="usuario",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        usuario.value = "admcenop"

        password = arcpy.Parameter(
            displayName="Contraseña",
            name="password",
            datatype="GPStringHidden",
            parameterType="Optional",
            direction="Input",
        )
        password.description = (
            "Si se deja vacío, se usa la variable de entorno ARCGIS_PASSWORD."
        )

        dias_maximo_atraso = arcpy.Parameter(
            displayName="Días máximos de atraso a incluir (0 = sin límite)",
            name="dias_maximo_atraso",
            datatype="GPLong",
            parameterType="Required",
            direction="Input",
        )
        dias_maximo_atraso.value = 0

        solo_top3 = arcpy.Parameter(
            displayName="Retornar solo el top 3 con más días de atraso",
            name="solo_top3",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input",
        )
        solo_top3.value = False

        enviar_correo = arcpy.Parameter(
            displayName="Enviar correo de aviso por cada SIA a vencer",
            name="enviar_correo",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input",
        )
        enviar_correo.value = False

        url_automated = arcpy.Parameter(
            displayName="URL del endpoint automatizado (Power Automate)",
            name="url_automated",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        url_automated.value = URL_AUTOMATED_CORREO

        salida_json = arcpy.Parameter(
            displayName="Archivo JSON de salida",
            name="salida_json",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output",
        )
        salida_json.filter.list = ["json"]

        resultado_json = arcpy.Parameter(
            displayName="Resultado JSON",
            name="resultado_json",
            datatype="GPString",
            parameterType="Derived",
            direction="Output",
        )

        return [
            portal_url,
            usuario,
            password,
            dias_maximo_atraso,
            solo_top3,
            enviar_correo,
            url_automated,
            salida_json,
            resultado_json,
        ]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        import pandas as pd
        from arcgis.gis import GIS

        portal_url = parameters[0].valueAsText
        usuario = parameters[1].valueAsText
        password = parameters[2].valueAsText or os.getenv("ARCGIS_PASSWORD")
        dias_maximo_atraso = int(parameters[3].value)
        solo_top3 = bool(parameters[4].value)
        enviar_correo = bool(parameters[5].value)
        url_automated = parameters[6].valueAsText or URL_AUTOMATED_CORREO
        salida_json = parameters[7].valueAsText

        if not password:
            raise arcpy.ExecuteError(
                "Debe indicar una contraseña o definir la variable de entorno "
                "ARCGIS_PASSWORD."
            )

        messages.addMessage(f"Conectando a {portal_url} como {usuario}...")
        gis = GIS(portal_url, usuario, password)

        item_productivo = gis.content.get(self.ITEM_PRODUCTIVO_ID)
        if item_productivo is None:
            raise arcpy.ExecuteError(
                f"No se encontró el ítem productivo {self.ITEM_PRODUCTIVO_ID}"
            )
        if not item_productivo.layers:
            raise arcpy.ExecuteError("El ítem productivo no contiene capas consultables")

        capa_sias = item_productivo.layers[0]
        resultado = capa_sias.query(
            where="estado = 2 AND termino_de_ejecucion IS NOT NULL",
            out_fields="*",
            return_geometry=False,
        )
        df_sias = resultado.sdf.copy()

        df_sias["estado"] = pd.to_numeric(df_sias["estado"], errors="coerce")
        df_sias["termino_de_ejecucion"] = pd.to_datetime(
            df_sias["termino_de_ejecucion"], errors="coerce"
        )

        hoy = pd.Timestamp.now().normalize()

        # Igual que Filter(vista, ...) + "if (finEjecucion > hoy) continue;" en arcade/arcade.js:
        # solo se consideran SIAs cuya ejecución ya terminó (sin límite superior).
        ejecucion_terminada = df_sias["termino_de_ejecucion"].dt.normalize().le(hoy)

        df_por_vencer = (
            df_sias.loc[ejecucion_terminada]
            .copy()
            .sort_values(["termino_de_ejecucion", "id_sias"])
        )
        df_por_vencer["dias_desde_termino"] = (
            hoy - df_por_vencer["termino_de_ejecucion"].dt.normalize()
        ).dt.days

        if dias_maximo_atraso > 0:
            df_por_vencer = df_por_vencer.loc[
                df_por_vencer["dias_desde_termino"] <= dias_maximo_atraso
            ]

        if solo_top3:
            df_por_vencer = df_por_vencer.head(3)

        messages.addMessage(
            f"SIAs aprobadas con ejecución terminada: {len(df_por_vencer):,}"
        )

        if enviar_correo and not df_por_vencer.empty:
            with open(PLANTILLA_CORREO_PATH, "r", encoding="utf-8") as archivo_plantilla:
                plantilla_html = archivo_plantilla.read()

            enviados = 0
            fallidos = 0
            for registro in df_por_vencer.to_dict("records"):
                mail = _valor_o_default(registro.get("email"), "")
                if not mail:
                    messages.addWarningMessage(
                        f"SIA {registro.get('id_sias')} no tiene email informado; no se envía aviso."
                    )
                    fallidos += 1
                    continue

                asunto = f"Aviso de desmovilización pendiente – SIA {registro.get('id_sias')}"
                cuerpo_html = renderizar_correo(plantilla_html, registro)

                if enviar_correo_automatizado(url_automated, mail, asunto, cuerpo_html, messages):
                    enviados += 1
                else:
                    fallidos += 1

            messages.addMessage(
                f"Avisos de desmovilización: {enviados} enviados, {fallidos} no enviados."
            )

        registros = json.loads(df_por_vencer.to_json(orient="records", date_format="iso"))
        salida = {
            "fecha_evaluacion": hoy.strftime("%Y-%m-%d"),
            "dias_maximo_atraso": dias_maximo_atraso,
            "solo_top3": solo_top3,
            "total_registros": len(registros),
            "registros": registros,
        }
        salida_texto = json.dumps(salida, ensure_ascii=False, indent=2)

        if salida_json:
            with open(salida_json, "w", encoding="utf-8") as archivo:
                archivo.write(salida_texto)
            messages.addMessage(f"JSON guardado en {salida_json}")

        parameters[8].value = salida_texto
