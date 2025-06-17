#!/usr/bin/env python3
"""
Script para verificar las rutas de los sitemaps de los sitios web.
"""
import json
import os
import time
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

# Lista de sitios web para verificar con sus sitemaps conocidos
SITES = [
    {"url": "https://theobjective.com", "sitemap": "https://theobjective.com/sitemap_index.xml"},
    {"url": "https://www.elmundo.es", "sitemap": "https://www.elmundo.es/mapas/sitemap-index.xml"},
    {"url": "https://www.elconfidencial.com", "sitemap": "https://www.elconfidencial.com/sitemap_index.xml"},
    {"url": "https://www.infobae.com/espana/", "sitemap": "https://www.infobae.com/espana/sitemap.xml"},
    {"url": "https://www.libertaddigital.com", "sitemap": "https://www.libertaddigital.com/sitemap_index.xml"},
    {"url": "https://www.vozpopuli.com", "sitemap": "https://www.vozpopuli.com/sitemap_index.xml"},
    {"url": "https://www.publico.es", "sitemap": "https://www.publico.es/sitemap_index.xml"},
    {"url": "https://okdiario.com", "sitemap": "https://okdiario.com/sitemap_index.xml"},
    {"url": "https://www.eldiario.es", "sitemap": "https://www.eldiario.es/sitemap_index.xml"},
    {"url": "https://www.larazon.es", "sitemap": "https://www.larazon.es/sitemap_index.xml"},
    {"url": "https://www.20minutos.es", "sitemap": "https://www.20minutos.es/sitemap_index.xml"},
    {"url": "https://www.abc.es", "sitemap": "https://www.abc.es/sitemap.xml"},
    {"url": "https://www.elespanol.com", "sitemap": "https://www.elespanol.com/sitemap_index.xml"},
    {"url": "https://www.elperiodico.com", "sitemap": "https://www.elperiodico.com/sitemap_index.xml"}
]

# Headers para simular un navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

# Posibles ubicaciones de sitemaps (en orden de prioridad)
SITEMAP_PATHS = [
    "/sitemap_index.xml",
    "/sitemap-index.xml",
    "/sitemap.xml",
    "/sitemap_news.xml",
    "/sitemap-news.xml",
    "/sitemap/sitemap_index.xml",
    "/sitemap/sitemap-index.xml",
    "/sitemap/sitemap.xml",
    "/sitemaps/sitemap_index.xml",
    "/sitemaps/sitemap-index.xml",
    "/sitemaps/sitemap.xml",
    "/sitemap_es.xml",
    "/sitemap-es.xml",
    "/sitemap_news_es.xml",
    "/sitemap-news-es.xml",
    "/mapas/sitemap-index.xml"  # Usado por El Mundo
]

def get_robots_txt(session, base_url):
    """Obtiene el contenido de robots.txt"""
    try:
        robots_url = urljoin(base_url, '/robots.txt')
        response = session.get(robots_url, timeout=10, allow_redirects=True)
        response.raise_for_status()
        if 'text/plain' in response.headers.get('content-type', '').lower():
            return response.text
        return None
    except Exception as e:
        print(f"  Error al obtener robots.txt para {base_url}: {str(e)}")
        return None

def find_sitemap_in_robots(robots_content):
    """Busca la ruta del sitemap en el contenido de robots.txt"""
    if not robots_content:
        return None
    
    for line in robots_content.split('\n'):
        line = line.strip()
        if line.lower().startswith('sitemap:'):
            parts = line.split(':', 1)
            if len(parts) > 1:
                return parts[1].strip()
    return None

def check_sitemap_url(session, base_url, path):
    """Verifica si una URL de sitemap es accesible"""
    sitemap_url = urljoin(base_url, path)
    try:
        # Primero intentamos con HEAD para ahorrar ancho de banda
        try:
            response = session.head(sitemap_url, timeout=5, allow_redirects=True)
            if response.status_code != 200:
                return None
                
            # Verificar que la respuesta parece ser un XML
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' in content_type or 'text/xml' in content_type:
                return sitemap_url
        except:
            pass
        
        # Si HEAD falla o no está claro, intentamos con GET
        try:
            response = session.get(sitemap_url, timeout=10, allow_redirects=True, stream=True)
            if response.status_code == 200:
                # Verificar los primeros bytes para ver si es XML
                chunk = response.raw.read(100).decode('utf-8', 'ignore').lower()
                if '<?xml' in chunk or '<sitemapindex' in chunk or '<urlset' in chunk:
                    return sitemap_url
        except:
            pass
            
    except Exception as e:
        print(f"  Error al verificar {sitemap_url}: {str(e)}")
    return None

