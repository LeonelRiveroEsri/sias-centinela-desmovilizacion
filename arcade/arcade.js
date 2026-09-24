// ArcGIS Dashboards - Expresion de datos para SIAs en desmovilizacion
// Vista: d0bf25b15c7f45f8b85deed166cd2046 (capa 0)
//
// Uso:
// 1. Cree un elemento Lista en ArcGIS Dashboards.
// 2. Seleccione "Expresion de datos" y pegue este archivo completo.
// 3. En la plantilla de la lista use el campo {html}.
//
// La expresion es de solo lectura. No incluye riesgo ambiental ni magnitud.

var PORTAL_URL = "https://sig.aminerals.cl/portal";
var ITEM_VISTA_ID = "d0bf25b15c7f45f8b85deed166cd2046";
var CAPA_ID = 0;

var portal = Portal(PORTAL_URL);
var campos = [
  "objectid",
  "id_sias",
  "empresa",
  "nomb_area",
  "nomb_contrato",
  "nombre_gerencia_responsable",
  "estado",
  "inicio_de_ejecucion",
  "termino_de_ejecucion",
  "termino_de_desmovilizacion",
  "termino_de_contrato",
  "url_sharepoint",
];

var vista = FeatureSetByPortalItem(
  portal,
  ITEM_VISTA_ID,
  CAPA_ID,
  campos,
  false,
);

// Primero se filtra en el servidor. La fecha se evalua en Arcade para evitar
// diferencias de sintaxis SQL entre ArcGIS Enterprise y ArcGIS Online.
var aprobadas = Filter(
  vista,
  "estado = 2 AND termino_de_ejecucion IS NOT NULL",
);
var ordenadas = OrderBy(aprobadas, "termino_de_ejecucion ASC, id_sias ASC");

function TextoSeguro(valor, reemplazo) {
  if (IsEmpty(valor)) {
    return reemplazo;
  }

  var salida = Text(valor);
  salida = Replace(salida, "&", "&amp;");
  salida = Replace(salida, "<", "&lt;");
  salida = Replace(salida, ">", "&gt;");
  salida = Replace(salida, '"', "&quot;");
  salida = Replace(salida, "'", "&#39;");
  return salida;
}

function FechaCorta(fecha) {
  if (IsEmpty(fecha)) {
    return "Sin fecha";
  }
  return Text(fecha, "DD/MM/YYYY");
}

var hoy = Now();
var entidades = [];
var oidSalida = 0;

