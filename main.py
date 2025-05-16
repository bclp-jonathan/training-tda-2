import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tarjetas de Crédito en Chile", layout="wide")
st.title("Análisis de Tarjetas de Crédito por Emisor en Chile")

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

    # Sección 1: Emisor con más tarjetas hoy
    st.header("1. Emisor con más tarjetas al día de hoy")
    latest = df.iloc[-1]
    fecha_actual = latest["Fecha"]
    emisores = pd.Series(latest[1:].dropna().values, index=latest[1:].dropna().index.astype(str))
    emisores_sorted = emisores.sort_values(ascending=False)
    st.metric("Emisor con más tarjetas", emisores_sorted.index[0], f"{int(emisores_sorted.iloc[0]):,} tarjetas")
    fig1 = px.bar(emisores_sorted.head(10), labels={"value": "Tarjetas Vigentes", "index": "Emisor"},
                  title=f"Top 10 emisores con más tarjetas ({fecha_actual.date()})")
    st.plotly_chart(fig1, use_container_width=True)

    # Sección 2: Emisor que más ha crecido en 2 años
    st.header("2. Emisor que más ha crecido en los últimos 2 años")
    fecha_ini = pd.Timestamp("2023-02-01")
    fecha_fin = pd.Timestamp("2025-02-01")
    df_2y = df[df["Fecha"].isin([fecha_ini, fecha_fin])].set_index("Fecha")
    crecimiento = df_2y.loc[fecha_fin] - df_2y.loc[fecha_ini]
    crecimiento = crecimiento.dropna().sort_values(ascending=False)
    st.metric("Mayor crecimiento absoluto", crecimiento.index[0], f"+{int(crecimiento.max()):,} tarjetas")
    fig2 = px.bar(crecimiento.head(10), labels={"value": "Crecimiento de Tarjetas", "index": "Emisor"},
                  title="Top 10 emisores con mayor crecimiento (2023-2025)")
    st.plotly_chart(fig2, use_container_width=True)

    # Sección 3: Emisor que más participación ha perdido
    st.header("3. Emisor que más participación ha perdido en los últimos 2 años")
    total_ini = df_2y.loc[fecha_ini].sum()
    total_fin = df_2y.loc[fecha_fin].sum()
    part_ini = df_2y.loc[fecha_ini] / total_ini
    part_fin = df_2y.loc[fecha_fin] / total_fin
    cambio_part = (part_fin - part_ini).dropna().sort_values()
    st.metric("Mayor pérdida de participación", cambio_part.index[0], f"{cambio_part.min() * 100:.2f} pp")
    fig3 = px.bar(cambio_part.head(10) * 100, labels={"value": "Cambio en Participación (%)", "index": "Emisor"},
                  title="Top 10 emisores que más participación han perdido (2023-2025)")
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("Por favor sube un archivo Excel para comenzar el análisis.")
