# TERRA ALERT
Enlace del host: Chla.pythonanywhere.com

**TERRA ALERT** es una aplicación web de visualización y análisis de desastres naturales. Permite explorar registros históricos, consultar información geográfica y comparar la evolución de distintos tipos de desastre y países.

El proyecto está desarrollado con **Python, Flask, HTML, CSS, JavaScript y Matplotlib**, y utiliza datos del conjunto **EM-DAT**.

## Características

- Panel principal con indicadores generales.
- Exploración de eventos y consulta de información por país.
- Gráficos temporales para comparar varios tipos de desastre o países.
- Rankings por frecuencia, fallecimientos y personas afectadas.
- Comparación geográfica por región o país.
- Filtros por periodo, indicador, país y tipo de desastre.
- Interpretaciones dinámicas que acompañan los gráficos seleccionados.
- Interfaz adaptable con una estética visual oscura inspirada en el espacio.

## Tecnologías

| Tecnología | Uso |
|---|---|
| Python | Lógica del servidor y procesamiento de datos |
| Flask | Aplicación web y rutas/API |
| Pandas / procesamiento CSV | Lectura y preparación de los datos |
| Matplotlib | Generación de gráficos en el servidor |
| HTML y Jinja | Estructura y plantillas |
| CSS | Diseño visual y adaptación a pantallas |
| JavaScript | Filtros e interacción con los gráficos |

## Estructura del proyecto

```text
demo_flask/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── emdat_disasters.csv
├── services/
│   ├── analysis_service.py
│   ├── data_service.py
│   ├── geography_service.py
│   └── graph_service.py
├── static/
│   ├── js/
│   │   ├── analysis.js
│   │   ├── events.js
│   │   └── globe.js
│   └── styles.css
└── templates/
    ├── analysis.html
    ├── base.html
    ├── dashboard.html
    └── events.html
```

## Secciones de la aplicación

### 1. Inicio

Presenta una visión general mediante indicadores y elementos visuales que resumen los datos disponibles.

### 2. Análisis

La página de análisis está organizada en cuatro bloques complementarios:

1. **Evolución temporal:** compara hasta cinco tipos de desastre a lo largo de un periodo seleccionado. Permite elegir el indicador.
2. **Frecuencia e impacto:** muestra un ranking de categorías mediante barras horizontales.
3. **Distribución geográfica:** permite comparar regiones o países y visualizar la evolución temporal de hasta ocho países seleccionados.
4. **Exploración de un país:** muestra la evolución anual y el desglose por tipo de desastre para el país, periodo e indicador elegidos.

Los gráficos se generan en el servidor con Matplotlib. JavaScript actualiza los filtros y solicita las imágenes y las interpretaciones correspondientes.

### 3. Eventos

Permite explorar los eventos registrados y consultar los datos disponibles mediante los controles de la página.

## Análisis y metodología

Los indicadores disponibles en la sección de análisis son:

- **Registros:** número de registros de desastres incluidos en el conjunto de datos.
- **Fallecimientos:** suma de los fallecimientos reportados.
- **Personas afectadas:** suma de las personas afectadas reportadas.

**Importante:** los valores ausentes de fallecimientos o personas afectadas no se consideran cero. Cuando no hay datos reportados para un periodo, la serie puede mostrar un espacio sin valor en lugar de representar un cero. Por tanto, los totales reflejan únicamente la información reportada en EM-DAT y no necesariamente el impacto completo de todos los desastres ocurridos.

El indicador de daños económicos no se incluye en los gráficos principales debido a la cobertura insuficiente de ese campo en el archivo utilizado.

La clasificación regional sigue los valores de la columna `Region` del conjunto EM-DAT. En estos datos, `Americas` aparece como una única región.

## Rutas principales

| Ruta | Descripción |
|---|---|
| `/` | Página de inicio |
| `/analisis` | Página de análisis |
| `/eventos` | Página de eventos |
| `/api/countries` | Lista de países disponibles |
| `/api/country/<iso>` | Estadísticas de un país por código ISO |
| `/api/latest-events` | Eventos recientes |
| `/api/geography` | Opciones geográficas |
| `/api/analysis/options` | Opciones para los filtros de análisis |
| `/api/analysis/insight` | Interpretación calculada según los filtros |

Las rutas de gráficos bajo `/api/analysis/` devuelven imágenes PNG generadas con Matplotlib.

## Limitaciones

- El gran volumen de datos (20 MB y aproximadamente 17.888 registros) puede ralentizar la carga y el procesamiento de la aplicación.
- La generación de gráficos puede tardar unos segundos al cambiar los filtros.
- Algunos registros no contienen datos sobre fallecimientos o personas afectadas.
- Los daños económicos no se incluyen debido a la falta de información suficiente.
- La aplicación utiliza datos estáticos de EM-DAT y no ofrece información en tiempo real.
- Las comparaciones están limitadas a 5 tipos de desastres y 8 países simultáneamente.
- Los resultados son descriptivos y no permiten predecir futuros desastres.

---

**TERRA ALERT — Visualización y análisis de desastres naturales.**