for (var sia in ordenadas) {
  var finEjecucion = sia["termino_de_ejecucion"];

  // Solo se muestran SIAs cuya ejecucion ya termino.
  if (finEjecucion > hoy) {
    continue;
  }

  oidSalida += 1;

  var finDesmovilizacion = sia["termino_de_desmovilizacion"];
  var diasDesdeTermino = Floor(DateDiff(hoy, finEjecucion, "days"));
  var diasAtraso = 0;
  var situacion = "Sin fecha de desmovilizacion";
  var color = "#64748b";
  var fondo = "#f1f5f9";

  if (!IsEmpty(finDesmovilizacion)) {
    diasAtraso = Floor(DateDiff(hoy, finDesmovilizacion, "days"));
    if (diasAtraso >= 0) {
      situacion = "Desmovilizacion vencida";
      color = "#b42318";
      fondo = "#fef3f2";
    } else {
      situacion = "Desmovilizacion programada";
      color = "#175cd3";
      fondo = "#eff8ff";
      diasAtraso = 0;
    }
  }

  var idSia = TextoSeguro(sia["id_sias"], "Sin ID");
  var empresa = TextoSeguro(sia["empresa"], "Empresa no informada");
  var area = TextoSeguro(sia["nomb_area"], "Area no informada");
  var contrato = TextoSeguro(sia["nomb_contrato"], "Sin contrato informado");
  var responsable = TextoSeguro(
    sia["nombre_gerencia_responsable"],
    "Responsable no informado",
  );
  var url = TextoSeguro(sia["url_sharepoint"], "");

  var enlace = "";
  if (!IsEmpty(url)) {
    enlace = Concatenate([
      '<a href="',
      url,
      '" target="_blank" rel="noopener noreferrer" ',
      'style="display:inline-block;margin-top:12px;padding:8px 12px;',
      "border-radius:6px;background:#0f4c81;color:#ffffff;",
      'font-size:12px;font-weight:600;text-decoration:none;">',
      "Abrir expediente</a>",
    ]);
  }

  var html = Concatenate([
    '<div style="font-family:Arial,sans-serif;background:#ffffff;',
    "border:1px solid #e2e8f0;border-left:5px solid ",
    color,
    ";",
    "border-radius:8px;padding:14px 16px;margin:5px 2px;",
    'box-shadow:0 2px 7px rgba(15,23,42,0.08);">',

    '<div style="display:flex;justify-content:space-between;',
    'align-items:flex-start;gap:12px;">',
    '<div><div style="font-size:11px;color:#64748b;font-weight:700;',
    'letter-spacing:.08em;text-transform:uppercase;">SIA</div>',
    '<div style="font-size:20px;color:#0f172a;font-weight:700;">',
    idSia,
    "</div></div>",
    '<span style="padding:5px 9px;border-radius:999px;background:',
    fondo,
    ";color:",
    color,
    ';font-size:11px;font-weight:700;">',
    situacion,
    "</span></div>",

    '<div style="margin-top:10px;font-size:14px;color:#1e293b;',
    'font-weight:700;">',
    area,
    "</div>",
    '<div style="margin-top:3px;font-size:12px;color:#475569;">',
    empresa,
    " &middot; ",
    contrato,
    "</div>",

    '<div style="display:grid;grid-template-columns:repeat(3,1fr);',
    'gap:8px;margin-top:13px;">',
    '<div style="background:#f8fafc;border-radius:6px;padding:8px;">',
    '<div style="font-size:10px;color:#64748b;">FIN EJECUCION</div>',
    '<div style="font-size:12px;color:#0f172a;font-weight:700;">',
    FechaCorta(finEjecucion),
    "</div></div>",
    '<div style="background:#f8fafc;border-radius:6px;padding:8px;">',
    '<div style="font-size:10px;color:#64748b;">FIN DESMOV.</div>',
    '<div style="font-size:12px;color:#0f172a;font-weight:700;">',
    FechaCorta(finDesmovilizacion),
    "</div></div>",
    '<div style="background:#f8fafc;border-radius:6px;padding:8px;">',
    '<div style="font-size:10px;color:#64748b;">DIAS DESDE TERMINO</div>',
    '<div style="font-size:12px;color:#0f172a;font-weight:700;">',
    Text(diasDesdeTermino, "#,###"),
    "</div></div></div>",

    '<div style="margin-top:10px;font-size:11px;color:#64748b;">',
    "<strong>Responsable:</strong> ",
    responsable,
    " &nbsp;|&nbsp; <strong>Fin contrato:</strong> ",
    FechaCorta(sia["termino_de_contrato"]),
    "</div>",
    enlace,
    "</div>",
  ]);

  Push(entidades, {
    attributes: {
      objectid: oidSalida,
      id_sias: Text(sia["id_sias"]),
      empresa: Text(sia["empresa"]),
      nomb_area: Text(sia["nomb_area"]),
      nomb_contrato: Text(sia["nomb_contrato"]),
      responsable: Text(sia["nombre_gerencia_responsable"]),
      termino_ejecucion: finEjecucion,
      termino_desmovilizacion: finDesmovilizacion,
      termino_contrato: sia["termino_de_contrato"],
      dias_desde_termino: diasDesdeTermino,
      dias_atraso: diasAtraso,
      situacion: situacion,
      url_sharepoint: Text(sia["url_sharepoint"]),
      html: html,
    },
  });
}

var resultado = {
  fields: [
    { name: "objectid", alias: "ObjectID", type: "esriFieldTypeOID" },
    { name: "id_sias", alias: "ID SIA", type: "esriFieldTypeString" },
    { name: "empresa", alias: "Empresa", type: "esriFieldTypeString" },
    { name: "nomb_area", alias: "Area", type: "esriFieldTypeString" },
    { name: "nomb_contrato", alias: "Contrato", type: "esriFieldTypeString" },
    { name: "responsable", alias: "Responsable", type: "esriFieldTypeString" },
    {
      name: "termino_ejecucion",
      alias: "Fin de ejecucion",
      type: "esriFieldTypeDate",
    },
    {
      name: "termino_desmovilizacion",
      alias: "Fin de desmovilizacion",
      type: "esriFieldTypeDate",
    },
    {
      name: "termino_contrato",
      alias: "Fin de contrato",
      type: "esriFieldTypeDate",
    },
    {
      name: "dias_desde_termino",
      alias: "Dias desde termino",
      type: "esriFieldTypeInteger",
    },
    {
      name: "dias_atraso",
      alias: "Dias de atraso",
      type: "esriFieldTypeInteger",
    },
    { name: "situacion", alias: "Situacion", type: "esriFieldTypeString" },
    {
      name: "url_sharepoint",
      alias: "Expediente",
      type: "esriFieldTypeString",
    },
    {
      name: "html",
      alias: "Tarjeta HTML",
      type: "esriFieldTypeString",
      length: 8000,
    },
  ],
  geometryType: "",
  features: entidades,
};

return FeatureSet(Text(resultado));
