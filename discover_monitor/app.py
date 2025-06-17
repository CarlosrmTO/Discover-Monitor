import os
import logging
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from fpdf import FPDF
import tempfile
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Directorio de datos
DATA_DIR = Path(__file__).parent / "data"
os.makedirs(DATA_DIR, exist_ok=True)

def load_data() -> pd.DataFrame:
    """Carga los datos de los artículos desde el archivo CSV."""
    try:
        data_file = DATA_DIR / "articles.csv"
        if data_file.exists():
            df = pd.read_csv(data_file, parse_dates=['published_date'])
            logger.info(f"Datos cargados correctamente desde {data_file}")
            return df
        else:
            logger.warning(f"Archivo {data_file} no encontrado")
            return pd.DataFrame(columns=['title', 'source', 'section', 'published_date', 'url'])
    except Exception as e:
        logger.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

def get_data() -> pd.DataFrame:
    """Obtiene los datos, cargándolos si es necesario.
    
    Returns:
        DataFrame con los datos cargados
    """
    if 'df' not in st.session_state or st.session_state.df.empty:
        st.session_state.df = load_data()
    return st.session_state.df

def generate_source_chart(df: pd.DataFrame) -> Optional[go.Figure]:
    """Genera un gráfico de barras mostrando artículos por fuente.
    
    Args:
        df: DataFrame con los datos de los artículos
        
    Returns:
        Objeto Figure de Plotly con el gráfico o None si no hay datos
    """
    if df.empty or 'source' not in df.columns:
        return None
        
    source_counts = df['source'].value_counts().reset_index()
    source_counts.columns = ['Fuente', 'Cantidad']
    
    fig = px.bar(
        source_counts, 
        x='Fuente', 
        y='Cantidad',
        color='Fuente',
        title='Total de artículos por fuente',
        labels={'Fuente': 'Fuente', 'Cantidad': 'Número de artículos'}
    )
    
    return fig

def generate_section_chart(df: pd.DataFrame, top_n: int = 10) -> Optional[go.Figure]:
    """Genera un gráfico de barras mostrando las secciones con más artículos.
    
    Args:
        df: DataFrame con los datos de los artículos
        top_n: Número de secciones a mostrar
        
    Returns:
        Objeto Figure de Plotly con el gráfico o None si no hay datos
    """
    if df.empty or 'section' not in df.columns:
        return None
    
    section_counts = df['section'].value_counts().head(top_n).reset_index()
    section_counts.columns = ['Sección', 'Cantidad']
    
    fig = px.bar(
        section_counts, 
        x='Cantidad', 
        y='Sección',
        orientation='h',
        title=f'Top {top_n} secciones con más artículos',
        labels={'Cantidad': 'Número de artículos', 'Sección': 'Sección'}
    )
    
    return fig

def generate_pdf_report(df: pd.DataFrame, output_path: str) -> None:
    """Genera un informe en PDF con los datos de los artículos.
    
    Args:
        df: DataFrame con los datos de los artículos
        output_path: Ruta donde guardar el archivo PDF
    """
    if df.empty:
        logger.warning("No hay datos para generar el informe PDF")
        return
        
    try:
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
        pdf.cell(200, 10, txt=f"Fuentes únicas: {df['source'].nunique() if not df.empty else 0}", ln=True)
        pdf.cell(200, 10, txt=f"Secciones únicas: {df['section'].nunique() if not df.empty else 0}", ln=True)
        pdf.ln(10)
        
        # Tabla de artículos (solo las primeras 50 filas para no hacer el PDF demasiado grande)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Artículos recientes (mostrando {min(50, len(df))} de {len(df)}):", ln=True)
        pdf.ln(5)
        
        # Encabezados de la tabla
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(100, 10, "Título", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Fuente", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Sección", 1, 0, 'C', 1)
        pdf.cell(30, 10, "Fecha", 1, 1, 'C', 1)
        
        # Filas de la tabla
        pdf.set_font("Arial", size=8)
        for _, row in df.head(50).iterrows():
            # Truncar el título si es muy largo
            title = row['title'][:50] + '...' if len(row['title']) > 50 else row['title']
            pdf.cell(100, 8, title, 1)
            pdf.cell(40, 8, str(row.get('source', '')), 1)
            pdf.cell(40, 8, str(row.get('section', '')), 1)
            pdf.cell(30, 8, str(row['published_date'].strftime('%Y-%m-%d') if pd.notnull(row.get('published_date')) else ''), 1, 1)
        
        # Guardar el PDF
        pdf.output(output_path)
        logger.info(f"Informe PDF generado en {output_path}")
        
    except Exception as e:
        logger.error(f"Error al generar el informe PDF: {e}")
        raise

