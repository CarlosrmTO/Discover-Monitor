# Discover Monitor

Aplicación para monitorear contenido en Google Discover para theobjective.com y sitios competidores.

## Características

- Extracción de artículos de sitemaps de noticias
- Interfaz web interactiva con Streamlit
- Visualización de datos con gráficos interactivos
- Exportación a múltiples formatos (CSV, Excel, PDF)
- Monitoreo de tendencias y estadísticas

## Requisitos

- Python 3.7+
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd discover-monitor
   ```

2. Crear y activar un entorno virtual (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Ejecutar el scraper para obtener datos:
   ```bash
   python -m discover_monitor.test_scraper
   ```

2. Iniciar la interfaz web:
   ```bash
   streamlit run discover_monitor/app.py
   ```

3. Abrir el navegador en la URL mostrada (generalmente http://localhost:8501)

## Estructura del Proyecto

```
discover_monitor/
├── __init__.py
├── app.py              # Aplicación Streamlit
├── scraper.py          # Lógica de scraping
├── test_scraper.py     # Script de prueba
├── config.py           # Configuración
└── check_sitemaps.py   # Utilidad para verificar sitemaps
```

## Próximos Pasos

- [ ] Implementar pruebas unitarias y de integración
- [ ] Configurar CI/CD con GitHub Actions
- [ ] Mejorar la documentación
- [ ] Añadir más fuentes de datos

## Licencia

MIT
