"""Additional tests to improve coverage for app.py."""
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

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

class MockSessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    
    def __contains__(self, key):
        return key in self.__dict__
    
    def __setitem__(self, key, value):
        self.__dict__[key] = value
    
    def __getitem__(self, key):
        return self.__dict__[key]

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return pd.DataFrame({
        'title': ['Test Article 1', 'Test Article 2'],
        'source': ['Source A', 'Source B'],
        'section': ['News', 'Sports'],
        'published_date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')],
        'url': ['http://example.com/1', 'http://example.com/2'],
        'description': ['Test description 1', 'Test description 2'],
        'image_url': ['http://example.com/img1.jpg', 'http://example.com/img2.jpg'],
        'author': ['Author 1', 'Author 2']
    })

# Tests for generate_source_chart

def test_generate_source_chart_empty():
    """Test generate_source_chart with empty DataFrame."""
    result = generate_source_chart(pd.DataFrame())
    assert result is None
    
    result = generate_source_chart(pd.DataFrame({'other_column': [1, 2, 3]}))
    assert result is None

def test_generate_source_chart_valid(sample_data):
    """Test generate_source_chart with valid data."""
    result = generate_source_chart(sample_data)
    assert result is not None
    # The chart should have one trace per source (2 sources in sample data)
    assert len(result.data) == 2  # One trace per source
    # Check that both sources are present in the traces
    sources_in_chart = {trace.name for trace in result.data}
    assert 'Source A' in sources_in_chart
    assert 'Source B' in sources_in_chart

# Tests for generate_section_chart

def test_generate_section_chart_empty():
    """Test generate_section_chart with empty DataFrame."""
    result = generate_section_chart(pd.DataFrame())
    assert result is None
    
    result = generate_section_chart(pd.DataFrame({'other_column': [1, 2, 3]}))
    assert result is None

def test_generate_section_chart_valid(sample_data):
    """Test generate_section_chart with valid data."""
    result = generate_section_chart(sample_data)
    assert result is not None
    assert len(result.data[0].x) == 2  # Should have 2 sections

# Tests for generate_pdf_report

@patch('discover_monitor.app.FPDF')
@patch('discover_monitor.app.datetime')
@patch('discover_monitor.app.st')
def test_generate_pdf_report_empty(mock_st, mock_datetime, mock_fpdf_class):
    """Test generate_pdf_report with empty DataFrame and None output path."""
    # Mock datetime.now()
    mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"
    
    # Create a mock PDF instance
    mock_pdf = MagicMock()
    mock_fpdf_class.return_value = mock_pdf
    
    # Test with empty DataFrame - should log warning and return early
    with patch('discover_monitor.app.logger') as mock_logger:
        empty_df = pd.DataFrame(columns=['title', 'source', 'section', 'published_date', 'url', 'description'])
        generate_pdf_report(empty_df, 'test.pdf')
        mock_logger.warning.assert_called_once_with("No hay datos para generar el informe PDF")
        mock_fpdf_class.assert_not_called()
    
    # Reset mocks
    mock_logger.reset_mock()
    mock_fpdf_class.reset_mock()
    
    # Test with valid data but None output path - should raise ValueError before FPDF is initialized
    with patch('discover_monitor.app.logger') as mock_logger:
        test_df = pd.DataFrame({
            'title': ['Test'],
            'source': ['Test'],
            'section': ['Test'],
            'published_date': [pd.Timestamp('2023-01-01')],
            'url': ['http://example.com'],
            'description': ['Test description']
        })
        
        # This should raise a ValueError before FPDF is initialized
        with pytest.raises(ValueError, match="La ruta de salida no puede estar vacía"):
            generate_pdf_report(test_df, None)
        
        # FPDF should not be initialized because we raise the error first
        mock_fpdf_class.assert_not_called()
        mock_pdf.output.assert_not_called()
            
@patch('discover_monitor.app.FPDF')
@patch('discover_monitor.app.datetime')
@patch('discover_monitor.app.st')
def test_generate_pdf_report_error(mock_st, mock_datetime, mock_fpdf_class):
    """Test error handling in generate_pdf_report."""
    # Mock datetime.now()
    mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"
    
    # Create a mock PDF that raises an exception when output is called
    mock_pdf = MagicMock()
    mock_pdf.output.side_effect = Exception("PDF generation error")
    mock_fpdf_class.return_value = mock_pdf
    
    # Setup mock logger
    mock_logger = MagicMock()
    
    # Test with valid data but error in PDF generation
    test_df = pd.DataFrame({
        'title': ['Test'],
        'source': ['Test'],
        'section': ['Test Section'],
        'published_date': [pd.Timestamp('2023-01-01')],
        'url': ['http://example.com'],
        'description': ['Test description'],
        'image_url': ['http://example.com/img.jpg'],
        'author': ['Test Author']
    })
    
    with patch('discover_monitor.app.logger', mock_logger):
        # Call the function with the test data
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            try:
                generate_pdf_report(test_df, temp_file.name)
            except Exception:
                pass  # Expected exception
        
        # Verify the error was shown to the user and logged
        mock_st.error.assert_called_once_with(
            "Error al generar el informe PDF: PDF generation error"
        )
        mock_logger.error.assert_called_once_with(
            "Error al generar el informe PDF: PDF generation error",
            exc_info=True
        )

