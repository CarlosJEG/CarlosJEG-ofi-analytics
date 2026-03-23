# Dashboard de Seguimiento

Aplicacion en Streamlit para limpiar `datos.csv` o `datos.xlsx` y visualizar KPIs operacionales y temporales.

## Repo minimo

El repositorio debe contener solo codigo y configuracion:

- `app.py`
- `dashboard/`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `README.md`

No subas al repo:

- `.env`
- `.venv/`
- `datos.csv`
- `datos.xlsx`
- cualquier otro archivo con datos reales

## Puesta en marcha local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Configuracion

La aplicacion lee variables desde `.env`.

- `DATA_FILE`: ruta del archivo fuente, opcional si cargaras el archivo manualmente
- `DATA_FORMAT`: `csv` o `xlsx`
- `APP_TITLE`: titulo del dashboard

Si `DATA_FILE` no esta configurado, la app permite subir el archivo desde la barra lateral.

## KPIs incluidos

- Casos cerrados y pendientes: cantidad y porcentaje
- Tipo de organismo: cantidad y porcentaje
- Juzgado / Liquidador: cantidad y porcentaje
- Tipo: cantidad y porcentaje
- Responsable: cantidad y porcentaje
- Cantidad diaria y mensual por fecha de recepcion
- Promedio diario y mensual de ingresos
- Fecha de recepcion vs fecha de vencimiento
- Fecha de recepcion vs fecha de respuesta

## Reglas de limpieza

- Se usa `datos.csv` como fuente principal
- Las fechas seriales de Excel se convierten a `datetime`
- Fechas fuera de rango de negocio se convierten a nulo
- Campos vacios de clasificacion se reemplazan por etiquetas visibles
- Si faltan columnas obligatorias, la app muestra un error claro

## Deploy en Streamlit Community Cloud

1. Sube este proyecto a GitHub sin los datos reales.
2. En Streamlit Community Cloud crea una app apuntando a `app.py`.
3. En `Advanced settings` define variables de entorno si usaras `DATA_FILE`.
4. Si no tendras un archivo persistente en el servidor, usa la carga manual desde la barra lateral.
5. Verifica que la app cargue, que los filtros funcionen y que los totales coincidan con tu validacion local.

## Datos a tener en cuenta para produccion

- El dataset contiene campos sensibles como nombre y RUT.
- Si la app sera interna, evita publicar archivos reales en GitHub o enlaces publicos.
- Define quien actualiza el archivo y con que frecuencia.
- Valida siempre estructura de columnas antes de reemplazar el dataset en produccion.
