"""Tests for the check_sitemaps module."""
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest
import requests

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import the module
from discover_monitor.check_sitemaps import (
    get_robots_txt,
    find_sitemap_in_robots,
    check_sitemap_url,
    find_sitemap,
    save_results,
    main,
    SITEMAP_PATHS,
    SITES
)

# Test data
SAMPLE_ROBOTS_TXT = """
User-agent: *
Disallow: /admin/
Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap_news.xml
"""

# Fixtures
@pytest.fixture
def mock_session():
    """Create a mock session for requests."""
    with patch('discover_monitor.check_sitemaps.requests.Session') as mock_session:
        yield mock_session.return_value

# Test cases
def test_get_robots_txt_success(mock_session):
    """Test successful retrieval of robots.txt."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = SAMPLE_ROBOTS_TXT
    mock_response.headers = {'content-type': 'text/plain'}
    mock_session.get.return_value = mock_response
    
    # Execute
    result = get_robots_txt(mock_session, "https://example.com")
    
    # Verify
    assert result == SAMPLE_ROBOTS_TXT
    mock_session.get.assert_called_once_with("https://example.com/robots.txt", timeout=10, allow_redirects=True)

def test_get_robots_txt_error(mock_session):
    """Test handling of errors when fetching robots.txt."""
    # Setup
    mock_session.get.side_effect = requests.RequestException("Connection error")
    
    # Execute
    result = get_robots_txt(mock_session, "https://example.com")
    
    # Verify
    assert result is None


def test_find_sitemap_in_robots_found():
    """Test finding sitemap URL in robots.txt."""
    # Execute
    result = find_sitemap_in_robots(SAMPLE_ROBOTS_TXT)
    
    # Verify
    assert result == "https://example.com/sitemap.xml"

def test_find_sitemap_in_robots_not_found():
    """Test when no sitemap is found in robots.txt."""
    # Execute
    result = find_sitemap_in_robots("User-agent: *\nDisallow: /admin/")
    
    # Verify
    assert result is None

def test_check_sitemap_url_valid(mock_session):
    """Test checking a valid sitemap URL."""
    # Setup
    mock_session.head.return_value.status_code = 200
    mock_session.head.return_value.headers = {'content-type': 'application/xml'}
    
    # Execute
    result = check_sitemap_url(mock_session, "https://example.com", "/sitemap.xml")
    
    # Verify
    assert result == "https://example.com/sitemap.xml"
    mock_session.head.assert_called_once()

def test_check_sitemap_url_falls_back_to_get(mock_session):
    """Test that GET is used when HEAD fails."""
    # Setup
    mock_session.head.side_effect = requests.RequestException("HEAD failed")
    mock_session.get.return_value.status_code = 200
    mock_session.get.return_value.raw.read.return_value = b'<?xml version="1.0"?>\n<urlset>'
    
    # Execute
    result = check_sitemap_url(mock_session, "https://example.com", "/sitemap.xml")
    
    # Verify
    assert result == "https://example.com/sitemap.xml"
    mock_session.get.assert_called_once()

def test_find_sitemap_known_good(mock_session):
    """Test finding sitemap when a known good URL is provided."""
    # Setup
    site_info = {
        'url': 'https://example.com',
        'sitemap': 'https://example.com/sitemap.xml'
    }
    
    with patch('discover_monitor.check_sitemaps.check_sitemap_url') as mock_check:
        mock_check.return_value = 'https://example.com/sitemap.xml'
        
        # Execute
        result = find_sitemap(mock_session, site_info)
        
        # Verify
        assert result == 'https://example.com/sitemap.xml'
        mock_check.assert_called_once_with(mock_session, 'https://example.com', 
                                         'https://example.com/sitemap.xml')

def test_find_sitemap_via_robots(mock_session, capsys):
    """Test finding sitemap via robots.txt."""
    # Setup
    site_info = {'url': 'https://example.com'}
    
    with patch('discover_monitor.check_sitemaps.get_robots_txt') as mock_get_robots, \
         patch('discover_monitor.check_sitemaps.find_sitemap_in_robots') as mock_find, \
         patch('discover_monitor.check_sitemaps.check_sitemap_url') as mock_check, \
         patch('discover_monitor.check_sitemaps.SITEMAP_PATHS', []):  # Avoid testing common paths
        
        # Setup mocks
        mock_get_robots.return_value = SAMPLE_ROBOTS_TXT
        mock_find.return_value = 'https://example.com/sitemap.xml'
        mock_check.return_value = 'https://example.com/sitemap.xml'
        
        # Execute
        result = find_sitemap(mock_session, site_info)
        
        # Verify
        captured = capsys.readouterr()
        assert "Buscando sitemap para: https://example.com" in captured.out
        assert "Buscando en robots.txt..." in captured.out
        assert "Encontrado en robots.txt: https://example.com/sitemap.xml" in captured.out
        assert result == 'https://example.com/sitemap.xml'
        mock_get_robots.assert_called_once_with(mock_session, 'https://example.com')
        mock_find.assert_called_once_with(SAMPLE_ROBOTS_TXT)
        # check_sitemap_url should not be called in this test case
        mock_check.assert_not_called()

@patch('discover_monitor.check_sitemaps.check_sitemap_url')
@patch('discover_monitor.check_sitemaps.find_sitemap_in_robots')
@patch('discover_monitor.check_sitemaps.get_robots_txt')
@patch('discover_monitor.check_sitemaps.SITEMAP_PATHS', ['/sitemap_index.xml'])
def test_find_sitemap_common_paths(mock_get_robots, mock_find, mock_check, mock_session, capsys):
    """Test finding sitemap by checking common paths."""
    # Setup
    site_info = {'url': 'https://example.com'}
    
    # Setup mocks
    mock_get_robots.return_value = None  # No robots.txt
    mock_find.return_value = None  # No sitemap found in robots.txt
    mock_check.return_value = 'https://example.com/sitemap_index.xml'
    
    # Execute
    result = find_sitemap(mock_session, site_info)
    
    # Verify the result is as expected
    assert result == 'https://example.com/sitemap_index.xml'
    
    # Verify the output messages
    captured = capsys.readouterr()
    assert "Buscando sitemap para: https://example.com" in captured.out
    assert "Buscando en robots.txt..." in captured.out
    assert "Probando rutas comunes de sitemaps..." in captured.out
    assert "Sitemap encontrado: https://example.com/sitemap_index.xml" in captured.out
    
    # Verify check_sitemap_url was called with the correct arguments
    mock_check.assert_called_once_with(
        mock_session, 
        'https://example.com', 
        '/sitemap_index.xml'
    )

def test_save_results_success(tmp_path):
    """Test successful saving of results."""
    # Setup
    results = [
        {'url': 'https://example1.com', 'sitemap': 'https://example1.com/sitemap.xml'},
        {'url': 'https://example2.com', 'sitemap': None}
    ]
    output_dir = tmp_path / 'data'
    output_dir.mkdir()
    
    # Execute
    with patch('os.makedirs'), \
         patch('builtins.open', mock_open()) as mock_file:
        result = save_results(results)
    
    # Verify
    assert result is True
    assert mock_file.call_count == 2  # Called for txt and json files

def test_main_success(mock_session, tmp_path):
    """Test main function execution."""
    # Setup
    test_args = ["check_sitemaps.py", "--output", str(tmp_path / 'output.json')]
    
    with patch('sys.argv', test_args), \
         patch('discover_monitor.check_sitemaps.requests.Session') as mock_sess, \
         patch('discover_monitor.check_sitemaps.find_sitemap') as mock_find, \
         patch('json.dump') as mock_json_dump:
        
        # Configure mocks
        mock_sess.return_value = mock_session
        mock_find.return_value = 'https://example.com/sitemap.xml'
        
        # Execute
        main()
        
        # Verify
        assert mock_find.call_count == len(SITES)
        assert mock_json_dump.called

# Test edge cases
def test_check_sitemap_url_none_path(mock_session):
    """Test check_sitemap_url with None path."""
    assert check_sitemap_url(mock_session, "https://example.com", None) is None

def test_find_sitemap_empty_site_info(mock_session):
    """Test find_sitemap with empty site info."""
    with pytest.raises(KeyError):
        find_sitemap(mock_session, {})