@patch('discover_monitor.app.FPDF')
@patch('discover_monitor.app.st')
@patch('discover_monitor.app.datetime')
def test_generate_pdf_report_file_error(mock_datetime, mock_st, mock_fpdf_class):
    """Test generate_pdf_report with file write error."""
    # Mock datetime.now()
    mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"
    
    # Create a test DataFrame with all required columns
    test_df = pd.DataFrame({
        'title': ['Test Article'],
        'source': ['Test Source'],
        'section': ['Test Section'],
        'description': ['Test Description'],
        'url': ['http://example.com'],
        'published_date': [pd.Timestamp('2023-01-01')],
        'image_url': ['http://example.com/image.jpg'],
        'author': ['Test Author']
    })
    
    # Setup mock logger
    mock_logger = MagicMock()
    
    # Create a mock PDF that raises an exception when output is called
    mock_pdf = MagicMock()
    mock_pdf.output.side_effect = IOError("Error al escribir el archivo")
    mock_fpdf_class.return_value = mock_pdf
    
    # Mock the logger
    with patch('discover_monitor.app.logger', mock_logger):
        # Call the function with test data
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            generate_pdf_report(test_df, temp_path)
        except Exception:
            pass  # Expected exception
        
        # Verify error was shown to user
        mock_st.error.assert_called_once_with(
            "Error al generar el informe PDF: Error al escribir el archivo"
        )
        
        # Verify error was logged with exc_info
        mock_logger.error.assert_called_once_with(
            "Error al generar el informe PDF: Error al escribir el archivo",
            exc_info=True
        )
        
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

# Tests for export_data

def test_export_data_empty(monkeypatch):
    """Test export_data with empty DataFrame."""
    # Mock Streamlit components
    mock_st = MagicMock()
    mock_st.sidebar = MagicMock()
    mock_st.warning = MagicMock()
    mock_st.sidebar.warning = MagicMock()  # Mock sidebar.warning
    
    # Apply mocks
    monkeypatch.setattr('discover_monitor.app.st', mock_st)
    
    # Mock the logger to prevent actual logging during test
    mock_logger = MagicMock()
    
    with patch('discover_monitor.app.logger', mock_logger):
        # Call with empty DataFrame
        export_data(pd.DataFrame())
        
        # Verify warning was shown in the sidebar
        mock_st.sidebar.warning.assert_called_once_with("No hay datos para exportar")
        
        # Verify no error logging occurred
        mock_logger.error.assert_not_called()

def test_export_data_csv_error(monkeypatch, sample_data):
    """Test export_data with CSV export error."""
    # Mock Streamlit components
    mock_st = MagicMock()
    mock_st.sidebar = MagicMock()
    mock_st.error = MagicMock()
    mock_st.sidebar.button.side_effect = [True, False, False]  # Simulate CSV button click
    mock_st.sidebar.download_button.return_value = None  # Mock download button
    
    # Mock the logger
    mock_logger = MagicMock()
    
    # Create a temporary file path that will be used for the test
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    temp_path = temp_file.name
    temp_file.close()  # Close the file so it can be used by the test
    
    # Create a mock for the file object that will be returned by open()
    mock_file = MagicMock()
    mock_file.__enter__.return_value = b'test data'  # Mock file content
    
    try:
        # Mock tempfile.NamedTemporaryFile to return our temp file
        def mock_named_temporary_file(*args, **kwargs):
            kwargs['delete'] = False  # Ensure we can track the file
            kwargs['suffix'] = '.csv'
            return tempfile.NamedTemporaryFile(*args, **kwargs)
        
        # Make to_csv raise an exception
        def mock_to_csv(*args, **kwargs):
            raise Exception("CSV export error")
        
        # Apply mocks
        monkeypatch.setattr('discover_monitor.app.st', mock_st)
        
        # Mock the logger, pandas to_csv, and builtins.open
        with patch('discover_monitor.app.logger', mock_logger), \
             patch('pandas.DataFrame.to_csv', side_effect=mock_to_csv), \
             patch('tempfile.NamedTemporaryFile', wraps=tempfile.NamedTemporaryFile) as mock_temp_file, \
             patch('builtins.open', return_value=mock_file):
            
            # Call the function with sample data
            export_data(sample_data)
            
            # Verify error handling
            mock_st.error.assert_called_once_with(
                "Error al exportar a CSV: CSV export error"
            )
            mock_logger.error.assert_called_once_with(
                "Error al exportar a CSV: CSV export error",
                exc_info=True
            )
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                print(f"Error cleaning up temp file {temp_path}: {e}")


