"""C.L.O.U.D. Sense - Tablero de control interactivo (Streamlit).
Datos reales: data/lecturas_mq.csv (ETL) y data/Plantilla_CloudSense.xlsx (pruebas). Nunca se inventan datos;
la 'vista previa de diseño' es opcional, está apagada por defecto y siempre se rotula como datos de ejemplo."""
from pathlib import Path
import numpy as np, pandas as pd, plotly.express as px, plotly.graph_objects as go, streamlit as st
px.defaults.template = 'plotly_dark'

BASE = Path(__file__).parent
ASSETS, DATA = BASE / "assets", BASE / "data"
CYAN, BLUE, ORANGE, RED, YEL, GRN, NAVY = "#22D3EE", "#2F7DE1", "#FF8A1F", "#EF4444", "#FACC15", "#22C55E", "#0B2A55"
px.defaults.color_discrete_sequence = ["#22D3EE", "#FF8A1F", "#2F7DE1", "#FACC15", "#22C55E", "#EF4444"]
ESTADO_COL = {"Crítico": RED, "Atención": YEL, "Normal": GRN, "Sin consumo": "#94A3B8"}
st.set_page_config(page_title="C.L.O.U.D. Sense", page_icon=str(ASSETS / "icono.png"), layout="wide", initial_sidebar_state="auto")
st.logo(str(ASSETS / "logo_horizontal.png"), icon_image=str(ASSETS / "icono.png"), size="large")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
html,body,p,label,li,td,th,input,textarea,a{font-family:'Poppins',sans-serif}
h1,h2,h3,h4,h5{font-family:'Poppins',sans-serif!important}
.sec,.eap,.card,.eap *,.card *{font-family:'Poppins',sans-serif}
.block-container{padding-top:2.6rem;padding-bottom:2rem;max-width:1500px}
[data-testid="stToolbarActions"],[data-testid="stAppDeployButton"],[data-testid="stMainMenu"],[data-testid="stDecoration"],footer,[data-testid="stSidebarResizeHandle"]{display:none!important}
header[data-testid="stHeader"]{background:transparent}
[data-testid="stExpandSidebarButton"]{background:#0E2547;border:1px solid #22D3EE;border-radius:10px;color:#22D3EE}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0A1F40,#07142B);border-right:1px solid #16345F}
a[data-testid="stSidebarNavLink"]{background:#0E2547;border:1px solid #16345F;border-radius:12px;padding:.75rem .7rem;margin-bottom:.45rem;transition:all .15s}
a[data-testid="stSidebarNavLink"] span{font-size:.86rem}
a[data-testid="stSidebarNavLink"]:hover{border-color:#22D3EE;transform:translateX(3px)}
a[data-testid="stSidebarNavLink"][aria-current="page"]{background:linear-gradient(90deg,#1456B8,#22D3EE);border-color:#22D3EE;box-shadow:0 4px 14px rgba(34,211,238,.25)}
a[data-testid="stSidebarNavLink"][aria-current="page"] span{color:#fff!important;font-weight:600}
.hdr{background:linear-gradient(100deg,#0B2A55 0%,#1456B8 65%,#22D3EE 120%);border-radius:16px;padding:20px 28px;margin-bottom:18px;border-bottom:3px solid #FF8A1F}
.hdr .tag{font-size:.72rem;letter-spacing:.22em;color:#9FE8F7;font-weight:500}
.hdr h1{margin:2px 0 2px;font-size:2rem;color:#fff;font-weight:700;padding:0}.hdr p{margin:0;color:#D6F6FF;font-size:1rem}
.demo{background:#FF8A1F;color:#07142B;font-weight:600;border-radius:8px;padding:6px 14px;margin-bottom:12px;text-align:center;font-size:.85rem}
.card{background:#0E2547;border-left:5px solid #22D3EE;border-radius:12px;padding:14px 18px;margin-bottom:10px}
.card b.t{color:#22D3EE}.sec{font-size:1.15rem;font-weight:600;margin:18px 0 6px;color:#E6F1FF}
.sec span{display:inline-block;width:6px;height:18px;background:#FF8A1F;border-radius:3px;margin-right:10px;vertical-align:-3px}
.eap{background:#0E2547;border:1px solid #16345F;border-radius:14px;padding:6px 18px;margin-top:14px}
.eap div{padding:8px 0;border-bottom:1px solid #16345F}.eap div:last-child{border:0}.eap b{color:#22D3EE;display:inline-block;min-width:92px}
[data-testid="stMetric"]{background:#0E2547;border:1px solid #16345F!important;border-radius:14px;padding:12px 16px}
[data-testid="stMetricValue"]{color:#22D3EE}
div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:14px}
.step{width:34px;height:34px;border-radius:50%;background:#FF8A1F;color:#07142B;font-weight:700;display:flex;align-items:center;justify-content:center;margin-bottom:6px}
</style>""", unsafe_allow_html=True)

# ------------------------------------------------------------------ datos
SHEETS = {"Tanques": ["id_tanque", "tipo", "capacidad_kg", "cliente", "tipo_cliente", "zona", "estado", "municipio", "latitud", "longitud"],
          "Reabastecimientos": ["id_recarga", "id_tanque", "fecha", "kg_cargados", "nivel_antes_pct", "nivel_despues_pct", "precio_kg", "monto", "dias_desde_ultima_recarga", "proveedor"],
          "Lecturas_Bascula": ["id_tanque", "fecha_hora", "peso_kg", "nivel_pct"],
          "Fugas": ["id_alerta", "id_tanque", "fecha_hora", "nivel_mq6", "caida_peso_pct", "duracion_min", "kg_perdidos_estimados", "tiempo_respuesta_min", "atendida", "gravedad", "origen"],
          "Pruebas": ["id_ensayo", "escenario", "concentracion_ppm", "tiempo_respuesta_s", "latencia_notificacion_s", "voltaje_sensor_v", "rssi_wifi_dbm", "alarma_activada"]}
MQ = ["mq2", "mq3", "mq5", "mq6", "mq7", "mq8", "mq135"]

def _fechas(out):
    for s, c in [("Reabastecimientos", "fecha"), ("Lecturas_Bascula", "fecha_hora"), ("Fugas", "fecha_hora")]:
        out[s][c] = pd.to_datetime(out[s][c], errors="coerce")
    return out

@st.cache_data(show_spinner=False)
def load_excel(src):
    out, info = {}, []
    for s_, cols in SHEETS.items():
        try:
            raw = pd.read_excel(src, sheet_name=s_)
            falt = [c for c in cols if c not in raw.columns]
            df = raw.reindex(columns=cols).dropna(how="all").reset_index(drop=True)
            estado = "Faltan columnas: " + ", ".join(falt) if falt else ("Vacía" if df.empty else "Cargada")
        except Exception:
            df, estado = pd.DataFrame(columns=cols), "Hoja no encontrada"
        out[s_] = df; info.append({"Hoja": s_, "Filas": len(df), "Estado": estado})
    return _fechas(out), info

@st.cache_data(show_spinner=False)
def make_demo():
    """SOLO para revisar el diseño. Datos de ejemplo, no son resultados del proyecto."""
    rng = np.random.default_rng(7); hoy = pd.Timestamp.now().normalize()
    zonas = {"Norte": (21.165, -88.15), "Centro": (21.143, -88.15), "Sur": (21.12, -88.15), "Oriente": (21.14, -88.12)}
    tipos = ["Doméstico", "Comercial", "Industrial"]; capv = {"Doméstico": 30, "Comercial": 100, "Industrial": 300}
    tq, lect, rec = [], [], []
    for i in range(12):
        z = list(zonas)[i % 4]; tp = tipos[i % 3]; cap = capv[tp]; la, lo = zonas[z]
        tid = f"T{i+1:02d}"
        tq.append([tid, "cilindro" if tp == "Doméstico" else "estacionario", cap, f"Cliente {i+1:02d}", tp, z, "Yucatán", "Tizimín", la + rng.normal(0, .006), lo + rng.normal(0, .006)])
        cons = cap * rng.uniform(.015, .06); peso = cap * rng.uniform(.3, .9); last = hoy - pd.Timedelta(days=120)
        for d in range(120, -1, -1):
            f = hoy - pd.Timedelta(days=d); peso -= cons * rng.uniform(.8, 1.2)
            if peso < cap * .12 and d > 4:
                kg = cap * .95 - peso; rec.append([f"R{len(rec)+1:03d}", tid, f, round(kg, 1), round(peso / cap * 100, 1), 95, round(rng.normal(19.5, .5), 2), 0, (f - last).days, "Planta Tizimín"])
                rec[-1][7] = round(rec[-1][3] * rec[-1][6], 2); last = f; peso = cap * .95
            lect.append([tid, f + pd.Timedelta(hours=8), round(peso, 1), round(peso / cap * 100, 1)])
    fu = []
    for k in range(14):
        n = int(rng.integers(500, 900)); fu.append([f"F{k+1:02d}", f"T{int(rng.integers(1,13)):02d}", hoy - pd.Timedelta(days=int(rng.integers(1, 120)), hours=int(rng.integers(0, 20))), n, round(rng.uniform(1, 9), 1),
                                                  int(rng.integers(3, 25)), round(rng.uniform(.1, 2), 2), int(rng.integers(5, 60)), 0 if k in (2, 9, 12) else 1, "Alta" if n > 750 else ("Media" if n > 620 else "Leve"), "Sensor MQ-6" if k % 3 else "Caída de peso"])
    pr = []
    for e, base in zip("ABC", (3.0, 4.2, 5.5)):
        for j in range(10):
            ppm = 200 + 80 * j; pr.append([len(pr) + 1, e, ppm, round(base + rng.normal(0, .5) - ppm / 1500, 2), round(rng.uniform(1.2, 3.5), 2), round(rng.uniform(2.4, 3.3), 2), int(rng.integers(-75, -50)), 1 if rng.random() > .05 else 0])
    mk = lambda r, s: pd.DataFrame(r, columns=SHEETS[s])
    return _fechas({"Tanques": mk(tq, "Tanques"), "Reabastecimientos": mk(rec, "Reabastecimientos"), "Lecturas_Bascula": mk(lect, "Lecturas_Bascula"),
                    "Fugas": mk(fu, "Fugas"), "Pruebas": mk(pr, "Pruebas")})

@st.cache_data(show_spinner=False)
def load_sensores():
    p = DATA / "lecturas_dw.csv"
    return pd.read_csv(p if p.exists() else DATA / "lecturas_mq.csv"), p.exists()

@st.cache_data(show_spinner=False)
def load_encuesta():
    p = DATA / "encuesta_respuestas.csv"
    if not p.exists(): return pd.DataFrame()
    d = pd.read_csv(p); return d[d.notna().sum(axis=1) >= 3].reset_index(drop=True)

ENC = load_encuesta()

with st.sidebar.expander("Opciones del tablero"):
    EXPLICA = st.toggle("Guía de lectura en cada gráfica", value=True, key="explica", help="Añade una línea que explica cómo leer cada gráfica.")
    DEMO = st.toggle("Vista previa de diseño", value=False, key="demo", help="Rellena el tablero con datos de ejemplo SOLO para revisar el diseño. Siempre se rotula como ejemplo.")
    up = st.file_uploader("Cargar Excel de pruebas", type="xlsx", help="Debe tener las hojas y columnas de Plantilla_CloudSense.xlsx. Reemplaza los datos solo durante esta sesión y las gráficas se recalculan solas.")
D, INFO = (make_demo(), None) if DEMO else load_excel(up if up else DATA / "Plantilla_CloudSense.xlsx")
SENS, DE_DW = load_sensores()
if INFO:
    with st.sidebar.expander("Datos cargados"):
        st.dataframe(pd.DataFrame(INFO), hide_index=True, width="stretch")
PUBLIC_URL = ""  # pega aquí el enlace público cuando publiques el tablero
with st.sidebar.popover("Abrir en el celular", icon=":material/qr_code_2:", width="stretch"):
    _url = st.text_input("Enlace público del tablero", value=PUBLIC_URL, placeholder="https://tu-tablero.streamlit.app")
    if _url.startswith("http"):
        import io, segno
        _b = io.BytesIO(); segno.make(_url, error="m").save(_b, kind="png", scale=8, border=2, dark="#07142B", light="#FFFFFF")
        st.image(_b.getvalue(), width=220); st.caption("Escanea el código con la cámara del celular.")
    else: st.caption("Pega el enlace público del tablero y aquí aparecerá su código QR.")
st.sidebar.caption("Fuente de datos: " + ("datos de ejemplo" if DEMO else ("Excel cargado" if up else "Plantilla_CloudSense.xlsx")))

# ------------------------------------------------------------------ utilidades
def header(titulo, pregunta):
    st.markdown(f'<div class="hdr"><div class="tag">C.L.O.U.D. SENSE · TABLERO DE CONTROL</div><h1>{titulo}</h1><p>{pregunta}</p></div>', unsafe_allow_html=True)
    if DEMO: st.markdown('<div class="demo">VISTA PREVIA DE DISEÑO · Datos de ejemplo, no son resultados del proyecto</div>', unsafe_allow_html=True)

def sec(t): st.markdown(f'<div class="sec"><span></span>{t}</div>', unsafe_allow_html=True)
def como_leer(t):
    if EXPLICA: st.caption(f"Cómo leerlo: {t}")

def vacio(hoja, para):
    with st.container(border=True):
        st.markdown(f"#### :material/hourglass_top: Esperando datos de las pruebas")
        st.write(f"Esta sección mostrará **{para}** en cuanto se cargue la hoja **{hoja}** de la plantilla Excel.")
        st.caption("Columnas esperadas: " + ", ".join(SHEETS[hoja]))
        if not DEMO: st.caption("Para ver cómo quedará esta sección, activa Vista previa de diseño en Opciones del tablero (muestra datos de ejemplo rotulados).")

def eap(e, a, p):
    st.markdown(f'<div class="eap"><div><b>Entender</b>{e}</div><div><b>Analizar</b>{a}</div><div><b>Proponer</b>{p}</div></div>', unsafe_allow_html=True)

def style(fig, h=380):
    fig.update_layout(height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#E6F1FF", family="Poppins"), margin=dict(l=10, r=10, t=50, b=10),
                      colorway=[CYAN, ORANGE, BLUE, YEL, GRN, RED], legend=dict(orientation="h", y=-0.2))
    fig.update_xaxes(gridcolor="#16345F"); fig.update_yaxes(gridcolor="#16345F")
    return fig

def moda(s):
    m = s.mode(); return m.iloc[0] if len(m) else np.nan

def color_estado(v):
    c = {"Crítico": RED, "Pendiente": RED, "Atención": YEL, "Lenta": YEL, "Normal": GRN, "Rápida": GRN}.get(v)
    return f"background-color:{c};color:#07142B;font-weight:600" if c else ""

def gauge(valor, titulo, rango=(0, 100), pasos=None, sufijo="%"):
    pasos = pasos or [(0, 33, GRN), (33, 66, YEL), (66, 100, RED)]
    f = go.Figure(go.Indicator(mode="gauge+number", value=valor, number=dict(suffix=sufijo, font=dict(color="#fff")), title=dict(text=titulo, font=dict(size=14)),
                               gauge=dict(axis=dict(range=list(rango)), bar=dict(color="#fff", thickness=.25), steps=[dict(range=[a, b], color=c) for a, b, c in pasos], bgcolor="#0E2547")))
    return style(f, 240).update_layout(margin=dict(l=20, r=20, t=60, b=10))

def estado_de(d, rojo, amar): return "Crítico" if d <= rojo else ("Atención" if d <= amar else "Normal")

def predecir(tanques, lect, reserva_pct, rojo, amar, ventana):
    filas = []
    for tid, g in lect.dropna(subset=["fecha_hora", "peso_kg"]).sort_values("fecha_hora").groupby("id_tanque"):
        g = g[g["fecha_hora"] >= g["fecha_hora"].max() - pd.Timedelta(days=ventana)]
        if len(g) < 3: continue
        subida = g["peso_kg"].diff() > 0.5
        if subida.any(): g = g.loc[subida[subida].index[-1]:]
        if len(g) < 3: continue
        t = (g["fecha_hora"] - g["fecha_hora"].iloc[0]).dt.total_seconds() / 86400
        pend, _ = np.polyfit(t, g["peso_kg"], 1)
        row = tanques.loc[tanques["id_tanque"] == tid]
        cap = float(row["capacidad_kg"].iloc[0]) if len(row) and pd.notna(row["capacidad_kg"].iloc[0]) else np.nan
        zona = row["zona"].iloc[0] if len(row) else None
        consumo = -pend; peso = float(g["peso_kg"].iloc[-1]); reserva = reserva_pct / 100 * cap if cap == cap else 0
        dias = max((peso - reserva) / consumo, 0.0) if consumo > 0 else np.inf
        fin = np.isfinite(dias)
        filas.append(dict(id_tanque=tid, zona=zona, estado=estado_de(dias, rojo, amar) if fin else "Sin consumo", dias_restantes=round(dias, 1) if fin else np.nan,
                          fecha_agotamiento=(g["fecha_hora"].iloc[-1] + pd.Timedelta(days=dias)).date() if fin else None,
                          nivel_pct=round(peso / cap * 100, 1) if cap == cap else np.nan, peso_actual_kg=round(peso, 1), consumo_kg_dia=round(consumo, 2), lecturas=len(g), capacidad_kg=cap))
    return pd.DataFrame(filas).sort_values("dias_restantes", na_position="last").reset_index(drop=True) if filas else pd.DataFrame()

# ------------------------------------------------------------------ páginas
def inicio():
    header("Inicio", "Un sistema que detecta fugas de gas LP y avisa cuándo reabastecer cada tanque")
    with st.container(border=True):
        a, b = st.columns([1, 1.6], vertical_alignment="center")
        a.image(str(ASSETS / "logo_horizontal.png"), width="stretch")
        b.markdown("### Detecta. Predice. Decide.")
        b.write("Un prototipo con **sensor de gas MQ-6** y **báscula** vigila cada tanque. Si hay una fuga, **avisa al instante**. Si el gas se está acabando, **calcula cuándo** habrá que reabastecer. "
                "Este tablero reúne todo para tomar mejores decisiones.")
    sec("Cómo funciona")
    pasos = [("sensors", "Medir", "El sensor MQ-6 huele el gas y la báscula pesa el tanque."), ("notifications_active", "Alertar", "Una alarma local suena y llega un aviso al celular."),
             ("database", "Analizar", "Los datos se limpian y se guardan en un almacén de datos."), ("insights", "Decidir", "El tablero muestra qué tanque atender primero.")]
    for col, (ic, t, d) in zip(st.columns(4), pasos):
        with col.container(border=True, height=175):
            n = pasos.index((ic, t, d)) + 1
            st.markdown(f'<div class="step">{n}</div>', unsafe_allow_html=True); st.markdown(f"**:material/{ic}: {t}**"); st.caption(d)
    sec("Explora el tablero")
    destinos = [("analisis1", "bar_chart", "Análisis 1 · Descriptivo", "¿Cuánto gas se entrega y cómo responden los sensores?"),
                ("analisis2", "trending_up", "Análisis 2 · Predictivo", "¿Cuándo se acaba el gas de cada tanque?"),
                ("analisis3", "gas_meter", "Análisis 3 · Fugas", "¿Dónde hay fugas y qué tan rápido se atienden?"),
                ("decisiones", "checklist", "Toma de decisiones", "¿Qué hacemos primero?")]
    for col, (pid, ic, t, q) in zip(st.columns(4), destinos):
        with col.container(border=True, height=195):
            st.markdown(f"**:material/{ic}: {t}**"); st.caption(q); st.page_link(PAGES[pid], label="Abrir sección", icon=":material/arrow_forward:")
    sec("El sistema en números")
    k = st.columns(5)
    k[0].metric("Lecturas de sensores", f"{len(SENS):,}", help="Lecturas históricas de 7 sensores MQ ya limpias y cargadas."); k[1].metric("Clases de gas", SENS["clase"].nunique())
    k[2].metric("Tanques vigilados", len(D["Tanques"])); k[3].metric("Alertas de fuga", len(D["Fugas"])); k[4].metric("Ensayos completados", f"{len(D['Pruebas'])}/30")
    st.progress(min(len(D["Pruebas"]) / 30, 1.0), text="Avance de las 30 pruebas del prototipo (10 por escenario)")
    if not DEMO and D["Tanques"].empty: st.caption("Los contadores en cero se llenan con los datos de las pruebas. No se usan datos simulados.")
    eap("El tablero responde cuatro preguntas de negocio y cierra con acciones concretas.", "Cada sección usa indicadores, gráficas y una guía de lectura.", "Recorre el menú lateral de arriba abajo; la última sección resume qué hacer.")

ORD = {"sin_gas": ["Nunca", "Una vez", "Varias veces"], "fuga": ["Nunca", "Una vez", "Varias veces"], "frecuencia": ["Cada semana", "Cada 2 semanas", "Cada mes", "Cada 2-3 meses"],
       "pago_unico": ["Menos de $600", "$600 - $1,000", "$1,000 - $1,500", "Más de $1,500"], "pago_mes": ["Nada", "$30 - $60", "$60 - $100", "Más de $100"], "compraria": ["Sí", "Tal vez", "No"]}

def conteo(col, titulo, h=300, tipo="bar"):
    c = ENC[col].dropna().value_counts().reset_index(); c.columns = ["opcion", "personas"]
    if col in ORD: c["opcion"] = pd.Categorical(c["opcion"], [o for o in ORD[col] if o in set(c["opcion"])] + [o for o in c["opcion"] if o not in ORD[col]], ordered=True); c = c.sort_values("opcion")
    if tipo == "pie": f = px.pie(c, names="opcion", values="personas", hole=.55, title=titulo)
    else: f = px.bar(c, x="opcion", y="personas", title=titulo, text_auto=True, labels={"opcion": "", "personas": "Personas"})
    return style(f, h)

def encuesta_view():
    if ENC.empty: vacio_encuesta(); return
    n = len(ENC); pc = lambda mask, base: f"{(mask.sum() / max(base.notna().sum(), 1)):.0%}"
    st.caption(f"Encuesta anónima sobre el uso de gas LP · {n} respuestas válidas. Con una muestra mayor (30 a 40) las conclusiones serían más sólidas.")
    k = st.columns(4)
    k[0].metric("Se han quedado sin gas", pc(ENC["sin_gas"].isin(["Una vez", "Varias veces"]), ENC["sin_gas"]), help="Alguna vez les pasó sin esperarlo.")
    k[1].metric("Sospecharon una fuga", pc(ENC["fuga"].isin(["Una vez", "Varias veces"]), ENC["fuga"]))
    k[2].metric("Utilidad del aviso (1 a 5)", f"{ENC['utilidad'].mean():.1f}", help=f"Mediana {ENC['utilidad'].median():.0f} · Moda {moda(ENC['utilidad'].dropna()):.0f}")
    k[3].metric("Lo comprarían", pc(ENC["compraria"] == "Sí", ENC["compraria"]), help="Respondieron que sí lo comprarían; con 'Tal vez' sube el interés.")
    sub = st.segmented_control("Tema", ["El problema", "El interés", "Precio y modelo"], default="El problema", key="enc_sub", label_visibility="collapsed") or "El problema"
    if sub == "El problema":
        a, b, c = st.columns(3)
        a.plotly_chart(conteo("sin_gas", "¿Se han quedado sin gas sin esperarlo?"), width="stretch"); b.plotly_chart(conteo("fuga", "¿Han sospechado una fuga?"), width="stretch")
        c.plotly_chart(conteo("como_sabe", "¿Cómo saben cuánto gas les queda?", tipo="pie"), width="stretch")
        como_leer("cada barra cuenta personas; la mayoría se ha quedado sin gas y casi nadie usa un medidor para saber cuánto le queda.")
        eap("Qué tan frecuente es el problema que resuelve el prototipo.", "Casi todos se han quedado sin gas alguna vez y la mayoría estima el nivel moviendo el tanque o no lo sabe.", "El aviso temprano y la medición de peso atienden una necesidad real.")
    elif sub == "El interés":
        a, b = st.columns(2)
        u = ENC["utilidad"].dropna().astype(int).value_counts().reindex(range(1, 6), fill_value=0).reset_index(); u.columns = ["nota", "personas"]
        a.plotly_chart(style(px.bar(u, x="nota", y="personas", title="Utilidad del aviso (1 = nada, 5 = mucho)", text_auto=True, labels={"nota": "Calificación", "personas": "Personas"}), 320), width="stretch")
        b.plotly_chart(conteo("importa", "¿Qué es lo que más les importaría?", 320), width="stretch")
        como_leer("barras altas a la derecha en la primera gráfica significan que el aviso les parece muy útil.")
        eap("Cuánto valora la gente un aviso de poco gas o de fuga.", f"{(ENC['utilidad'] >= 4).sum()} de {ENC['utilidad'].notna().sum()} personas lo califican con 4 o 5; lo que más importa es evitar fugas y que no se acabe el gas.", "Comunicar el producto con esos dos beneficios.")
    else:
        a, b = st.columns(2)
        a.plotly_chart(conteo("pago_unico", "¿Cuánto pagarían una sola vez?", 320), width="stretch"); b.plotly_chart(conteo("pago_mes", "¿Cuánto pagarían al mes?", 320), width="stretch")
        c, d = st.columns(2)
        c.plotly_chart(conteo("uso", "¿Cómo preferirían usarlo?", 300, "pie"), width="stretch"); d.plotly_chart(conteo("compraria", "Si existiera hoy, ¿lo comprarían?", 300), width="stretch")
        como_leer("compara el precio que aceptan con el costo del dispositivo para decidir el modelo de venta.")
        eap("Cuánto están dispuestos a pagar y cómo prefieren usarlo.", "La mayoría pagaría menos de $1,000 una sola vez y prefiere usar la app por su cuenta.", "Ofrecer el dispositivo a precio accesible y el monitoreo como servicio opcional.")

def vacio_encuesta():
    with st.container(border=True):
        st.markdown("#### :material/hourglass_top: Esperando respuestas de la encuesta")
        st.write("Guarda las respuestas en data/encuesta_respuestas.csv para ver esta sección.")

def analisis1():
    header("Análisis 1 · Descriptivo", "¿Cuánto gas se entrega, cómo responden los sensores y qué opina el mercado?")
    vista = st.segmented_control("Vista", ["Reabastecimiento (R1)", "Sensores de gas", "Encuesta de mercado"], default="Reabastecimiento (R1)", label_visibility="collapsed", key="v1") or "Reabastecimiento (R1)"
    if vista.startswith("Reabast"):
        rec, tq = D["Reabastecimientos"], D["Tanques"]
        if rec.empty or tq.empty: vacio("Reabastecimientos", "los kilogramos de gas entregados por zona, tipo de cliente y semestre"); return
        m = rec.merge(tq[["id_tanque", "zona", "tipo_cliente"]], on="id_tanque", how="left")
        m["semestre"] = m["fecha"].dt.year.astype("Int64").astype(str) + "-S" + np.where(m["fecha"].dt.month <= 6, "1", "2")
        c1, c2, c3 = st.columns([1.2, 1.2, 1.4])
        zonas = c1.multiselect("Zona", sorted(m["zona"].dropna().unique()), default=sorted(m["zona"].dropna().unique()))
        tipos = c2.multiselect("Tipo de cliente", sorted(m["tipo_cliente"].dropna().unique()), default=sorted(m["tipo_cliente"].dropna().unique()))
        dim = c3.radio("Agrupar por", ["zona", "tipo_cliente", "semestre"], horizontal=True, format_func=lambda x: {"zona": "Zona", "tipo_cliente": "Tipo de cliente", "semestre": "Semestre"}[x])
        m = m[m["zona"].isin(zonas) & m["tipo_cliente"].isin(tipos)]
        k = st.columns(5)
        k[0].metric("Gas entregado", f"{m['kg_cargados'].sum():,.0f} kg"); k[1].metric("Recargas", f"{len(m):,}"); k[2].metric("Media por recarga", f"{m['kg_cargados'].mean():,.1f} kg")
        k[3].metric("Mediana", f"{m['kg_cargados'].median():,.1f} kg"); k[4].metric("Moda", f"{moda(m['kg_cargados']):,.1f} kg")
        g1, g2 = st.columns([1.5, 1])
        with g1:
            g = m.groupby([dim, "semestre" if dim != "semestre" else "tipo_cliente"], as_index=False)["kg_cargados"].sum()
            st.plotly_chart(style(px.bar(g, x=dim, y="kg_cargados", color=g.columns[1], barmode="group", title="Kilogramos entregados", labels={"kg_cargados": "kg entregados", "zona": "Zona", "tipo_cliente": "Tipo de cliente", "semestre": "Semestre"})), width="stretch"); como_leer("cada barra suma los kilogramos entregados; cambia el agrupamiento arriba.")
        with g2:
            st.plotly_chart(style(px.pie(m.groupby("tipo_cliente", as_index=False)["kg_cargados"].sum(), names="tipo_cliente", values="kg_cargados", hole=.55, title="Participación por tipo de cliente")), width="stretch"); como_leer("qué porción del gas va a cada tipo de cliente.")
        eap("Cuánto gas se entrega, y a quién, por zona y semestre.", "Compara la altura de las barras para ubicar las zonas y clientes que más consumen.", "Planear rutas de reparto primero hacia las zonas de mayor volumen.")
    elif vista == "Sensores de gas":
        sec("Qué tanto reacciona el sensor MQ-6")
        u = st.slider("Umbral de alerta del MQ-6", 300, 700, 450, 5, help="Una lectura cuenta como alerta cuando el MQ-6 llega a este valor o lo supera.")
        s = SENS.copy(); s["alerta"] = s["mq6"] >= u; pct = s["alerta"].mean()
        k = st.columns(4); k[0].metric("Lecturas analizadas", f"{len(s):,}"); k[1].metric("Alertas generadas", f"{int(s['alerta'].sum()):,}")
        k[2].metric("MQ-6 media | mediana", f"{s['mq6'].mean():.0f} | {s['mq6'].median():.0f}"); k[3].metric("Moda | desviación", f"{moda(s['mq6']):.0f} | {s['mq6'].std():.1f}")
        a, b = st.columns([1, 1.6])
        a.plotly_chart(gauge(round(pct * 100, 1), "Porcentaje de lecturas en alerta", (0, 100), [(0, 10, GRN), (10, 30, YEL), (30, 100, RED)]), width="stretch"); 
        with a: como_leer("la aguja indica qué parte de las lecturas dispara la alerta con el umbral elegido.")
        xs = np.arange(300, 701, 5); ys = [(s["mq6"] >= x).mean() * 100 for x in xs]
        fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=CYAN, width=3), name="% en alerta")); fig.add_trace(go.Scatter(x=[u], y=[pct * 100], mode="markers", marker=dict(size=14, color=ORANGE), name="Umbral elegido"))
        b.plotly_chart(style(fig.update_layout(title="¿Qué pasa si subo o bajo el umbral?", xaxis_title="Umbral MQ-6", yaxis_title="% de lecturas en alerta"), 280), width="stretch")
        with b: como_leer("a mayor umbral, menos alertas. El punto naranja es tu selección.")
        sec("La huella de cada gas")
        c1, c2 = st.columns(2)
        med = s.groupby("clase")[MQ].mean(); z = (med - med.mean()) / med.std(ddof=0)
        hm = px.imshow(z.values, x=[m.upper() for m in MQ], y=med.index, aspect="auto", color_continuous_scale=[[0, NAVY], [.5, BLUE], [1, ORANGE]], title="Respuesta de cada sensor por clase de gas")
        hm.update_traces(text=med.round(0).values, texttemplate="%{text}"); hm.update_coloraxes(showscale=False)
        c1.plotly_chart(style(hm, 360), width="stretch")
        with c1: como_leer("más naranja = el sensor reacciona más a ese gas; el número es el promedio de lectura.")
        with c2:
            sel = st.pills("Sensor a comparar", MQ, default="mq6", format_func=str.upper) or "mq6"
            bx = px.box(s, x="clase", y=sel, color="clase", title=f"Distribución de {sel.upper()} por clase")
            if sel == "mq6": bx.add_hline(y=u, line_dash="dash", line_color=ORANGE, annotation_text="Umbral")
            st.plotly_chart(style(bx, 330), width="stretch"); como_leer("la caja muestra dónde está la mayoría de las lecturas; los puntos son valores atípicos.")
        sec("Lecturas en el tiempo")
        if DE_DW and {"turno", "nombre_semestre", "anio_mes"} <= set(s.columns):
            sems = sorted(s["nombre_semestre"].dropna().unique())
            sel_s = st.segmented_control("Semestre", ["Todos"] + sems, default="Todos", key="sem") or "Todos"
            v = s if sel_s == "Todos" else s[s["nombre_semestre"] == sel_s]
            d1, d2 = st.columns(2)
            ps = s.groupby("nombre_semestre").agg(lecturas=("mq6", "size"), mq6_prom=("mq6", "mean")).reset_index()
            f = go.Figure(go.Bar(x=ps["nombre_semestre"], y=ps["lecturas"], name="Lecturas", marker_color=CYAN))
            f.add_trace(go.Scatter(x=ps["nombre_semestre"], y=ps["mq6_prom"], name="MQ-6 promedio", yaxis="y2", mode="lines+markers", line=dict(color=ORANGE, width=3)))
            f.update_layout(title="Lecturas y MQ-6 promedio por semestre", yaxis_title="Lecturas", yaxis2=dict(overlaying="y", side="right", title="MQ-6 promedio", showgrid=False, range=[0, float(ps["mq6_prom"].max()) * 1.3]))
            d1.plotly_chart(style(f), width="stretch")
            with d1: como_leer("las barras son la cantidad de lecturas (eje izquierdo); la línea naranja es el MQ-6 promedio (eje derecho). Las escalas son distintas.")
            pm = v.groupby("anio_mes").size().reset_index(name="lecturas").sort_values("anio_mes")
            d2.plotly_chart(style(px.bar(pm, x="anio_mes", y="lecturas", title=f"Lecturas por mes ({sel_s})", labels={"anio_mes": "Mes", "lecturas": "Lecturas"})), width="stretch")
            with d2: como_leer("elige un semestre arriba para ver sus meses (de semestre a mes).")
            e1, e2 = st.columns(2)
            e1.plotly_chart(style(px.bar(v.groupby("clase").size().reset_index(name="lecturas"), x="clase", y="lecturas", title=f"Lecturas por clase de gas ({sel_s})", text_auto=True, labels={"clase": "Clase", "lecturas": "Lecturas"})), width="stretch")
            e2.plotly_chart(style(px.bar(v.groupby("turno")["alerta"].sum().reset_index(), x="turno", y="alerta", title=f"Alertas MQ-6 por turno ({sel_s})", labels={"turno": "Turno", "alerta": "Alertas"})), width="stretch")
        else:
            st.caption("Para ver lecturas por mes, semestre y turno, exporta el almacén de datos con exportar_dw.py (genera data/lecturas_dw.csv).")
        eap("El MQ-6 convierte la cantidad de gas en un número; el umbral decide cuándo suena la alarma.", "La huella muestra que ningún sensor por sí solo separa todos los gases: el MQ-6 reacciona distinto en cada clase.",
            "Calibrar el umbral con las pruebas y usar la báscula como segunda señal para evitar falsas alarmas.")
    else:
        encuesta_view()

def analisis2():
    header("Análisis 2 · Predictivo", "R2 · ¿Cuándo habrá que reabastecer cada tanque?")
    lect, tq = D["Lecturas_Bascula"], D["Tanques"]
    with st.popover("Ajustar el modelo", icon=":material/tune:"):
        reserva = st.slider("Reserva mínima del tanque (%)", 0, 30, 10); rojo = st.slider("Crítico si quedan (días) ≤", 1, 10, 3)
        amar = st.slider("Atención si quedan (días) ≤", 3, 30, 7); vent = st.slider("Ventana de consumo (días)", 3, 90, 30)
    if lect.empty: vacio("Lecturas_Bascula", "los tanques ordenados por urgencia y su fecha estimada de agotamiento"); return
    res = predecir(tq, lect, reserva, rojo, amar, vent)
    if res.empty: st.warning("Hay lecturas, pero se necesitan al menos 3 por tanque dentro de la ventana elegida."); return
    k = st.columns(4); k[0].metric("Tanques analizados", len(res)); k[1].metric("Críticos", int((res["estado"] == "Crítico").sum()), help="Tanques que se agotan pronto.")
    k[2].metric("Consumo medio", f"{res['consumo_kg_dia'].mean():.2f} kg/día"); k[3].metric("Mediana de días restantes", f"{res['dias_restantes'].median():.1f}")
    sec("Qué tanque atender primero")
    a, b = st.columns([1, 1.3])
    top = res.dropna(subset=["dias_restantes"]).head(15).iloc[::-1]
    fb = px.bar(top, x="dias_restantes", y="id_tanque", color="estado", color_discrete_map=ESTADO_COL, orientation="h", title="Días restantes por tanque", labels={"dias_restantes": "Días restantes", "id_tanque": "Tanque", "estado": "Estado"}, category_orders={"estado": ["Crítico", "Atención", "Normal"]})
    fb.update_yaxes(categoryorder="array", categoryarray=list(top["id_tanque"]))
    a.plotly_chart(style(fb, 420), width="stretch")
    with a: como_leer("barras cortas y rojas = tanques que se acaban primero.")
    cols = ["id_tanque", "zona", "estado", "dias_restantes", "fecha_agotamiento", "nivel_pct", "consumo_kg_dia"]
    b.dataframe(res[cols].style.map(color_estado, subset=["estado"]), hide_index=True, height=420, width="stretch",
                column_config={"id_tanque": "Tanque", "zona": "Zona", "estado": "Estado", "dias_restantes": st.column_config.NumberColumn("Días restantes", format="%.1f"), "fecha_agotamiento": "Se agota el",
                               "nivel_pct": st.column_config.ProgressColumn("Nivel actual", min_value=0, max_value=100, format="%.0f%%"), "consumo_kg_dia": st.column_config.NumberColumn("Consumo (kg/día)", format="%.2f")})
    with b: como_leer("ordenada de más a menos urgente; la barra muestra cuánto gas queda.")
    sec("Detalle de un tanque y simulador")
    t = st.selectbox("Elige un tanque", res["id_tanque"], key="tsel")
    r = res[res["id_tanque"] == t].iloc[0]; g = lect[lect["id_tanque"] == t].sort_values("fecha_hora")
    aj = st.slider("¿Y si el consumo cambia? (%)", -50, 100, 0, 5, help="Simula qué pasaría si el cliente consume más o menos gas.")
    cons2 = r["consumo_kg_dia"] * (1 + aj / 100); reserva_kg = reserva / 100 * r["capacidad_kg"] if r["capacidad_kg"] == r["capacidad_kg"] else 0
    dias2 = (r["peso_actual_kg"] - reserva_kg) / cons2 if cons2 > 0 else np.nan
    c1, c2, c3 = st.columns([1, 1, 2.2])
    c1.plotly_chart(gauge(float(r["nivel_pct"]) if pd.notna(r["nivel_pct"]) else 0, "Nivel actual del tanque", pasos=[(0, 15, RED), (15, 35, YEL), (35, 100, GRN)]), width="stretch")
    c2.metric("Días restantes", f"{dias2:.1f}" if pd.notna(dias2) else "Sin consumo", delta=f"{dias2 - r['dias_restantes']:+.1f} días vs. normal" if pd.notna(dias2) and pd.notna(r["dias_restantes"]) else None)
    c2.metric("Se agota el", str((g["fecha_hora"].max() + pd.Timedelta(days=float(dias2))).date()) if pd.notna(dias2) else "-")
    fig = go.Figure(go.Scatter(x=g["fecha_hora"], y=g["peso_kg"], name="Peso medido", line=dict(color=CYAN, width=3)))
    if pd.notna(dias2):
        x1 = g["fecha_hora"].max(); fig.add_trace(go.Scatter(x=[x1, x1 + pd.Timedelta(days=float(dias2))], y=[r["peso_actual_kg"], reserva_kg], name="Proyección", line=dict(color=ORANGE, dash="dash", width=3)))
        fig.add_hline(y=reserva_kg, line_dash="dot", line_color=RED, annotation_text="Reserva mínima")
    c3.plotly_chart(style(fig.update_layout(title=f"Peso del tanque {t} y proyección de agotamiento", yaxis_title="kg"), 320), width="stretch")
    with c3: como_leer("la línea azul es el peso real; la naranja punteada proyecta cuándo se llega a la reserva.")
    eap("Con la báscula se mide cuánto gas pierde el tanque por día; ese ritmo permite proyectar cuándo se acaba.", "Días restantes = (peso actual - reserva) / consumo diario. El simulador muestra el efecto de un cambio de consumo.",
        "Programar primero los tanques críticos y agrupar las rutas por zona.")

def analisis3():
    header("Análisis 3 · Fugas", "R3 y R4 · ¿Dónde hay fugas, qué tan rápido se atienden y cómo se comporta el prototipo?")
    tab = st.segmented_control("Sección", ["Mapa de fugas (R3)", "Atención (R4)", "Pruebas del prototipo"], default="Mapa de fugas (R3)", label_visibility="collapsed", key="v3") or "Mapa de fugas (R3)"
    fu, tq, pr = D["Fugas"], D["Tanques"], D["Pruebas"]
    if tab.startswith("Mapa"):
        if fu.empty: vacio("Fugas", "el mapa de fugas por zona y tipo de cliente"); return
        m = fu.merge(tq, on="id_tanque", how="left")
        gr = st.multiselect("Gravedad", ["Leve", "Media", "Alta"], default=["Leve", "Media", "Alta"]); m = m[m["gravedad"].isin(gr)]
        a, b = st.columns([1.6, 1]); ll = m.dropna(subset=["latitud", "longitud"])
        if len(ll):
            mp = px.scatter_map(ll, lat="latitud", lon="longitud", color="gravedad", color_discrete_map={"Leve": GRN, "Media": YEL, "Alta": RED}, zoom=11, hover_data=["id_tanque", "zona", "nivel_mq6"], map_style="carto-darkmatter")
            mp.update_traces(marker=dict(size=14)); a.plotly_chart(style(mp, 440), width="stretch")
        with a: como_leer("cada punto es una fuga; el color indica la gravedad.")
        b.plotly_chart(style(px.bar(m.groupby(["zona", "tipo_cliente"], as_index=False).size(), x="zona", y="size", color="tipo_cliente", title="Fugas por zona y tipo de cliente"), 440), width="stretch")
    elif tab.startswith("Aten"):
        if fu.empty: vacio("Fugas", "el tiempo de respuesta y las fugas sin atender"); return
        k = st.columns(4); pend = int((fu["atendida"] == 0).sum())
        k[0].metric("Alertas", len(fu)); k[1].metric("Sin atender", pend); k[2].metric("Respuesta media", f"{fu['tiempo_respuesta_min'].mean():.1f} min"); k[3].metric("Mediana", f"{fu['tiempo_respuesta_min'].median():.1f} min")
        a, b = st.columns([1.4, 1])
        v = fu.copy(); v["semáforo"] = np.where(v["atendida"] == 0, "Pendiente", np.where(v["tiempo_respuesta_min"] > 30, "Lenta", "Rápida"))
        a.dataframe(v.sort_values("fecha_hora", ascending=False)[["id_alerta", "id_tanque", "fecha_hora", "gravedad", "tiempo_respuesta_min", "semáforo"]].style.map(color_estado, subset=["semáforo"]), hide_index=True, height=380, width="stretch")
        b.plotly_chart(style(px.histogram(fu, x="tiempo_respuesta_min", nbins=10, title="Distribución del tiempo de respuesta (min)"), 380), width="stretch")
        with b: como_leer("barras altas a la izquierda = respuestas rápidas.")
    else:
        if pr.empty: vacio("Pruebas", "los resultados de los 30 ensayos por escenario"); return
        k = st.columns(4); k[0].metric("Ensayos", f"{len(pr)}/30"); k[1].metric("Respuesta media", f"{pr['tiempo_respuesta_s'].mean():.1f} s")
        k[2].metric("Latencia de aviso (mediana)", f"{pr['latencia_notificacion_s'].median():.1f} s"); k[3].metric("Alarma activada", f"{pr['alarma_activada'].mean():.0%}")
        a, b = st.columns(2)
        a.plotly_chart(style(px.box(pr, x="escenario", y="tiempo_respuesta_s", color="escenario", points="all", title="Tiempo de respuesta por escenario (s)")), width="stretch")
        fg = px.scatter(pr, x="concentracion_ppm", y="tiempo_respuesta_s", color="escenario", title="Concentración de gas vs. tiempo de respuesta"); q = pr.dropna(subset=["concentracion_ppm", "tiempo_respuesta_s"])
        if len(q) > 3 and q["concentracion_ppm"].nunique() > 1:
            bb, a0 = np.polyfit(q["concentracion_ppm"], q["tiempo_respuesta_s"], 1); xs = np.array([q["concentracion_ppm"].min(), q["concentracion_ppm"].max()])
            fg.add_trace(go.Scatter(x=xs, y=a0 + bb * xs, mode="lines", name="Tendencia", line=dict(color=ORANGE, dash="dash")))
        b.plotly_chart(style(fg), width="stretch")
        with a: como_leer("A: cocina, B: exterior junto a tanques, C: comercio cerrado. Cajas más bajas = respuesta más rápida.")
    eap("Las fugas se ubican en el mapa y se mide qué tan rápido se atienden; las pruebas validan que el prototipo funciona.", "Zonas con más puntos rojos y tiempos largos necesitan atención.", "Reforzar la atención donde las respuestas sean lentas o haya fugas pendientes.")

@st.dialog("Cómo se calcula")
def explicar():
    st.write("**Reabastecimiento:** se ajusta una recta al peso del tanque desde su última recarga; la pendiente es el consumo diario. Días restantes = (peso actual - reserva) / consumo diario.")
    st.write("**Fugas:** una alerta está pendiente cuando no se ha marcado como atendida. **Calibración:** se mide qué porcentaje de lecturas históricas del MQ-6 superaría el umbral elegido.")

def decisiones():
    header("Toma de decisiones", "¿Qué hacemos primero con lo que muestran los datos?")
    acc = []; lect, tq, fu = D["Lecturas_Bascula"], D["Tanques"], D["Fugas"]
    if not lect.empty:
        res = predecir(tq, lect, 10, 3, 7, 30)
        if len(res):
            crit = res[res["estado"] == "Crítico"]; acc.append(("Crítico" if len(crit) else "Normal", "Reabastecer", f"{len(crit)} tanque(s) críticos: " + ", ".join(map(str, crit["id_tanque"].head(6))) if len(crit) else "Ningún tanque en estado crítico."))
    if not fu.empty:
        pend = int((fu["atendida"] == 0).sum()); acc.append(("Crítico" if pend else "Normal", "Atender fugas", f"{pend} alerta(s) sin atender; respuesta mediana {fu['tiempo_respuesta_min'].median():.1f} min."))
    u = st.slider("Umbral del MQ-6 a evaluar", 300, 700, 450, 5); pct = (SENS["mq6"] >= u).mean()
    acc.append(("Atención" if pct > .1 else "Normal", "Calibrar el sensor", f"Con umbral {u}, el {pct:.1%} de las lecturas históricas serían alerta."))
    medidores = []
    if not lect.empty and len(res): medidores.append((100 * (res["estado"] == "Crítico").mean(), "Tanques en estado crítico"))
    if not fu.empty: medidores.append((100 * (fu["atendida"] == 0).mean(), "Fugas sin atender"))
    medidores.append((round(pct * 100, 1), "Lecturas en alerta (MQ-6)"))
    sec("Panorama")
    for col, (val, tit) in zip(st.columns(len(medidores)), medidores):
        col.plotly_chart(gauge(round(float(val), 1), tit, (0, 100), [(0, 10, GRN), (10, 30, YEL), (30, 100, RED)]), width="stretch")
    como_leer("cuanto más a la derecha y más rojo, más urgente es esa situación.")
    if not ENC.empty:
        pc_ = (ENC["compraria"] == "Sí").sum() / max(ENC["compraria"].notna().sum(), 1); ut_ = (ENC["utilidad"] >= 4).sum() / max(ENC["utilidad"].notna().sum(), 1)
        p6 = (ENC["pago_unico"] == "Menos de $600").sum() / max(ENC["pago_unico"].notna().sum(), 1)
        acc.append(("Atención" if p6 >= .4 else "Normal", "Validación de mercado", f"{pc_:.0%} lo compraría y {ut_:.0%} califica el aviso con 4 o 5; {p6:.0%} pagaría menos de $600 por el dispositivo."))
    sec("Prioridades")
    for est, t, d in acc: st.markdown(f'<div class="card" style="border-left-color:{ESTADO_COL[est]}"><b style="color:{ESTADO_COL[est]}">{est.upper()}</b> &nbsp;·&nbsp; <b>{t}:</b> {d}</div>', unsafe_allow_html=True)
    if lect.empty and fu.empty: vacio("Lecturas_Bascula", "las prioridades de reabastecimiento y de atención de fugas")
    sec("Plan de acción")
    plan = st.data_editor(pd.DataFrame({"Acción": ["Recargar tanques críticos", "Atender fugas pendientes", "Ajustar el umbral del MQ-6", "Reforzar zonas de mayor demanda"], "Responsable": ["", "", "", ""], "Hecho": [False] * 4}), hide_index=True, width="stretch")
    c1, c2, _ = st.columns([1, 1, 3]); c1.download_button("Descargar plan (CSV)", plan.to_csv(index=False).encode("utf-8-sig"), "plan_de_accion.csv", "text/csv", icon=":material/download:")
    if c2.button("Cómo se calcula", icon=":material/help:"): explicar()
    eap("Las prioridades se generan solas con los datos cargados; sin datos no se inventan recomendaciones.", "Primero lo crítico, luego lo que requiere atención.", "Asignar un responsable a cada acción y dar seguimiento en el plan.")

PAGES = {"inicio": st.Page(inicio, title="Inicio", icon=":material/home:", default=True),
         "analisis1": st.Page(analisis1, title="Análisis 1 · Descriptivo", icon=":material/bar_chart:", url_path="analisis1"),
         "analisis2": st.Page(analisis2, title="Análisis 2 · Predictivo", icon=":material/trending_up:", url_path="analisis2"),
         "analisis3": st.Page(analisis3, title="Análisis 3 · Fugas", icon=":material/gas_meter:", url_path="analisis3"),
         "decisiones": st.Page(decisiones, title="Toma de decisiones", icon=":material/checklist:", url_path="decisiones")}
st.navigation(list(PAGES.values())).run()
