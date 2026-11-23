"""Minería de datos para el tablero: lee modelos_mineria / resultados_mineria del DW (PostgreSQL)
y, si la base no responde, usa los CSV de respaldo de la carpeta data/."""
from pathlib import Path
import numpy as np, pandas as pd, plotly.graph_objects as go, plotly.express as px, streamlit as st

DATA = Path(__file__).parent / "data"
CLASES = ["NoGas", "Perfume", "Smoke", "Mixture"]
SQL_MODELOS = ("SELECT ejecucion_id, algoritmo, tecnica, variable_objetivo, exactitud, precision_pond, recall_pond, "
               "f1_pond, auc, n_entrenamiento, n_prueba, ejecutado_en, notas FROM modelos_mineria ORDER BY ejecutado_en DESC")
SQL_RESULT = ("SELECT lectura_id, clase_real, clase_predicha, probabilidad FROM resultados_mineria "
              "WHERE ejecucion_id = :ej")


@st.cache_data(ttl=60, show_spinner=False)
def _consulta(sql, ej=None):
    """Consulta de solo lectura con st.connection. Si falla lanza la excepción (así un fallo no se queda en caché)."""
    con = st.connection("postgresql", type="sql")
    return con.query(sql, params={"ej": ej} if ej else None, ttl=0)


def cargar():
    """Devuelve dict(ok, fuente, modelos, resultados). Primero PostgreSQL, luego CSV de respaldo."""
    motivo = "tablas vacías"
    try:
        m = _consulta(SQL_MODELOS)
        if m is not None and not m.empty:
            r = _consulta(SQL_RESULT, str(m.iloc[0]["ejecucion_id"]))
            if r is not None and not r.empty:
                return dict(ok=True, fuente="PostgreSQL (bodega de datos)", modelos=m, resultados=r)
    except Exception as e:
        motivo = type(e).__name__ + ": " + (str(getattr(e, "orig", e)).strip().splitlines() or [""])[0][:110]
    pm, pr = DATA / "modelos_mineria_respaldo.csv", DATA / "resultados_mineria_respaldo.csv"
    if pm.exists() and pr.exists():
        return dict(ok=True, fuente=f"archivos de respaldo (sin conexión a la base · {motivo})", modelos=pd.read_csv(pm), resultados=pd.read_csv(pr))
    return dict(ok=False, fuente="sin datos", modelos=pd.DataFrame(), resultados=pd.DataFrame())


def _num(x):
    try: return float(x)
    except (TypeError, ValueError): return np.nan


def _analiza(M):
    """Calcula matriz de confusión y métricas por clase a partir de resultados_mineria."""
    r, m = M["resultados"], M["modelos"].iloc[0]
    clases = [c for c in CLASES if c in set(r["clase_real"]) | set(r["clase_predicha"])] or sorted(set(r["clase_real"]))
    cm = pd.crosstab(r["clase_real"], r["clase_predicha"]).reindex(index=clases, columns=clases, fill_value=0)
    tp = np.diag(cm.values).astype(float)
    rec = tp / cm.sum(axis=1).replace(0, np.nan).values
    pre = tp / cm.sum(axis=0).replace(0, np.nan).values
    err = cm.copy().astype(int)
    for c in clases: err.loc[c, c] = 0
    pares = err.stack(); pares = pares[pares > 0].sort_values(ascending=False)
    return dict(m=m, cm=cm, rec=pd.Series(rec, index=clases), pre=pd.Series(pre, index=clases), pares=pares,
                n=len(r), aciertos=int(tp.sum()), clases=clases)


def prioridad(M):
    """Tarjeta para 'Prioridades' de Toma de decisiones (o None si no hay datos)."""
    if not M["ok"] or M["resultados"].empty: return None
    a = _analiza(M); exa = a["aciertos"] / a["n"]; peor = a["rec"].idxmin()
    if len(a["pares"]):
        (real, pred), k = next(iter(a["pares"].items()))
        txt = f"{a['m']['algoritmo']} acierta {exa:.1%}; el error principal es confundir {real} con {pred} ({k} lecturas)."
    else:
        txt = f"{a['m']['algoritmo']} acierta {exa:.1%} sin confusiones entre clases."
    return ("Normal" if exa >= .95 and a["rec"].min() >= .9 else "Atención", "Usar el modelo de minería", txt)