def test_export_data_pdf_error(monkeypatch, sample_data):
    """Test export_data with PDF export error."""
    # Mock Streamlit components
    mock_st = MagicMock()
    mock_st.sidebar = MagicMock()
    mock_st.error = MagicMock()
    mock_st.sidebar.button.side_effect = [False, False, True]  # Simulate PDF button click
    
    # Mock the logger
    mock_logger = MagicMock()
    
    # Create a real temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_path = tmp_file.name
    
    # Mock generate_pdf_report to raise an exception
    def mock_generate_pdf_report(df, output_path):
        raise Exception("PDF generation error")
    
    # Apply mocks
    monkeypatch.setattr('discover_monitor.app.st', mock_st)
    
    # Mock the logger and generate_pdf_report
    with patch('discover_monitor.app.logger', mock_logger), \
         patch('discover_monitor.app.generate_pdf_report', mock_generate_pdf_report):
        
        # Call the function with sample data
        export_data(sample_data)
        
        # Verify error handling
        mock_st.error.assert_called_once_with(
            "Error al generar el PDF: PDF generation error"
        )
        mock_logger.error.assert_called_once_with(
            "Error al generar el PDF: PDF generation error",
            exc_info=True
        )
    
    # Clean up
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)

# Tests for main function

def test_main_error_handling(monkeypatch):
    """Test main function error handling."""
    # Mock the load_data function to raise an exception
    def mock_load_data():
        raise Exception("Test error")
    
    # Mock the logger to verify error logging
    mock_logger = MagicMock()
    
    # Create a mock session state that supports attribute access
    mock_session_state = MagicMock()
    mock_session_state.__contains__.return_value = False  # Simulate empty session state
    mock_session_state.df = pd.DataFrame()  # Empty DataFrame by default
    
    # Mock Streamlit components
    mock_st = MagicMock()
    mock_st.session_state = mock_session_state
    mock_st.error = MagicMock()
    
    # Apply mocks
    monkeypatch.setattr('discover_monitor.app.load_data', mock_load_data)
    monkeypatch.setattr('discover_monitor.app.st', mock_st)
    
    # Mock the logger
    with patch('discover_monitor.app.logger', mock_logger):
        # Call main
        main()
        
        # Verify error handling - main() now shows a generic error message
        mock_st.error.assert_called_once_with("Se produjo un error inesperado: Test error")
        mock_logger.error.assert_called_once_with(
            "Error inesperado en la aplicación: Test error",
            exc_info=True
        )

def test_main_filter_error(monkeypatch, sample_data):
    """Test main function with filter error."""
    # Mock load_data to return sample data
    def mock_load_data():
        return sample_data
        
    # Mock get_data to return sample data
    def mock_get_data():
        return sample_data
        
    # Mock setup_sidebar_filters to raise an exception
    def mock_setup_sidebar_filters(df):
        raise Exception("Filter error")
    
    # Mock the logger to verify error logging
    mock_logger = MagicMock()
    
    # Create a mock session state that supports attribute access
    mock_session_state = MagicMock()
    mock_session_state.__contains__.return_value = False  # Simulate empty session state
    mock_session_state.df = pd.DataFrame()  # Empty DataFrame by default
    
    # Mock Streamlit components
    mock_st = MagicMock()
    mock_st.session_state = mock_session_state
    mock_st.error = MagicMock()
    
    # Apply mocks
    monkeypatch.setattr('discover_monitor.app.load_data', mock_load_data)
    monkeypatch.setattr('discover_monitor.app.get_data', mock_get_data)
    monkeypatch.setattr('discover_monitor.app.setup_sidebar_filters', mock_setup_sidebar_filters)
    monkeypatch.setattr('discover_monitor.app.st', mock_st)
    
    # Mock the logger
    with patch('discover_monitor.app.logger', mock_logger):
        # Call main
        main()
        
        # Verify error handling - check that the specific filter error is shown
        mock_st.error.assert_any_call("Error al configurar los filtros: Filter error")
        
        # Verify the logger was called with the correct error
        mock_logger.error.assert_any_call(
            "Error en setup_sidebar_filters: Filter error",
            exc_info=True
        )
