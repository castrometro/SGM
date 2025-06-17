import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_control_gestion(df, titulo):
    df = df.sort_values("Categoria")
    df["Porcentaje"] = pd.to_numeric(df["Porcentaje"], errors="coerce")
    fig = px.pie(df, names="Categoria", values="Porcentaje", hole=0.5,
                 color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_layout(height=400, title=titulo, legend_title_text="Categoría")
    return fig

def plot_facturacion_sector_industrial(df):
    df["%"] = df["%"].str.replace("%", "").astype(float)
    fig = px.pie(df, names="Sector Industrial", values="%", title="Facturación por Sector Industrial 2023",
                 color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_traces(textinfo="percent+label", hovertemplate="%{label}: %{value:,.0f}%")
    fig.update_layout(height=500)
    return fig

def plot_resumen_ingresos_anual(df):
    df["% Mensual"] = df["% Mensual"].str.replace("%", "").astype(float)
    df["Presupuesto Mensual"] = df["Presupuesto Mensual"].astype(float)
    df["Real Mensual"] = df["Real Mensual"].astype(float)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Mes"], y=df["Presupuesto Mensual"], name="Presupuesto", marker_color="crimson"))
    fig.add_trace(go.Bar(x=df["Mes"], y=df["Real Mensual"], name="Real", marker_color="lightgray"))
    fig.add_trace(go.Scatter(x=df["Mes"], y=df["% Mensual"], name="% Mensual", yaxis="y2", mode="lines+markers+text",
                             text=[f"{v:.0f}%" for v in df["% Mensual"]], textposition="top center",
                             line=dict(color="deepskyblue", width=2)))
    fig.update_layout(
        xaxis=dict(title="Meses"),
        yaxis=dict(title="UF"),
        yaxis2=dict(title="% Mensual", overlaying="y", side="right", range=[0, 180], tickformat="%"),
        barmode="group",
        height=500
    )
    return fig