def bloque(M, sec, kpi_card, style, eap, colores):
    """Sección 'Minería de datos' de la página Toma de decisiones."""
    NAVY, TERRACOTA, TEAL, MUSTARD, BRICK = colores
    sec("Minería de datos: ¿qué modelo se usa y qué tan confiable es?")
    if not M["ok"] or M["resultados"].empty:
        with st.container(border=True):
            st.markdown("#### :material/hourglass_top: Esperando resultados de la minería")
            st.write("Esta sección se llena con las tablas **modelos_mineria** y **resultados_mineria** de la bodega de datos.")
        return
    a = _analiza(M); m = a["m"]; exa = a["aciertos"] / a["n"]
    st.caption(f"Fuente: {M['fuente']} · corrida **{m['ejecucion_id']}** · {a['n']:,} lecturas evaluadas")
    k = st.columns(4)
    with k[0]: kpi_card(f"{exa*100:.1f}", "Exactitud (aciertos)", color=TEAL, explicacion="De cada 100 lecturas, en cuántas el modelo acertó el tipo de gas.")
    with k[1]: kpi_card(f"{_num(m.get('f1_pond'))*100:.1f}" if pd.notna(_num(m.get('f1_pond'))) else "n/d", "F1 ponderado", color=NAVY, explicacion="Una nota que combina aciertos y falsas alarmas en todas las clases. Más cerca de 100, mejor.")
    with k[2]: kpi_card(f"{_num(m.get('auc'))*100:.1f}" if pd.notna(_num(m.get('auc'))) else "n/d", "AUC (separación de clases)", color=TERRACOTA, explicacion="Qué tan bien el modelo distingue un tipo de gas de otro. 100 sería perfecto; 50, como lanzar una moneda.")
    with k[3]: kpi_card(f"{a['n']-a['aciertos']:,}", "Lecturas mal clasificadas", rango=(0, max(a['n'], 1)), color=BRICK, sufijo="", explicacion="Cuántas lecturas el modelo confundió con otro tipo de gas.")

    c1, c2 = st.columns(2)
    z = a["cm"].values; cl = a["clases"]
    fig = go.Figure(go.Heatmap(z=z, x=cl, y=cl, colorscale=[[0, "#FFFFFF"], [1, "#1F5FA8"]], showscale=False,
                               text=z, texttemplate="%{text}", hovertemplate="Real %{y} → predicho %{x}: %{z}<extra></extra>"))
    fig.update_layout(title="Matriz de confusión (filas = real, columnas = predicho)", xaxis_title="Clase predicha", yaxis_title="Clase real")
    fig.update_yaxes(autorange="reversed")
    c1.plotly_chart(style(fig), width="stretch")
    pc = pd.DataFrame({"Clase": cl * 2, "Métrica": ["Recall (detectadas)"] * len(cl) + ["Precisión"] * len(cl),
                       "Valor": list(a["rec"].values * 100) + list(a["pre"].values * 100)})
    fb = px.bar(pc, x="Clase", y="Valor", color="Métrica", barmode="group", title="Desempeño por clase (%)",
                color_discrete_sequence=[TERRACOTA, NAVY]); fb.update_yaxes(range=[0, 100], title="%")
    c2.plotly_chart(style(fb), width="stretch")

    if len(a["pares"]):
        t = a["pares"].reset_index(); t.columns = ["Clase real", "Predicha como", "Lecturas"]
        st.markdown("**Dónde se equivoca el modelo**"); tabla(t)
    with st.expander("Corridas registradas en la bodega"):
        tabla(M["modelos"])
    peor = a["rec"].idxmin()
    eap(f"El modelo {m['algoritmo']} clasifica el tipo de lectura de la matriz de sensores MQ con {exa:.1%} de exactitud.",
        f"La clase más difícil es {peor} (recall {a['rec'].min():.1%}); " + ("las demás se detectan casi sin error." if a["rec"].drop(peor).min() >= .99 else "revisar también el resto de clases."),
        "Usar el modelo para filtrar falsas alarmas y reforzar con más muestras de la clase que más se confunde.")


def tabla(datos, destino=None):
    """Tabla: nativa de día; en modo noche se dibuja como HTML para que respete los colores oscuros."""
    d = destino or st
    if not st.session_state.get("modo_noche", False):
        d.dataframe(datos, hide_index=True, width="stretch", **({"height": 420} if hasattr(datos, "data") else {})); return
    sty = datos if hasattr(datos, "to_html") and hasattr(datos, "data") else datos.style
    d.markdown('<div class="tbl-w">' + sty.hide(axis="index").to_html() + '</div>', unsafe_allow_html=True)
