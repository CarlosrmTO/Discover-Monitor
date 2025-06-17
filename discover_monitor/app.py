import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from fpdf import FPDF
import tempfile
import base64
from pathlib import Path

# Configuración de la página
st.set_page_config(
    page_title="Monitor de Descubrimiento",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título de la aplicación
st.title("📊 Monitor de Contenidos en Discover")
st.markdown("---")

# Cargar datos
def load_data():
    """Carga los datos de los artículos desde el archivo CSV."""
    data_file = Path(__file__).parent / "data" / "articles.csv"
    if data_file.exists():
        df = pd.read_csv(data_file, parse_dates=['timestamp'])
        # Asegurarse de que la columna de fecha esté en formato datetime
        if 'published_date' in df.columns:
            df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')
        return df
    return pd.DataFrame()

# Cargar datos
df = load_data()

# Sidebar para filtros
st.sidebar.title("Filtros")

# Filtro por fuente
if not df.empty:
    sources = ['Todos'] + sorted(df['source'].dropna().unique().tolist())
    selected_source = st.sidebar.selectbox('Fuente', sources, index=0)
    
    if selected_source != 'Todos':
        df = df[df['source'] == selected_source]

# Filtro por fecha
if not df.empty and 'published_date' in df.columns:
    min_date = df['published_date'].min().date()
    max_date = df['published_date'].max().date()
    
    date_range = st.sidebar.date_input(
        'Rango de fechas',
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df['published_date'].dt.date >= start_date) & 
                (df['published_date'].dt.date <= end_date)]

