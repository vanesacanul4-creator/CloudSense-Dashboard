# C.L.O.U.D. Sense · Dashboard (Streamlit)

## Correrlo en tu Debian
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    streamlit run app.py

## Opciones del tablero (menú lateral)
- **Guía de lectura en cada gráfica:** explica cómo leer cada gráfica (activada por defecto).
- **Vista previa de diseño:** llena el tablero con datos de ejemplo SOLO para revisar el diseño o tomar capturas de prueba. Muestra una franja naranja "Datos de ejemplo" en todas las páginas. Para la entrega, déjala apagada.

## Cargar los datos de las pruebas (lunes)
1. Abre `data/Plantilla_CloudSense.xlsx` y llena las hojas desde la fila 2 (no cambies los encabezados).
2. Guarda y recarga el dashboard. Las hojas vacías muestran "Esperando datos"; nunca se inventan datos.
   - Lecturas_Bascula → predicción de agotamiento (R2)
   - Tanques + Reabastecimientos → R1
   - Fugas → R3 y R4
   - Pruebas → los 30 ensayos (escenarios A, B, C)
3. Alternativa rápida: sube el Excel desde el menú lateral (solo vale en esa sesión).

## Sensores MQ con turno y semestre (data warehouse)
    pip install psycopg2-binary
    python exportar_dw.py        # genera data/lecturas_dw.csv desde dw_cloud_sense

## Publicar (enlace para el profe)
1. Sube la carpeta a un repositorio de GitHub (si es público, revisa que el Excel no tenga datos personales).
2. En share.streamlit.io: New app → tu repo → `app.py` → Deploy. El enlace queda abierto sin pedir permisos.
3. Para actualizar datos: reemplaza el Excel en el repositorio y la app se actualiza.

## Datos en vivo desde la base de la app (U3A4)
El tablero lee la base `cloudsense` de la app (tanques, ubicaciones, lecturas, alertas) por medio de cuatro vistas de solo lectura del esquema `dash`.
1. En el servidor: `sudo -u postgres psql -d cloudsense < 02_vistas_dashboard.sql` (carpeta `sql/`). No modifica datos de la app.
2. En Streamlit Cloud → Settings → Secrets, agrega un bloque `[connections.app]` igual a `[connections.postgresql]` pero con `database = "cloudsense"`.
3. Un tanque o alerta nuevos en la app aparecen en los mapas en menos de 30 s (o con el botón "Actualizar ahora" del menú lateral).
4. Si la base no responde, el tablero usa el Excel como respaldo. Los ids de la app llevan el prefijo `APP-`.