def find_sitemap(session, site_info):
    """Busca el sitemap de un sitio web"""
    base_url = site_info['url']
    known_sitemap = site_info.get('sitemap')
    
    print(f"\nBuscando sitemap para: {base_url}")
    
    # 0. Verificar si el sitemap conocido funciona
    if known_sitemap:
        if check_sitemap_url(session, base_url, known_sitemap):
            print(f"  Sitemap conocido funciona: {known_sitemap}")
            return known_sitemap
        print(f"  El sitemap conocido no funciona: {known_sitemap}")
    
    # 1. Buscar en robots.txt
    print("  Buscando en robots.txt...")
    robots_content = get_robots_txt(session, base_url)
    if robots_content:
        sitemap_url = find_sitemap_in_robots(robots_content)
        if sitemap_url:
            print(f"  Encontrado en robots.txt: {sitemap_url}")
            return sitemap_url
    
    # 2. Probar rutas comunes de sitemaps
    print("  Probando rutas comunes de sitemaps...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for path in SITEMAP_PATHS:
            futures.append(executor.submit(check_sitemap_url, session, base_url, path))
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                print(f"  Sitemap encontrado: {result}")
                return result
    
    # 3. Si no se encuentra, devolver la ruta por defecto o la conocida
    default_sitemap = known_sitemap or urljoin(base_url, "/sitemap.xml")
    print(f"  Usando sitemap por defecto: {default_sitemap}")
    return default_sitemap

def save_results(results):
    """Guarda los resultados en un archivo"""
    try:
        # Crear directorio data si no existe
        os.makedirs('data', exist_ok=True)
        
        # Guardar resultados en formato de texto
        txt_path = os.path.join('data', 'sitemap_results.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("=== Resultados de búsqueda de sitemaps ===\n\n")
            for result in results:
                f.write(f"{result['url']}: {result['sitemap']}\n")
        
        # Guardar resultados en formato JSON para uso posterior
        json_path = os.path.join('data', 'sitemaps.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\nLos resultados se han guardado en {txt_path} y {json_path}")
        return True
    except Exception as e:
        print(f"Error al guardar los resultados: {str(e)}")
        return False

def main():
    """Función principal"""
    session = requests.Session()
    session.headers.update(HEADERS)
    session.max_redirects = 3
    
    results = []
    
    print("=== Verificando sitemaps ===")
    
    # Usar una barra de progreso manual para mejor control
    with tqdm(total=len(SITES), desc="Procesando sitios") as pbar:
        for site_info in SITES:
            try:
                site_url = site_info['url']
                pbar.set_description(f"Procesando {site_url}")
                
                # Intentar encontrar el sitemap
                sitemap = find_sitemap(session, site_info)
                
                # Extraer nombre del sitio
                domain = urlparse(site_url).netloc
                name = domain.replace('www.', '').split('.')[0].capitalize()
                
                # Agregar a resultados
                results.append({
                    'url': site_url.rstrip('/'),
                    'sitemap': sitemap,
                    'name': name
                })
                
                # Pequeña pausa para no sobrecargar
                time.sleep(1)
                
            except Exception as e:
                print(f"\nError procesando {site_info.get('url')}: {str(e)}")
            finally:
                pbar.update(1)
    
    # Mostrar resumen
    print("\n=== Resumen ===")
    success = sum(1 for r in results if r['sitemap'])
    print(f"Sitios procesados: {len(results)}")
    print(f"Sitemaps encontrados: {success}")
    print(f"Sitemaps no encontrados: {len(results) - success}")
    
    # Mostrar sitemaps encontrados
    print("\n=== Sitemaps encontrados ===")
    for result in results:
        if result['sitemap']:
            print(f"{result['url']}: {result['sitemap']}")
    
    # Mostrar sitios sin sitemap
    no_sitemap = [r['url'] for r in results if not r['sitemap']]
    if no_sitemap:
        print("\n=== Sitios sin sitemap encontrado ===")
        for url in no_sitemap:
            print(f"- {url}")
    
    # Generar configuración para config.py
    print("\n=== Configuración para config.py ===")
    print("WEBSITES = [")
    for result in results:
        site_url = result['url']
        is_own = site_url == 'https://theobjective.com'
        own_site_line = ",\n        'is_own_site': True" if is_own else ""
        print(f"    {{'name': '{result['name']}', 'url': '{site_url}', 'sitemap': '{result['sitemap']}'{own_site_line}}},")
    print("]")
    
    # Guardar resultados
    save_results(results)

if __name__ == "__main__":
    main()