# Mostrar datos
if df.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    # Mostrar estadísticas rápidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de artículos", len(df))
    with col2:
        st.metric("Fuentes únicas", df['source'].nunique())
    with col3:
        st.metric("Secciones únicas", df['section'].nunique())
    
    # Pestañas para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["📊 Resumen", "📰 Artículos", "📈 Análisis"])
    
    with tab1:
        st.subheader("Resumen de datos")
        
        # Gráfico de artículos por fuente
        st.markdown("### Artículos por fuente")
        source_counts = df['source'].value_counts().reset_index()
        source_counts.columns = ['Fuente', 'Cantidad']
        
        fig1 = px.bar(
            source_counts, 
            x='Fuente', 
            y='Cantidad',
            color='Fuente',
            title='Total de artículos por fuente'
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Gráfico de artículos por sección (top 10)
        st.markdown("### Top 10 secciones con más artículos")
        section_counts = df['section'].value_counts().head(10).reset_index()
        section_counts.columns = ['Sección', 'Cantidad']
        
        fig2 = px.bar(
            section_counts, 
            x='Cantidad', 
            y='Sección',
            orientation='h',
            title='Top 10 secciones con más artículos',
            color='Sección'
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        # Mostrar tabla con los artículos
        st.subheader("Lista de artículos")
        st.dataframe(
            df[['title', 'source', 'section', 'published_date']].sort_values('published_date', ascending=False),
            column_config={
                'title': 'Título',
                'source': 'Fuente',
                'section': 'Sección',
                'published_date': 'Fecha de publicación'
            },
            hide_index=True,
            use_container_width=True
        )
    
    with tab3:
        st.subheader("Análisis detallado")
        
        # Gráfico de artículos por sección por fuente
        st.markdown("### Artículos por sección por fuente")
        if not df.empty and 'source' in df.columns and 'section' in df.columns:
            source_section = df.groupby(['source', 'section']).size().reset_index(name='count')
            
            fig3 = px.bar(
                source_section,
                x='source',
                y='count',
                color='section',
                title='Distribución de artículos por sección y fuente',
                labels={'source': 'Fuente', 'count': 'Número de artículos', 'section': 'Sección'}
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        # Gráfico de tendencia temporal
        st.markdown("### Tendencias temporales")
        if not df.empty and 'published_date' in df.columns:
            # Agrupar por fecha y fuente
            df_daily = df.copy()
            df_daily['date'] = df_daily['published_date'].dt.date
            daily_counts = df_daily.groupby(['date', 'source']).size().reset_index(name='count')
            
            fig4 = px.line(
                daily_counts,
                x='date',
                y='count',
                color='source',
                title='Tendencia de publicaciones por día',
                labels={'date': 'Fecha', 'count': 'Número de artículos', 'source': 'Fuente'}
            )
            st.plotly_chart(fig4, use_container_width=True)
    
    # Sección de exportación
    st.sidebar.markdown("---")
    st.sidebar.subheader("Exportar datos")
    
    # Función para crear un enlace de descarga
    def get_download_link(file_path, file_label):
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">Descargar {file_label}</a>'
        return href
    
    # Exportar a CSV
    if st.sidebar.button("Exportar a CSV"):
        csv = df.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="Descargar CSV",
            data=csv,
            file_name=f"discover_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Exportar a Excel
    if st.sidebar.button("Exportar a Excel"):
        excel_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        with pd.ExcelWriter(excel_file.name, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Articulos')
        
        with open(excel_file.name, 'rb') as f:
            excel_data = f.read()
        
        st.sidebar.download_button(
            label="Descargar Excel",
            data=excel_data,
            file_name=f"discover_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Exportar a PDF
    if st.sidebar.button("Exportar a PDF"):
        # Crear un PDF temporal
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Título
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Informe de Artículos en Discover", ln=True, align='C')
        pdf.ln(10)
        
        # Fecha del informe
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.ln(10)
        
        # Estadísticas
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Estadísticas:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Total de artículos: {len(df)}", ln=True)
        pdf.cell(200, 10, txt=f"Fuentes únicas: {df['source'].nunique()}", ln=True)
        pdf.cell(200, 10, txt=f"Secciones únicas: {df['section'].nunique()}", ln=True)
        pdf.ln(10)
        
        # Tabla de artículos (solo las primeras 50 filas para no hacer el PDF demasiado grande)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Artículos recientes (mostrando {min(50, len(df))} de {len(df)}):", ln=True)
        pdf.ln(5)
        
        # Configurar la tabla
        pdf.set_font("Arial", 'B', 10)
        col_widths = [100, 30, 30, 30]  # Ajustar según sea necesario
        
        # Encabezados de la tabla
        headers = ['Título', 'Fuente', 'Sección', 'Fecha']
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, txt=header, border=1)
        pdf.ln()
        
        # Filas de la tabla
        pdf.set_font("Arial", size=8)
        for _, row in df.head(50).iterrows():
            # Ajustar el texto para que quepa en la celda
            title = row['title'][:40] + '...' if len(str(row['title'])) > 40 else row['title']
            source = str(row['source'])[:15] + '...' if len(str(row['source'])) > 15 else row['source']
            section = str(row['section'])[:15] + '...' if len(str(row['section'])) > 15 else row['section']
            date = str(row['published_date']).split(' ')[0] if 'published_date' in row and pd.notna(row['published_date']) else 'N/A'
            
            pdf.cell(col_widths[0], 10, txt=str(title), border=1)
            pdf.cell(col_widths[1], 10, txt=str(source), border=1)
            pdf.cell(col_widths[2], 10, txt=str(section), border=1)
            pdf.cell(col_widths[3], 10, txt=str(date), border=1)
            pdf.ln()
        
        # Guardar el PDF temporal
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf.output(pdf_file.name)
        
        # Crear botón de descarga
        with open(pdf_file.name, "rb") as f:
            pdf_data = f.read()
        
        st.sidebar.download_button(
            label="Descargar PDF",
            data=pdf_data,
            file_name=f"discover_report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

# Mensaje de ayuda si no hay datos
if df.empty:
    st.info("No se encontraron datos. Ejecuta el script de scraping primero para generar datos.")
    if st.button("Ejecutar Scraper"):
        with st.spinner("Ejecutando scraper..."):
            import subprocess
            result = subprocess.run(["python", "-m", "discover_monitor.test_scraper"], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("¡Scraper ejecutado exitosamente!")
                st.experimental_rerun()
            else:
                st.error(f"Error al ejecutar el scraper: {result.stderr}")
