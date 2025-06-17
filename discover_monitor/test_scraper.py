import os
import sys
import logging
from pathlib import Path

# Asegurarse de que el directorio padre esté en el path
sys.path.append(str(Path(__file__).parent.parent))

from discover_monitor.scraper import DiscoverMonitor
from discover_monitor.config import WEBSITES

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_scraper.log'),
        logging.StreamHandler()
    ]
)

def main():
    # Usar solo los primeros 2 sitios para prueba
    test_sites = WEBSITES[:2]
    
    # Configurar el monitor con los sitios de prueba
    monitor = DiscoverMonitor()
    
    # Probar con un máximo de 3 artículos por sitio
    monitor.run(max_articles_per_site=3)

if __name__ == "__main__":
    # Crear directorio de datos si no existe
    os.makedirs('data', exist_ok=True)
    
    # Ejecutar prueba
    main()