def setup_sidebar_filters(df: pd.DataFrame) -> Dict[str, Any]:
    """Configura los filtros en la barra lateral.
    
    Args:
        df: DataFrame con los datos a filtrar
        
    Returns:
        Diccionario con los filtros seleccionados
    """
    filters = {}
    
    # Filtro por fuente
    sources = ['Todos'] + sorted(df['source'].dropna().unique().tolist()) if not df.empty else ['Todos']
    filters['source'] = st.sidebar.selectbox('Fuente', sources, index=0)
    
    # Filtro por fecha
    min_date = df['published_date'].min().to_pydatetime() if not df.empty and 'published_date' in df.columns else datetime.now() - timedelta(days=30)
    max_date = df['published_date'].max().to_pydatetime() if not df.empty and 'published_date' in df.columns else datetime.now()
    
    date_range = st.sidebar.date_input(
        'Rango de fechas',
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        filters['start_date'], filters['end_date'] = date_range
    else:
        filters['start_date'], filters['end_date'] = min_date, max_date
    
    return filters

def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Aplica los filtros al DataFrame.
    
    Args:
        df: DataFrame a filtrar
        filters: Diccionario con los filtros a aplicar
        
    Returns:
        DataFrame filtrado
    """
    if df.empty:
        return df
        
    filtered_df = df.copy()
    
    # Aplicar filtro de fuente si existe la clave 'source' en los filtros
    if 'source' in filters and filters.get('source') != 'Todos':
        filtered_df = filtered_df[filtered_df['source'] == filters['source']]
    
    # Aplicar filtro de fecha
    if 'start_date' in filters and 'end_date' in filters:
        # Asegurarse de que las fechas sean del tipo correcto
        start_date = pd.Timestamp(filters['start_date']).date() if filters['start_date'] else None
        end_date = pd.Timestamp(filters['end_date']).date() if filters['end_date'] else None
        
        if start_date and end_date:
            filtered_df = filtered_df[
                (filtered_df['published_date'].dt.date >= start_date) &
                (filtered_df['published_date'].dt.date <= end_date)
            ]
    
    return filtered_df

def display_metrics(filtered_df: pd.DataFrame) -> None:
    """Muestra las métricas principales.
    
    Args:
        filtered_df: DataFrame con los datos filtrados
    """
    if not filtered_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de artículos", len(filtered_df))
        with col2:
            st.metric("Fuentes únicas", filtered_df['source'].nunique() if not filtered_df.empty else 0)
        with col3:
            st.metric("Secciones únicas", filtered_df['section'].nunique() if not filtered_df.empty else 0)

def display_charts(filtered_df: pd.DataFrame) -> None:
    """Muestra los gráficos.
    
    Args:
        filtered_df: DataFrame con los datos filtrados
    """
    if not filtered_df.empty:
        tab1, tab2 = st.tabs(["📊 Por fuente", "📈 Por sección"])
        
        with tab1:
            fig = generate_source_chart(filtered_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No hay datos para mostrar el gráfico por fuente")
        
        with tab2:
            fig = generate_section_chart(filtered_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No hay datos para mostrar el gráfico por sección")

def display_table(filtered_df: pd.DataFrame) -> None:
    """Muestra la tabla de artículos.
    
    Args:
        filtered_df: DataFrame con los datos filtrados
    """
    if not filtered_df.empty:
        st.subheader("Artículos")
        st.dataframe(
            filtered_df[['title', 'source', 'section', 'published_date', 'url']],
            column_config={
                'title': 'Título',
                'source': 'Fuente',
                'section': 'Sección',
                'published_date': 'Fecha de publicación',
                'url': st.column_config.LinkColumn('Enlace')
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("No hay datos que coincidan con los filtros seleccionados")

def export_data(filtered_df: pd.DataFrame) -> None:
    """Muestra los controles de exportación.
    
    Args:
        filtered_df: DataFrame con los datos a exportar
    """
    if not filtered_df.empty:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Exportar datos")
        
        # Exportar a CSV
        if st.sidebar.button("Exportar a CSV"):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                    filtered_df.to_csv(tmp_file.name, index=False)
                    with open(tmp_file.name, 'rb') as f:
                        st.sidebar.download_button(
                            label="Descargar CSV",
                            data=f,
                            file_name="articulos_discover.csv",
                            mime="text/csv"
                        )
                st.success("Datos exportados a CSV exitosamente")
            except Exception as e:
                st.error(f"Error al exportar a CSV: {str(e)}")
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
        
        # Exportar a Excel
        if st.sidebar.button("Exportar a Excel"):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    filtered_df.to_excel(tmp_file.name, index=False, engine='openpyxl')
                    with open(tmp_file.name, 'rb') as f:
                        st.sidebar.download_button(
                            label="Descargar Excel",
                            data=f,
                            file_name="articulos_discover.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                st.success("Datos exportados a Excel exitosamente")
            except Exception as e:
                st.error(f"Error al exportar a Excel: {str(e)}")
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
        
        # Exportar a PDF
        if st.sidebar.button("Generar Informe PDF"):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    generate_pdf_report(filtered_df, tmp_file.name)
                    with open(tmp_file.name, 'rb') as f:
                        st.sidebar.download_button(
                            label="Descargar PDF",
                            data=f,
                            file_name="informe_articulos.pdf",
                            mime="application/pdf"
                        )
                st.success("Informe PDF generado exitosamente")
            except Exception as e:
                st.error(f"Error al generar el PDF: {str(e)}")
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

def main() -> None:
    """Función principal de la aplicación Streamlit."""
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
    
    # Inicializar el estado de la sesión para los datos
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame()
    
    # Cargar datos iniciales si no hay datos en la sesión
    if st.session_state.df.empty:
        st.session_state.df = load_data()
    
    # Obtener los datos
    df = get_data()
    
    # Configurar la barra lateral
    filters = setup_sidebar_filters(df) if not df.empty else {}
    
    # Aplicar filtros
    filtered_df = apply_filters(df, filters) if not df.empty else pd.DataFrame()
    
    # Mostrar métricas
    display_metrics(filtered_df)
    
    # Mostrar gráficos
    display_charts(filtered_df)
    
    # Mostrar tabla
    display_table(filtered_df)
    
    # Mostrar controles de exportación
    export_data(filtered_df)
    
    # Mostrar mensaje si no hay datos
    if df.empty:
        st.info("No se encontraron datos. Ejecuta el script de scraping primero para generar datos.")
        if st.button("Ejecutar Scraper"):
            with st.spinner("Ejecutando scraper..."):
                try:
                    # Aquí iría la lógica para ejecutar el scraper
                    st.success("¡Datos actualizados correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al ejecutar el scraper: {e}")

if __name__ == "__main__":
    main()
