"""Additional tests to improve coverage for app.py."""
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add the parent directory to the path so we can import the app module
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import pytest
import streamlit as st

from discover_monitor.app import (
    load_data,
    get_data,
    generate_source_chart,
    generate_section_chart,
    generate_pdf_report,
    apply_filters,
    setup_sidebar_filters,
    export_data,
    display_metrics,
    display_charts,
    display_table,
    main
)

# Fixtures

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return pd.DataFrame({
        'title': ['Test Article 1', 'Test Article 2'],
        'source': ['Source A', 'Source B'],
        'section': ['News', 'Sports'],
        'published_date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')],
        'url': ['http://example.com/1', 'http://example.com/2'],
        'description': ['Test description 1', 'Test description 2']
    })
import streamlit as st

from discover_monitor.app import (
    load_data,
    get_data,
    generate_source_chart,
    generate_section_chart,
    generate_pdf_report,
    apply_filters,
    setup_sidebar_filters,
    export_data,
    main
)

# Sample test data for testing
TEST_DATA = pd.DataFrame({
    'title': ['Article 1', 'Article 2', 'Article 3'],
    'source': ['Source A', 'Source B', 'Source A'],
    'section': ['Section 1', 'Section 2', 'Section 1'],
    'published_date': [
        (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
        (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d')
    ],
    'url': [
        'http://example.com/1',
        'http://example.com/2',
        'http://example.com/3'
    ],
    'description': ['Desc 1', 'Desc 2', 'Desc 3']
})

@patch('app.DATA_DIR', new_callable=tempfile.TemporaryDirectory)
def test_load_data_cache_miss(mock_data_dir):
    """Test load_data when cache file doesn't exist."""
    # Create a temporary directory for DATA_DIR
    temp_dir = Path(mock_data_dir.name)
    data_file = temp_dir / "articles.csv"
    
    # Make sure the file doesn't exist
    if data_file.exists():
        data_file.unlink()
    
    with patch('app.pd.read_csv') as mock_read_csv:
        # Call the function
        result = load_data()
        
        # Verify behavior
        mock_read_csv.assert_not_called()  # Should not try to read non-existent file
        assert result.empty  # Should return empty DataFrame

def test_apply_filters_empty_data():
    """Test apply_filters with empty DataFrame."""
    empty_df = pd.DataFrame()
    filters = {'source': ['Source A'], 'section': ['Section 1']}
    result = apply_filters(empty_df, filters)
    assert result.empty

@patch('app.datetime')
def test_setup_sidebar_filters_empty_data(mock_datetime, monkeypatch):
    """Test setup_sidebar_filters with empty DataFrame."""
    # Mock datetime.now() to return a fixed date
    mock_now = datetime(2023, 1, 1)
    mock_datetime.now.return_value = mock_now
    
    # Mock the sidebar selectbox and date_input
    mock_sidebar = MagicMock()
    mock_sidebar.selectbox.return_value = 'Todos'
    mock_sidebar.date_input.return_value = (mock_now - timedelta(days=30), mock_now)
    
    # Apply the mock
    monkeypatch.setattr('app.st.sidebar', mock_sidebar)
    
    # Call with empty DataFrame
    empty_df = pd.DataFrame(columns=['source', 'published_date'])
    filters = setup_sidebar_filters(empty_df)
    
    # Verify the expected filters
    assert filters == {
        'source': 'Todos',
        'start_date': mock_now - timedelta(days=30),
        'end_date': mock_now
    }

def test_export_data_empty_data():
    """Test export_data with empty DataFrame."""
    empty_df = pd.DataFrame()
    mock_sidebar = MagicMock()
    
    with patch('app.st.sidebar', mock_sidebar), \
         patch('app.st.warning') as mock_warning:
        export_data(empty_df)
        
        # Verify no export buttons were added
        mock_sidebar.button.assert_not_called()
        mock_sidebar.markdown.assert_not_called()
        mock_sidebar.subheader.assert_not_called()
        mock_warning.assert_not_called()

def test_main_error_handling(monkeypatch):
    """Test main function error handling."""
    # Mock the get_data function to raise an exception
    def mock_get_data():
        raise Exception("Test error")
        
    # Mock Streamlit components
    mock_st = MagicMock()
    mock_st.sidebar = MagicMock()
    mock_st.error = MagicMock()
    mock_st.session_state = {}
    
    # Apply mocks
    monkeypatch.setattr('discover_monitor.app.get_data', mock_get_data)
    monkeypatch.setattr('discover_monitor.app.st', mock_st)
    
    # Import and call main
    from discover_monitor.app import main
    main()
    
    # Verify error handling
    mock_st.error.assert_called_once()
    
    # Test with valid data but filter error
    def mock_get_valid_data():
        return pd.DataFrame({
            'title': ['Test'],
            'source': ['Test'],
            'section': ['Test'],
            'published_date': [pd.Timestamp('2023-01-01')],
            'url': ['http://example.com']
        })
    
    def mock_setup_sidebar_filters(df):
        raise Exception("Filter error")
    
    monkeypatch.setattr('discover_monitor.app.get_data', mock_get_valid_data)
    monkeypatch.setattr('discover_monitor.app.setup_sidebar_filters', mock_setup_sidebar_filters)
    
    main()
    assert mock_st.error.call_count == 2  # Should have been called again for the filter error

def test_generate_source_chart_empty_data():
    """Test generate_source_chart with empty DataFrame."""
    empty_df = pd.DataFrame()
    with patch('app.st.bar_chart') as mock_chart:
        generate_source_chart(empty_df)
        mock_chart.assert_not_called()

def test_generate_section_chart_empty_data():
    """Test generate_section_chart with empty DataFrame."""
    empty_df = pd.DataFrame()
    with patch('app.st.bar_chart') as mock_chart:
        generate_section_chart(empty_df)
        mock_chart.assert_not_called()

@patch('discover_monitor.app.FPDF')
def test_generate_pdf_report_empty_data(mock_fpdf):
    """Test generate_pdf_report with empty DataFrame."""
    with patch('discover_monitor.app.logger') as mock_logger:
        # Test with empty DataFrame - should just return without creating PDF
        generate_pdf_report(pd.DataFrame(), 'test.pdf')
        mock_logger.warning.assert_called_once_with("No hay datos para generar el informe PDF")
        mock_fpdf.assert_not_called()
        
        # Test with None output path - should raise ValueError
        with pytest.raises(ValueError):
            generate_pdf_report(pd.DataFrame({'title': ['Test']}), None)
            
        # Test with valid data but file write error
        test_df = pd.DataFrame({
            'title': ['Test Article'],
            'source': ['Test Source'],
            'section': ['Test Section'],
            'published_date': [pd.Timestamp('2023-01-01')],
            'url': ['http://example.com']
        })
        
        # Configurar el mock de FPDF para que falle al guardar
        mock_pdf_instance = MagicMock()
        mock_fpdf.return_value = mock_pdf_instance
        mock_pdf_instance.output.side_effect = IOError("Error al escribir")
        
        with pytest.raises(IOError) as exc_info:
            generate_pdf_report(test_df, 'test.pdf')
        
        # Verificar que el mensaje de error sea el esperado
        assert "Error al escribir" in str(exc_info.value)
        
        # Verificar que se llamó a logger.error
        mock_logger.error.assert_called_once_with(
            "Error al generar el informe PDF: Error al escribir",
            exc_info=True
        )

def test_export_data_empty_warning():
    """Test that export_data shows warning when DataFrame is empty."""
    with patch('discover_monitor.app.st.sidebar.warning') as mock_warning:
        export_data(pd.DataFrame())
        mock_warning.assert_called_once_with("No hay datos para exportar")

def test_export_data_csv_error():
    """Test error handling when CSV export fails."""
    # Setup test data
    test_df = pd.DataFrame({
        'title': ['Test Article'],
        'source': ['Test Source'],
        'section': ['Test Section'],
        'published_date': [pd.Timestamp('2023-01-01')],
        'url': ['http://example.com']
    })
    
    # Setup mocks
    with patch('discover_monitor.app.st.sidebar') as mock_sidebar, \
         patch('discover_monitor.app.st.error') as mock_error, \
         patch('discover_monitor.app.logger') as mock_logger, \
         patch('discover_monitor.app.tempfile.NamedTemporaryFile') as mock_tempfile, \
         patch('pandas.DataFrame.to_csv') as mock_to_csv, \
         patch('os.path.exists', return_value=True), \
         patch('os.unlink') as mock_unlink:
        
        # Configure mocks
        mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Exportar a CSV"
        mock_file = MagicMock()
        mock_file.name = '/tmp/tempfile.csv'
        mock_tempfile.return_value.__enter__.return_value = mock_file
        mock_to_csv.side_effect = Exception("CSV error")
        
        # Call the function
        export_data(test_df)
        
        # Verify error handling
        mock_error.assert_called_once()
        assert "Error al exportar a CSV" in mock_error.call_args[0][0]
        mock_logger.error.assert_called_once()
        assert "CSV error" in str(mock_logger.error.call_args[0][0])
        mock_unlink.assert_called_once_with('/tmp/tempfile.csv')

def test_export_data_excel_error():
    """Test error handling when Excel export fails."""
    # Setup test data
    test_df = pd.DataFrame({
        'title': ['Test Article'],
        'source': ['Test Source'],
        'section': ['Test Section'],
        'published_date': [pd.Timestamp('2023-01-01')],
        'url': ['http://example.com']
    })
    
    # Setup mocks
    with patch('discover_monitor.app.st.sidebar') as mock_sidebar, \
         patch('discover_monitor.app.st.error') as mock_error, \
         patch('discover_monitor.app.logger') as mock_logger, \
         patch('discover_monitor.app.tempfile.NamedTemporaryFile') as mock_tempfile, \
         patch('pandas.DataFrame.to_excel') as mock_to_excel, \
         patch('os.path.exists', return_value=True), \
         patch('os.unlink') as mock_unlink:
        
        # Configure mocks
        mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Exportar a Excel"
        mock_file = MagicMock()
        mock_file.name = '/tmp/tempfile.xlsx'
        mock_tempfile.return_value.__enter__.return_value = mock_file
        mock_to_excel.side_effect = Exception("Excel error")
        
        # Call the function
        export_data(test_df)
        
        # Verify error handling
        mock_error.assert_called_once()
        assert "Error al exportar a Excel" in mock_error.call_args[0][0]
        mock_logger.error.assert_called_once()
        assert "Excel error" in str(mock_logger.error.call_args[0][0])
        mock_unlink.assert_called_once_with('/tmp/tempfile.xlsx')

def test_export_data_pdf_error():
    """Test error handling when PDF generation fails."""
    # Setup test data
    test_df = pd.DataFrame({
        'title': ['Test Article'],
        'source': ['Test Source'],
        'section': ['Test Section'],
        'published_date': [pd.Timestamp('2023-01-01')],
        'url': ['http://example.com']
    })
    
    # Setup mocks
    with patch('discover_monitor.app.st.sidebar') as mock_sidebar, \
         patch('discover_monitor.app.st.error') as mock_error, \
         patch('discover_monitor.app.logger') as mock_logger, \
         patch('discover_monitor.app.tempfile.NamedTemporaryFile') as mock_tempfile, \
         patch('discover_monitor.app.generate_pdf_report') as mock_generate_pdf, \
         patch('os.path.exists', return_value=True), \
         patch('os.unlink') as mock_unlink:
        
        # Configure mocks
        mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Generar Informe PDF"
        
        # Create a proper mock for the file object
        mock_file = MagicMock()
        mock_file.name = '/tmp/tempfile.pdf'
        
        # Set up the context manager to return our mock file
        mock_temp_instance = MagicMock()
        mock_temp_instance.__enter__.return_value = mock_file
        # Make sure name attribute is accessible on the instance
        mock_temp_instance.name = '/tmp/tempfile.pdf'
        mock_tempfile.return_value = mock_temp_instance
        
        # Simulate PDF generation error
        mock_generate_pdf.side_effect = Exception("PDF generation error")
        
        # Call the function
        export_data(test_df)
        
        # Verify error handling
        mock_error.assert_called_once()
        assert "Error al generar el PDF" in mock_error.call_args[0][0]
        mock_logger.error.assert_called_once()
        assert "PDF generation error" in str(mock_logger.error.call_args[0][0])
        
        # Verify unlink was called with the temporary file's name
        # The function calls unlink with tmp_file.name, which is the mock_temp_instance.name
        mock_unlink.assert_called_once_with('/tmp/tempfile.pdf')
