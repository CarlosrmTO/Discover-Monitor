import os
import sys
import json
import time
import logging
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from tqdm import tqdm
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Asegurarse de que el directorio padre esté en el path
sys.path.append(str(Path(__file__).parent.parent))

from discover_monitor.config import WEBSITES, DATA_DIR, ARTICLES_FILE, DISCOVER_DATA_FILE

# Asegurarse de que el directorio de datos exista
os.makedirs(DATA_DIR, exist_ok=True)

# Configuración de logging
log_file = os.path.join(DATA_DIR, 'discover_monitor.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constantes
SITEMAP_NS = {
    'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    'news': 'http://www.google.com/schemas/sitemap-news/0.9',
    'image': 'http://www.google.com/schemas/sitemap-image/1.1'
}
MAX_WORKERS = 5  # Número máximo de workers para procesamiento paralelo
REQUEST_TIMEOUT = 15  # Segundos

@dataclass
class Article:
    """Clase para representar un artículo extraído."""
    url: str
    title: str
    section: str
    description: str
    source: str
    is_own_site: bool
    published_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    image_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convierte el artículo a diccionario para su almacenamiento."""
        return {
            'url': self.url,
            'title': self.title,
            'section': self.section,
            'description': self.description,
            'source': self.source,
            'is_own_site': self.is_own_site,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'image_url': self.image_url,
            'timestamp': datetime.now().isoformat()
        }

def _parse_date(date_str: str) -> Optional[datetime]:
    """Parsea una cadena de fecha a un objeto datetime.
    
    Args:
        date_str: Cadena de fecha en varios formatos posibles
        
    Returns:
        Objeto datetime o None si no se pudo parsear
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    # Eliminar espacios en blanco al inicio y final
    date_str = date_str.strip()
    
    # Lista de formatos de fecha comunes a probar
    date_formats = [
        "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 con timezone
        "%Y-%m-%dT%H:%M:%S",    # ISO 8601 sin timezone
        "%Y-%m-%d %H:%M:%S",    # Formato SQL
        "%Y-%m-%d",             # Solo fecha
        "%d/%m/%Y %H:%M:%S",    # Formato europeo con tiempo
        "%d/%m/%Y",             # Formato europeo sin tiempo
        "%m/%d/%Y %H:%M:%S",    # Formato americano con tiempo
        "%m/%d/%Y",             # Formato americano sin tiempo
        "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822 con timezone
        "%a, %d %b %Y %H:%M:%S",      # RFC 2822 sin timezone
        "%a %b %d %H:%M:%S %Y",       # Formato de fecha de Unix
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Intentar con dateutil.parser si está disponible
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except (ImportError, ValueError):
        pass
    
    logger.warning(f"No se pudo parsear la fecha: {date_str}")
    return None

class DiscoverMonitor:
    def __init__(self, output_file: str = None, max_workers: int = 5):
        """Inicializa el monitor de Discover.
        
        Args:
            output_file: Ruta al archivo de salida para guardar los artículos.
            max_workers: Número máximo de workers para el ThreadPoolExecutor.
        """
        self.output_file = output_file or os.path.join(DATA_DIR, 'articles.csv')
        self.max_workers = max_workers
        self.articles = []  # Lista para almacenar los artículos encontrados
        self.processed_urls = set()  # Conjunto para URLs ya procesadas
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.setup_directories()

    def setup_directories(self):
        """Crea los directorios necesarios si no existen."""
        os.makedirs(DATA_DIR, exist_ok=True)
        
    def _save_articles(self, file_path: str = None) -> None:
        """Guarda los artículos en un archivo CSV.
        
        Args:
            file_path: Ruta del archivo donde guardar los artículos. Si es None, se usa self.output_file.
        """
        if not file_path:
            file_path = self.output_file
            
        if not self.articles:
            logger.warning("No hay artículos para guardar")
            return
            
        try:
            # Convertir los artículos a diccionarios
            articles_data = [article.to_dict() for article in self.articles]
            
            # Crear DataFrame y guardar en CSV
            df = pd.DataFrame(articles_data)
            
            # Asegurarse de que el directorio existe
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Guardar el archivo
            df.to_csv(file_path, index=False, encoding='utf-8')
            logger.info(f"Artículos guardados en {file_path}")
            
        except Exception as e:
            logger.error(f"Error al guardar los artículos: {str(e)}")
            raise
        
    def _fetch_sitemap(self, url: str) -> Optional[str]:
        """Descarga el contenido de un sitemap.
        
        Args:
            url: URL del sitemap a descargar
            
        Returns:
            Contenido del sitemap como string o None si hay un error
        """
        try:
            logger.info(f"Descargando sitemap: {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error al descargar el sitemap {url}: {str(e)}")
            return None
            
    def _parse_article_from_url(self, url: str) -> Optional[Article]:
        """Extrae metadatos de un artículo a partir de su URL.
        
        Args:
            url: URL del artículo a analizar
            
        Returns:
            Objeto Article con los metadatos extraídos o None si hay un error
        """
        try:
            logger.info(f"Analizando artículo: {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer título (usando varios selectores comunes)
            title = None
            title_selectors = [
                'h1',
                'h1.article-title',
                'h1.entry-title',
                'h1.post-title',
                'title',
                'meta[property="og:title"]',
                'meta[name="title"]'
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element and element.get_text().strip():
                    title = element.get_text().strip()
                    if selector.startswith('meta'):
                        title = element.get('content', '').strip()
                    if title:
                        break
            
            # Extraer descripción
            description = None
            desc_selectors = [
                'meta[property="og:description"]',
                'meta[name="description"]',
                'meta[itemprop="description"]',
                'p.article-summary',
                'div.article-content > p',
                'div.entry-content > p'
            ]
            
            for selector in desc_selectors:
                element = soup.select_one(selector)
                if element:
                    if selector.startswith('meta'):
                        description = element.get('content', '').strip()
                    else:
                        description = element.get_text().strip()
                    if description:
                        break
            
            # Extraer imagen
            image_url = None
            img_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                'img.article-image',
                'img.wp-post-image',
                'figure img',
                'div.article-image img'
            ]
            
            for selector in img_selectors:
                element = soup.select_one(selector)
                if element:
                    if selector.startswith('meta'):
                        image_url = element.get('content', '')
                    else:
                        image_url = element.get('src', '')
                    if image_url:
                        break
            
            # Extraer sección (de la URL o de la navegación)
            section = 'General'
            try:
                # Intentar extraer de la URL
                path_parts = urlparse(url).path.strip('/').split('/')
                if len(path_parts) > 1 and path_parts[0]:
                    section = path_parts[0].capitalize()
            except Exception as e:
                logger.warning(f"No se pudo extraer la sección de la URL {url}: {str(e)}")
            
            # Crear y devolver el artículo
            return Article(
                url=url,
                title=title or 'Sin título',
                section=section,
                description=description or '',
                source=urlparse(url).netloc,
                is_own_site=False,
                image_url=image_url
            )
            
        except Exception as e:
            logger.error(f"Error al analizar el artículo {url}: {str(e)}")
            return None

    def _parse_sitemap_index(self, xml_content: str) -> List[str]:
        """Parsea un índice de sitemap y devuelve las URLs de los sitemaps."""
        try:
            # Registrar los primeros 200 caracteres del contenido para depuración
            logger.debug(f"Parsing sitemap index. Content start: {xml_content[:200]}...")
            
            # Intentar con namespaces primero
            root = ET.fromstring(xml_content)
            
            # Intentar diferentes patrones de búsqueda
            sitemap_locs = []
            
            # Patrón 1: Con namespace
            sitemap_locs = root.findall('.//sitemap:loc', SITEMAP_NS)
            
            # Si no se encontraron con namespace, intentar sin namespace
            if not sitemap_locs:
                logger.debug("No se encontraron sitemaps con namespace, intentando sin namespace...")
                sitemap_locs = root.findall('.//loc')
            
            # Si aún no hay resultados, buscar en todo el documento
            if not sitemap_locs:
                logger.debug("Búsqueda exhaustiva de sitemaps...")
                sitemap_locs = root.findall('.//{*}loc') or root.findall('.//loc')
            
            # Filtrar y limpiar las URLs
            urls = []
            for loc in sitemap_locs:
                if loc is not None and loc.text and loc.text.strip():
                    url = loc.text.strip()
                    # Asegurarse de que la URL sea absoluta
                    if not url.startswith(('http://', 'https://')):
                        logger.warning(f"URL relativa encontrada en sitemap: {url}")
                        continue
                    urls.append(url)
            
            logger.info(f"Se encontraron {len(urls)} URLs de sitemap en el índice")
            return urls
            
        except ET.ParseError as e:
            logger.error(f"Error de parseo XML en el sitemap índice: {str(e)}")
            # Intentar con BeautifulSoup como respaldo
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(xml_content, 'lxml')
                urls = [loc.text.strip() for loc in soup.find_all('loc') if loc and loc.text.strip()]
                logger.info(f"Se encontraron {len(urls)} URLs de sitemap usando BeautifulSoup")
                return urls
            except Exception as bs_e:
                logger.error(f"Error al analizar con BeautifulSoup: {str(bs_e)}")
                return []
        except Exception as e:
            logger.error(f"Error inesperado al analizar índice de sitemap: {str(e)}", exc_info=True)
            return []

    def _parse_news_sitemap(self, xml_content: str) -> List[Article]:
        """Parsea un sitemap de noticias y devuelve información de artículos."""
        articles = []
        try:
            logger.debug("Analizando sitemap de noticias...")
            
            # Registrar los primeros 200 caracteres del contenido para depuración
            logger.debug(f"Contenido del sitemap de noticias (inicio): {xml_content[:200]}...")
            
            # Usar BeautifulSoup para un análisis más flexible
            soup = BeautifulSoup(xml_content, 'lxml-xml')
            
            # Buscar todas las etiquetas url
            url_tags = soup.find_all('url')
            logger.info(f"Se encontraron {len(url_tags)} etiquetas 'url' en el sitemap de noticias")
            
            for url_tag in url_tags:
                try:
                    # Extraer la URL
                    loc_tag = url_tag.find('loc')
                    if not loc_tag or not loc_tag.text.strip():
                        continue
                    
                    url = loc_tag.text.strip()
                    
                    # Extraer metadatos de noticias
                    news_tag = url_tag.find('news:news')
                    if not news_tag:
                        logger.debug(f"No se encontró etiqueta de noticias para {url}")
                        continue
                    
                    # Extraer título
                    title_tag = news_tag.find('news:title')
                    title = title_tag.text.strip() if title_tag and title_tag.text else 'Sin título'
                    
                    # Extraer fecha de publicación
                    pub_date = None
                    pub_date_tag = news_tag.find('news:publication_date')
                    if pub_date_tag and pub_date_tag.text:
                        try:
                            # Manejar diferentes formatos de fecha
                            pub_date_str = pub_date_tag.text.strip()
                            # Intentar con diferentes formatos de fecha
                            for fmt in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S', 
                                       '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                                try:
                                    pub_date = datetime.strptime(pub_date_str, fmt)
                                    break
                                except ValueError:
                                    continue
                        except Exception as e:
                            logger.warning(f"No se pudo analizar la fecha de publicación para {url}: {str(e)}")
                    
                    # Extraer imagen si está disponible
                    image_url = None
                    image_tag = url_tag.find('image:image')
                    if image_tag:
                        image_loc = image_tag.find('image:loc')
                        if image_loc and image_loc.text:
                            image_url = image_loc.text.strip()
                    
                    # Extraer sección de la URL
                    parsed_url = urlparse(url)
                    section = parsed_url.path.strip('/').split('/')[0] if parsed_url.path else 'home'
                    
                    # Crear objeto Article
                    article = Article(
                        url=url,
                        title=title,
                        section=section,
                        description='',  # Se completará más tarde
                        source='',  # Se establecerá más adelante
                        is_own_site=False,  # Se ajustará según el sitio
                        published_date=pub_date,
                        image_url=image_url
                    )
                    
                    articles.append(article)
                    logger.debug(f"Artículo procesado: {title} - {url}")
                    
                except Exception as e:
                    logger.warning(f"Error procesando entrada de noticia: {str(e)}", exc_info=True)
            
            logger.info(f"Se procesaron {len(articles)} artículos del sitemap de noticias")
            return articles
            
        except Exception as e:
            logger.error(f"Error inesperado al analizar sitemap de noticias: {str(e)}", exc_info=True)
            return []

    def _parse_standard_sitemap(self, xml_content: str) -> List[Article]:
        """Parsea un sitemap estándar y devuelve información de URLs."""
        articles = []
        try:
            logger.debug("Analizando sitemap estándar...")
            
            # Usar BeautifulSoup para un análisis más flexible
            soup = BeautifulSoup(xml_content, 'lxml-xml')
            
            # Buscar todas las etiquetas url
            url_tags = soup.find_all('url')
            logger.info(f"Se encontraron {len(url_tags)} etiquetas 'url' en el sitemap estándar")
            
            for url_tag in url_tags:
                try:
                    # Extraer la URL
                    loc_tag = url_tag.find('loc')
                    if not loc_tag or not loc_tag.text.strip():
                        continue
                        
                    url = loc_tag.text.strip()
                    
                    # Extraer fecha de última modificación
                    lastmod = None
                    lastmod_tag = url_tag.find('lastmod')
                    if lastmod_tag and lastmod_tag.text:
                        try:
                            # Intentar con diferentes formatos de fecha
                            lastmod_str = lastmod_tag.text.strip()
                            for fmt in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S', 
                                       '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                                try:
                                    lastmod = datetime.strptime(lastmod_str, fmt)
                                    break
                                except ValueError:
                                    continue
                        except Exception as e:
                            logger.debug(f"No se pudo analizar la fecha de modificación para {url}: {str(e)}")
                    
                    # Extraer título si está disponible
                    title = ''
                    title_tag = url_tag.find('title') or url_tag.find('news:title')
                    if title_tag and title_tag.text:
                        title = title_tag.text.strip()
                    
                    # Extraer descripción si está disponible
                    description = ''
                    desc_tag = url_tag.find('description') or url_tag.find('news:description')
                    if desc_tag and desc_tag.text:
                        description = desc_tag.text.strip()
                    
                    # Extraer imagen si está disponible
                    image_url = None
                    image_tag = url_tag.find('image:image') or url_tag.find('image')
                    if image_tag:
                        image_loc = image_tag.find('image:loc') or image_tag.find('loc')
                        if image_loc and image_loc.text:
                            image_url = image_loc.text.strip()
                    
                    # Extraer sección de la URL
                    parsed_url = urlparse(url)
                    section = parsed_url.path.strip('/').split('/')[0] if parsed_url.path else 'home'
                    
                    # Crear objeto Article
                    article = Article(
                        url=url,
                        title=title,
                        section=section,
                        description=description,
                        source='',  # Se establecerá más adelante
                        is_own_site=False,  # Se ajustará según el sitio
                        last_modified=lastmod
                    )
                    
                    articles.append(article)
                    logger.debug(f"URL procesada: {url}")
                    
                except Exception as e:
                    logger.warning(f"Error procesando entrada de sitemap: {str(e)}", exc_info=True)
            
            logger.info(f"Se procesaron {len(articles)} URLs del sitemap estándar")
            return articles
            
        except Exception as e:
            logger.error(f"Error inesperado al analizar sitemap estándar: {str(e)}", exc_info=True)
            return []

    def fetch_sitemap(self, sitemap_url: str) -> List[Dict]:
        """
        Obtiene y analiza un sitemap, manejando tanto índices como sitemaps regulares.
        Devuelve una lista de artículos con metadatos básicos.
        """
        try:
            logger.info(f"Fetching sitemap: {sitemap_url}")
            response = self.session.get(sitemap_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            
            # Verificar si es un índice de sitemap
            if 'sitemapindex' in response.text.lower() or 'sitemapindex' in content_type:
                logger.info(f"Detected sitemap index: {sitemap_url}")
                sitemap_urls = self._parse_sitemap_index(response.text)
                
                # Procesar cada sitemap en el índice
                articles = []
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = [
                        executor.submit(self.fetch_sitemap, sitemap_url)
                        for sitemap_url in sitemap_urls[:20]  # Limitar para no sobrecargar
                    ]
                    
                    for future in as_completed(futures):
                        try:
                            articles.extend(future.result())
                        except Exception as e:
                            logger.error(f"Error processing sitemap: {str(e)}")
                
                return articles
                
            # Verificar si es un sitemap de noticias
            elif 'newssitemap' in response.text.lower() or 'newssitemap' in content_type:
                logger.info(f"Detected news sitemap: {sitemap_url}")
                return self._parse_news_sitemap(response.text)
                
            # Asumir que es un sitemap estándar
            else:
                logger.info(f"Detected standard sitemap: {sitemap_url}")
                return self._parse_standard_sitemap(response.text)
                
        except requests.RequestException as e:
            logger.error(f"Error fetching sitemap {sitemap_url}: {str(e)}")
            return []
        except ET.ParseError as e:
            logger.error(f"Error parsing XML from {sitemap_url}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error processing {sitemap_url}: {str(e)}")
            return []

    def extract_article_info(self, article: Article) -> Optional[Article]:
        """
        Extrae información detallada de un artículo a partir de su URL.
        
        Args:
            article: Instancia de Article con la URL y metadatos básicos
            
        Returns:
            Article actualizado con la información extraída, o None si hay un error
        """
        try:
            logger.debug(f"Extracting article info from: {article.url}")
            
            # Configurar headers para parecer un navegador real
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Realizar la petición con manejo de redirecciones
            response = self.session.get(
                article.url, 
                headers=headers,
                timeout=REQUEST_TIMEOUT, 
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Verificar que el contenido sea HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"Skipping non-HTML content at {article.url} (Content-Type: {content_type})")
                return None
                
            # Parsear el HTML con BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extraer título si no lo tenemos
            if not article.title or article.title == 'Sin título':
                title_tag = soup.find('title')
                if title_tag:
                    article.title = title_tag.get_text(strip=True)
                else:
                    # Intentar encontrar el título en meta tags
                    og_title = soup.find('meta', property='og:title')
                    if og_title and og_title.get('content'):
                        article.title = og_title['content'].strip()
                    else:
                        article.title = 'Sin título'
            
            # Extraer descripción
            description = ''
            meta_desc = soup.find('meta', {'name': 'description'}) or \
                       soup.find('meta', {'property': 'og:description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc['content'].strip()
            article.description = description
            
            # Extraer imagen destacada si no la tenemos
            if not article.image_url:
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    article.image_url = og_image['content']
                else:
                    # Intentar encontrar la primera imagen grande
                    img = soup.find('img', {'src': True})
                    if img:
                        article.image_url = urljoin(article.url, img['src'])
            
            # Extraer fecha de publicación si no la tenemos
            if not article.published_date:
                # Buscar en meta tags comunes de fecha
                date_selectors = [
                    {'name': 'article:published_time'},
                    {'property': 'article:published_time'},
                    {'name': 'date'},
                    {'property': 'og:published_time'},
                    {'name': 'publish-date'},
                    {'name': 'pubdate'},
                    {'class': 'date-published'},
                    {'class': 'entry-date'},
                    {'class': 'published'},
                ]
                
                for selector in date_selectors:
                    try:
                        date_tag = soup.find(attrs=selector)
                        if date_tag and date_tag.get('content'):
                            date_str = date_tag['content']
                            article.published_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        elif date_tag and date_tag.text.strip():
                            # Intentar parsear la fecha del texto
                            date_str = date_tag.text.strip()
                            # Aquí podrías agregar más formatos de fecha según sea necesario
                            for fmt in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d', '%d/%m/%Y'):
                                try:
                                    article.published_date = datetime.strptime(date_str, fmt)
                                    break
                                except ValueError:
                                    continue
                            if article.published_date:
                                break
                    except Exception as e:
                        logger.debug(f"Error parsing date with selector {selector}: {str(e)}")
                        continue
            
            logger.info(f"Successfully extracted article: {article.title}")
            return article
            
        except requests.RequestException as e:
            logger.error(f"Error fetching article {article.url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing {article.url}: {str(e)}", exc_info=True)
            return None

    def load_existing_data(self) -> pd.DataFrame:
        """Load existing articles data from CSV if it exists."""
        if os.path.exists(ARTICLES_FILE):
            return pd.read_csv(ARTICLES_FILE)
        return pd.DataFrame()

    def save_articles(self, articles: List[Dict]):
        """Save articles to CSV, appending to existing data."""
        df = pd.DataFrame(articles)
        if not df.empty:
            if os.path.exists(ARTICLES_FILE):
                existing_df = pd.read_csv(ARTICLES_FILE)
                df = pd.concat([existing_df, df]).drop_duplicates(subset=['url'], keep='first')
            df.to_csv(ARTICLES_FILE, index=False)

    def monitor_websites(self, max_articles_per_site: int = 50) -> None:
        """
        Monitorea todos los sitios web configurados en busca de nuevos artículos.
        
        Args:
            max_articles_per_site: Número máximo de artículos a procesar por sitio
        """
        logger.info("Iniciando monitoreo de sitios web...")
        
        # Crear directorio de datos si no existe
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Cargar datos existentes
        existing_articles = self.load_existing_data()
        existing_urls = set(existing_articles['url'].tolist()) if not existing_articles.empty else set()
        
        # Estadísticas
        total_new = 0
        
        # Procesar cada sitio web
        for site in tqdm(WEBSITES, desc="Sitios web"):
            try:
                site_name = site['name']
                logger.info(f"Procesando sitio: {site_name}")
                
                # Obtener artículos del sitemap
                articles = self.fetch_sitemap(site['sitemap'])
                
                if not articles:
                    logger.warning(f"No se encontraron artículos en el sitemap de {site_name}")
                    continue
                
                # Establecer información del sitio en los artículos
                for article in articles:
                    article.source = site_name
                    article.is_own_site = site.get('is_own_site', False)
                
                # Filtrar artículos nuevos
                new_articles = [
                    article for article in articles 
                    if article.url not in existing_urls
                ][:max_articles_per_site]
                
                if not new_articles:
                    logger.info(f"No hay artículos nuevos en {site_name}")
                    continue
                
                # Procesar artículos en paralelo
                processed_articles = []
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    # Crear tareas para extraer información de cada artículo
                    future_to_article = {
                        executor.submit(self.extract_article_info, article): article
                        for article in new_articles
                    }
                    
                    # Procesar resultados a medida que estén disponibles
                    for future in tqdm(
                        as_completed(future_to_article),
                        total=len(new_articles),
                        desc=f"Procesando {site_name}",
                        leave=False
                    ):
                        article = future_to_article[future]
                        try:
                            result = future.result()
                            if result:
                                processed_articles.append(result)
                                existing_urls.add(result.url)  # Evitar duplicados en esta ejecución
                        except Exception as e:
                            logger.error(f"Error procesando artículo {article.url}: {str(e)}")
                
                # Guardar artículos procesados
                if processed_articles:
                    self.save_articles(processed_articles)
                    total_new += len(processed_articles)
                    logger.info(f"Añadidos {len(processed_articles)} nuevos artículos de {site_name}")
                
            except Exception as e:
                logger.error(f"Error monitoreando {site.get('name', 'sitio desconocido')}: {str(e)}", exc_info=True)
        
        logger.info(f"Monitoreo completado. Se añadieron {total_new} artículos nuevos en total.")

    def run(self, max_articles_per_site: int = 50):
        """
        Ejecuta el proceso de monitoreo completo.
        
        Args:
            max_articles_per_site: Número máximo de artículos a procesar por sitio
        """
        start_time = datetime.now()
        logger.info("=" * 80)
        logger.info(f"Iniciando ejecución del monitor de Discover - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        try:
            # Ejecutar el monitoreo de sitios web
            self.monitor_websites(max_articles_per_site)
            
            # Calcular tiempo de ejecución
            execution_time = datetime.now() - start_time
            logger.info("=" * 80)
            logger.info(f"Monitoreo completado en {execution_time}")
            logger.info("=" * 80)
            
        except KeyboardInterrupt:
            logger.warning("Ejecución interrumpida por el usuario")
        except Exception as e:
            logger.critical(f"Error crítico durante la ejecución: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    monitor = DiscoverMonitor()
    monitor.run()