from setuptools import setup, find_packages

setup(
    name="discover_monitor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'pandas>=1.3.0',
        'requests>=2.26.0',
        'beautifulsoup4>=4.10.0',
        'lxml>=4.6.3',
        'python-dotenv>=0.19.0',
        'google-api-python-client>=2.0.0',
        'google-auth-oauthlib>=0.4.0',
        'google-auth-httplib2>=0.1.0',
        'schedule>=1.1.0',
        'tqdm>=4.62.0',
        'python-dateutil>=2.8.2',
        'plotly>=5.0.0',
        'streamlit>=1.33.0',
        'fpdf>=1.7.2',
    ],
    python_requires='>=3.7',
)
