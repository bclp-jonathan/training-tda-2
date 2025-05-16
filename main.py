import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Tarjetas de Crédito en Chile", layout="wide")
st.title("Análisis de Tarjetas de Crédito por Emisor en Chile")

# Paleta de colores BCG
bcg_colors = ["#00654F", "#00B398", "#A2AAAD", "#005F73", "#E0E1DD"]

# Cargar archivo
uploaded_file = st.file_uploader("Sube el archivo Excel CMF de tarjetas de crédito", type=["xlsx"])

if uploaded_file:
    # Leer archivo con estructura conocida
    df_raw = pd.read_excel(uploaded_file, sheet_name='tarj_vig_tit_emi', skiprows=3)
    df_raw.rename(columns={df_raw.columns[0]: "Fecha"}, inplace=True)
    df_raw.dropna(axis=1, how='all', inplace=True)
    df_raw["Fecha"] = pd.to_datetime(df_raw["Fecha"], errors='coerce')

    for col in df_raw.columns[1:]:
        df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce')

    df = df_raw[df_raw["Fecha"].notna()].copy()

    # Navegación horizontal
    tabs = st.tabs([
        "1. Más tarjetas hoy",
        "2. Mayor crecimiento 2 años",
        "3. Mayor pérdida de participación",
        "4. Participación Banco de Chile",
        "5. Comparación competidores",
        "6. Crecimiento últimos 12 meses",
        "7. Alertas de caída Banco de Chile",
        "8. Apertura participación (Waterfall)"
    ])

    with tabs[0]:
        st.header("1. Emisor con más tarjetas al día de hoy")
        latest = df.iloc[-1]
        fecha_actual = latest["Fecha"]
        emisores = pd.Series(latest[1:].dropna().values, index=latest[1:].dropna().index.astype(str))
        emisores_sorted = emisores.sort_values(ascending=False)
        st.metric("Emisor con más tarjetas", emisores_sorted.index[0], f"{int(emisores_sorted.iloc[0]):,} tarjetas")

        df_bar1 = emisores_sorted.head(10).reset_index()
        df_bar1.columns = ["Emisor", "Tarjetas Vigentes"]

        fig1 = px.bar(df_bar1,
                      x="Emisor",
                      y="Tarjetas Vigentes",
                      text="Tarjetas Vigentes",
                      labels={"Tarjetas Vigentes": "Tarjetas Vigentes", "Emisor": "Emisor"},
                      title=f"Top 10 emisores con más tarjetas ({fecha_actual.date()})",
                      color_discrete_sequence=bcg_colors)
        fig1.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        fig1.update_layout(xaxis_tickangle=-45, uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig1, use_container_width=True)

    with tabs[1]:
        st.header("2. Emisor que más ha crecido en los últimos 2 años")
        fecha_ini = pd.Timestamp("2023-02-01")
        fecha_fin = pd.Timestamp("2025-02-01")
        df_2y = df[df["Fecha"].isin([fecha_ini, fecha_fin])].set_index("Fecha")
        crecimiento_abs = df_2y.loc[fecha_fin] - df_2y.loc[fecha_ini]
        crecimiento_pct = (crecimiento_abs / df_2y.loc[fecha_ini]) * 100
        crecimiento_abs = crecimiento_abs.dropna()
        crecimiento_pct = crecimiento_pct.dropna()
        top_crecimiento = crecimiento_pct.sort_values(ascending=False).head(1)
        emisor_top = top_crecimiento.index[0]
        tarjetas_ini = int(df_2y.loc[fecha_ini, emisor_top])
        tarjetas_fin = int(df_2y.loc[fecha_fin, emisor_top])
        var_pct = top_crecimiento.iloc[0]
        st.metric("Mayor crecimiento porcentual", emisor_top,
                  f"{var_pct:.2f}% ({tarjetas_ini:,} → {tarjetas_fin:,})")
        fig2 = px.bar(crecimiento_pct.sort_values(ascending=False).head(10).reset_index(),
                      x="index", y=0, text=0,
                      labels={"index": "Emisor", 0: "Crecimiento %"},
                      title="Top 10 emisores con mayor crecimiento porcentual (2023-2025)",
                      color_discrete_sequence=bcg_colors)
        fig2.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

    with tabs[2]:
        st.header("3. Emisor que más participación ha perdido en los últimos 2 años")
        total_ini = df_2y.loc[fecha_ini].sum()
        total_fin = df_2y.loc[fecha_fin].sum()
        part_ini = df_2y.loc[fecha_ini] / total_ini
        part_fin = df_2y.loc[fecha_fin] / total_fin
        cambio_part = (part_fin - part_ini).dropna().sort_values()
        top_perdida = cambio_part.head(1)
        emisor_pierde = top_perdida.index[0]
        tarjetas_ini_p = int(df_2y.loc[fecha_ini, emisor_pierde])
        tarjetas_fin_p = int(df_2y.loc[fecha_fin, emisor_pierde])
        st.metric("Mayor pérdida de participación", emisor_pierde,
                  f"{top_perdida.iloc[0] * 100:.2f} pp ({tarjetas_ini_p:,} → {tarjetas_fin_p:,})")
        fig3 = px.bar(cambio_part.head(10).reset_index(),
                      x="index", y=0,
                      labels={"index": "Emisor", 0: "Cambio en Participación (%)"},
                      title="Top 10 emisores que más participación han perdido (2023-2025)",
                      color_discrete_sequence=bcg_colors)
        fig3.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
        fig3.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)

    with tabs[3]:
        st.header("4. Evolución de participación de mercado del Banco de Chile")
        df["Total"] = df.drop(columns=["Fecha"]).sum(axis=1)
        df["Participacion_BChile"] = df["Banco de Chile"] / df["Total"] * 100
        fig4 = px.line(df, x="Fecha", y="Participacion_BChile", title="Participación de mercado del Banco de Chile (%)",
                      labels={"Participacion_BChile": "Participación (%)"},
                      color_discrete_sequence=bcg_colors)
        st.plotly_chart(fig4, use_container_width=True)

    with tabs[4]:
        st.header("5. Comparación de tarjetas vigentes con competidores")
        df_comp = df[["Fecha", "Banco de Chile", "Banco Santander", "Banco Falabella", "Banco del Estado de Chile"]].copy()
        df_comp = df_comp.melt(id_vars="Fecha", var_name="Emisor", value_name="Tarjetas")
        fig5 = px.line(df_comp, x="Fecha", y="Tarjetas", color="Emisor",
                       title="Comparación temporal de tarjetas entre principales bancos",
                       color_discrete_sequence=bcg_colors)
        st.plotly_chart(fig5, use_container_width=True)

    with tabs[5]:
        st.header("6. Ranking de crecimiento últimos 12 meses")
        df_last12 = df[df["Fecha"] >= df["Fecha"].max() - pd.DateOffset(months=12)].copy()
        df_growth = df_last12.set_index("Fecha").iloc[-1] - df_last12.set_index("Fecha").iloc[0]
        df_growth = df_growth.dropna().sort_values(ascending=False).reset_index()
        df_growth.columns = ["Emisor", "Crecimiento"]
        fig6 = px.bar(df_growth.head(10), x="Emisor", y="Crecimiento", text="Crecimiento",
                      title="Top 10 emisores con mayor crecimiento en últimos 12 meses",
                      color_discrete_sequence=bcg_colors)
        fig6.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        fig6.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig6, use_container_width=True)

    with tabs[6]:
        st.header("7. Alertas de caída mensual en Banco de Chile")
        df_bch = df[["Fecha", "Banco de Chile"]].dropna()
        df_bch["Variacion"] = df_bch["Banco de Chile"].diff()
        df_alerta = df_bch[df_bch["Variacion"] < 0]
        fig7 = px.line(df_bch, x="Fecha", y="Banco de Chile",
                       title="Evolución de tarjetas del Banco de Chile con alertas de caída",
                       color_discrete_sequence=bcg_colors)
        fig7.add_scatter(x=df_alerta["Fecha"], y=df_alerta["Banco de Chile"], mode="markers",
                         marker=dict(size=10, color="red"), name="Caída")
        st.plotly_chart(fig7, use_container_width=True)

    with tabs[7]:
        st.header("8. Apertura del market share por emisor (Waterfall)")
        ultima_fecha = df["Fecha"].max()
        total_ult = df[df["Fecha"] == ultima_fecha].drop(columns=["Fecha"]).sum(axis=1).values[0]
        participaciones = df[df["Fecha"] == ultima_fecha].drop(columns=["Fecha"]).T
        participaciones.columns = ["Tarjetas"]
        participaciones = participaciones.sort_values(by="Tarjetas", ascending=False).dropna()
        participaciones["Participacion"] = participaciones["Tarjetas"] / total_ult * 100

        fig8 = go.Figure(go.Waterfall(
            name="Participación",
            orientation="v",
            measure=["relative"] * len(participaciones) + ["total"],
            x=participaciones.index.tolist() + ["Total"],
            y=participaciones["Participacion"].tolist() + [0],
            connector={"line": {"color": "gray"}}
        ))

        fig8.update_layout(title="Desglose del market share por emisor (%) - Última fecha",
                           yaxis_title="Participación (%)",
                           xaxis_title="Emisor")
        st.plotly_chart(fig8, use_container_width=True)

else:
    st.info("Por favor sube un archivo Excel para comenzar el análisis.")
