import streamlit as st
import pandas as pd
import plotly.express as px

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

    # Selector de análisis
    seccion = st.sidebar.radio("Selecciona una sección:", [
        "1. Emisor con más tarjetas al día de hoy",
        "2. Emisor que más ha crecido en los últimos 2 años",
        "3. Emisor que más participación ha perdido en los últimos 2 años"
    ])

    if seccion == "1. Emisor con más tarjetas al día de hoy":
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

    elif seccion == "2. Emisor que más ha crecido en los últimos 2 años":
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

    elif seccion == "3. Emisor que más participación ha perdido en los últimos 2 años":
        st.header("3. Emisor que más participación ha perdido en los últimos 2 años")
        fecha_ini = pd.Timestamp("2023-02-01")
        fecha_fin = pd.Timestamp("2025-02-01")
        df_2y = df[df["Fecha"].isin([fecha_ini, fecha_fin])].set_index("Fecha")
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

else:
    st.info("Por favor sube un archivo Excel para comenzar el análisis.")
