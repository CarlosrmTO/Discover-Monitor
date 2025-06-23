from datetime import datetime

def get_elpais_sitemap():
    """Generate the El País sitemap URL for the current month and year.
    
    Returns:
        str: Formatted sitemap URL for the current month and year.
    """
    now = datetime.now()
    return f"https://elpais.com/sitemaps/{now.year}/{now.month:02d}/sitemap.xml"

# List of websites to monitor with verified sitemaps
WEBSITES = [
    {
        'name': 'The Objective',
        'url': 'https://theobjective.com',
        'sitemap': 'https://theobjective.com/sitemap_index.xml',
        'is_own_site': True
    },
    {
        'name': 'El Mundo',
        'url': 'https://www.elmundo.es',
        'sitemap': 'https://www.elmundo.es/sitemaps/sitemap.xml',
        'is_own_site': False
    },
    {
        'name': 'El Confidencial',
        'url': 'https://www.elconfidencial.com',
        'sitemap': 'https://www.elconfidencial.com/sitemap_index.xml',
        'is_own_site': False
    },
    {
        'name': 'Infobae',
        'url': 'https://www.infobae.com/espana',
        'sitemap': 'https://www.infobae.com/arc/outboundfeeds/sitemap2/',
        'is_own_site': False
    },
    {
        'name': 'Libertad Digital',
        'url': 'https://www.libertaddigital.com',
        'sitemap': 'https://www.libertaddigital.com/sitemap.xml',
        'is_own_site': False
    },
    {
        'name': 'Vozpópuli',
        'url': 'https://www.vozpopuli.com',
        'sitemap': 'https://www.vozpopuli.com/sitemaps/sitemap-news2.xml',
        'is_own_site': False
    },
    {
        'name': 'Público',
        'url': 'https://www.publico.es',
        'sitemap': 'https://www.publico.es/sitemap-index.xml',
        'is_own_site': False
    },
    {
        'name': 'OKDiario',
        'url': 'https://okdiario.com',
        'sitemap': 'https://okdiario.com/sitemap_index.xml',
        'is_own_site': False
    },
    {
        'name': 'El País',
        'url': 'https://elpais.com',
        'sitemap': get_elpais_sitemap(),
        'is_own_site': False,
        'dynamic_sitemap': True
    },
    {
        'name': 'eldiario.es',
        'url': 'https://www.eldiario.es',
        'sitemap': 'https://www.eldiario.es/sitemap_index_25b87.xml',
        'is_own_site': False
    },
    {
        'name': 'La Razón',
        'url': 'https://www.larazon.es',
        'sitemap': 'https://www.larazon.es/sitemaps/news.xml',
        'is_own_site': False
    },
    {
        'name': '20 Minutos',
        'url': 'https://www.20minutos.es',
        'sitemap': 'https://www.20minutos.es/sitemap-index.xml',
        'is_own_site': False
    },
    {
        'name': 'ABC',
        'url': 'https://www.abc.es',
        'sitemap': 'https://www.abc.es/sitemap.xml',
        'is_own_site': False
    },
    {
        'name': 'El Español',
        'url': 'https://www.elespanol.com',
        'sitemap': 'https://www.elespanol.com/sitemap_index.xml',
        'is_own_site': False
    },
    {
        'name': 'El Periódico',
        'url': 'https://www.elperiodico.com',
        'sitemap': 'https://www.elperiodico.com/es/google-news.xml',
        'is_own_site': False
    }
]

# Google Search Console API settings
GSC_CREDENTIALS_FILE = 'credentials.json'  # You'll need to create this file with your GSC credentials
GSC_PROPERTY = 'sc-domain:theobjective.com'  # Your Search Console property

# Data storage
DATA_DIR = 'data'
ARTICLES_FILE = f"{DATA_DIR}/articles.csv"
DISCOVER_DATA_FILE = f"{DATA_DIR}/discover_data.csv"