"""Tests for the main module."""
import os
import sys
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import the module
from discover_monitor.main import check_requirements, parse_arguments, main
from discover_monitor.scraper import DiscoverMonitor

# Test data
SAMPLE_CREDENTIALS = '''{
  "type": "service_account",
  "project_id": "test-project"
}'''

# Fixtures
@pytest.fixture
def setup_environment(monkeypatch, tmp_path):
    """Set up a clean test environment."""
    # Create a temporary directory for the test
    test_dir = tmp_path / "test_discover_monitor"
    test_dir.mkdir()
    
    # Create a temporary credentials file
    creds_file = test_dir / "test_credentials.json"
    creds_file.write_text(SAMPLE_CREDENTIALS)
    
    # Create a temporary data directory
    data_dir = test_dir / "data"
    data_dir.mkdir()
    
    # Set up environment variables
    monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS', str(creds_file))
    
    # Change to the test directory
    monkeypatch.chdir(test_dir)
    
    # Mock WEBSITES in config
    with patch('discover_monitor.config.WEBSITES', [{
        'name': 'Test Site',
        'url': 'https://example.com',
        'sitemap': 'https://example.com/sitemap.xml',
        'is_own_site': True
    }]):
        yield test_dir, creds_file, data_dir

# Test cases for check_requirements
def test_check_requirements_with_env_var(setup_environment, capsys):
    """Test check_requirements when credentials are provided via environment variable."""
    test_dir, creds_file, data_dir = setup_environment
    
    # The fixture already sets up the environment variable
    check_requirements()
    
    # Check that the data directory was created
    assert data_dir.exists()
    
    # Verify no warnings were printed
    captured = capsys.readouterr()
    assert "Warning:" not in captured.out

def test_check_requirements_without_creds(monkeypatch, tmp_path, capsys):
    """Test check_requirements when no credentials are found."""
    # Set up a clean environment without credentials
    test_dir = tmp_path / "test_no_creds"
    test_dir.mkdir()
    data_dir = test_dir / "data"
    
    # Remove any credentials from environment
    monkeypatch.delenv('GOOGLE_APPLICATION_CREDENTIALS', raising=False)
    
    # Change to the test directory
    monkeypatch.chdir(test_dir)
    
    # Mock os.path.exists to return False for the credentials file
    with patch('os.path.exists', return_value=False):
        check_requirements()
    
    # Check that the data directory was created
    assert data_dir.exists()
    
    # Verify warning was printed
    captured = capsys.readouterr()
    assert "Warning: Google Search Console credentials not found" in captured.out

# Test cases for parse_arguments
def test_parse_arguments_default():
    """Test parse_arguments with default values."""
    with patch('sys.argv', ['script_name']):
        args = parse_arguments()
        assert args.limit == 50
        assert args.output == 'data/discover_report.csv'

def test_parse_arguments_custom():
    """Test parse_arguments with custom values."""
    with patch('sys.argv', [
        'script_name',
        '--limit', '100',
        '--output', 'custom_report.csv'
    ]):
        args = parse_arguments()
        assert args.limit == 100
        assert args.output == 'custom_report.csv'

# Test cases for main
@patch('discover_monitor.main.DiscoverMonitor')
@patch('discover_monitor.main.parse_arguments')
def test_main_success(mock_parse_args, mock_monitor_class, setup_environment, capsys):
    """Test the main function with successful execution."""
    test_dir, creds_file, data_dir = setup_environment
    
    # Set up mock return values
    mock_args = MagicMock()
    mock_args.limit = 50
    mock_args.output = str(data_dir / 'report.csv')
    mock_parse_args.return_value = mock_args
    
    # Create a mock for the DiscoverMonitor instance
    mock_monitor = MagicMock()
    mock_monitor_class.return_value = mock_monitor
    
    # Call the main function
    with patch('sys.argv', ['script_name']):
        main()
    
    # Verify the monitor was called
    mock_monitor_class.assert_called_once()
    mock_monitor.run.assert_called_once()
    
    # Verify output
    captured = capsys.readouterr()
    assert "Google Discover Monitoring Tool" in captured.out
    assert "Monitoring complete" in captured.out

@patch('discover_monitor.main.DiscoverMonitor')
@patch('discover_monitor.main.parse_arguments')
def test_main_keyboard_interrupt(mock_parse_args, mock_monitor_class, setup_environment, capsys):
    """Test the main function with keyboard interrupt."""
    # Set up mock return values
    mock_args = MagicMock()
    mock_args.limit = 50
    mock_args.output = 'data/report.csv'
    mock_parse_args.return_value = mock_args
    
    # Make the monitor.run() raise KeyboardInterrupt
    mock_monitor = MagicMock()
    mock_monitor.run.side_effect = KeyboardInterrupt()
    mock_monitor_class.return_value = mock_monitor
    
    # Call the main function and check exit code
    with patch('sys.argv', ['script_name']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    
    # Verify output
    captured = capsys.readouterr()
    assert "Monitoring stopped by user" in captured.out

@patch('discover_monitor.main.DiscoverMonitor')
@patch('discover_monitor.main.parse_arguments')
def test_main_unexpected_error(mock_parse_args, mock_monitor_class, setup_environment, capsys):
    """Test the main function with an unexpected error."""
    # Set up mock return values
    mock_args = MagicMock()
    mock_args.limit = 50
    mock_args.output = 'data/report.csv'
    mock_parse_args.return_value = mock_args
    
    # Make the monitor.run() raise an unexpected exception
    mock_monitor = MagicMock()
    mock_monitor.run.side_effect = Exception("Test error")
    mock_monitor_class.return_value = mock_monitor
    
    # Call the main function and check exit code
    with patch('sys.argv', ['script_name']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
    
    # Verify error message
    captured = capsys.readouterr()
    assert "An error occurred: Test error" in captured.out
