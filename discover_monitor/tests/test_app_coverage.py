"""Additional tests to improve coverage for app.py."""
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pandas as pd
import pytest
import streamlit as st

from app import (
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
    # Mock the streamlit functions
    mock_st = MagicMock()
    monkeypatch.setattr('app.st', mock_st)
    
    # Mock session state
    mock_session_state = MagicMock()
    mock_session_state.df = pd.DataFrame()  # Empty DataFrame to trigger load_data
    mock_st.session_state = mock_session_state
    
    # Mock load_data to raise an exception
    mock_load_data = MagicMock(side_effect=Exception("Test error"))
    monkeypatch.setattr('app.load_data', mock_load_data)
    
    # Call the main function
    with pytest.raises(Exception) as exc_info:
        main()
    
    # Verify the error was raised
    assert "Test error" in str(exc_info.value)
    
    # Verify load_data was called
    mock_load_data.assert_called_once()

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

@patch('app.FPDF')
def test_generate_pdf_report_empty_data(mock_fpdf):
    """Test generate_pdf_report with empty DataFrame."""
    empty_df = pd.DataFrame()
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            generate_pdf_report(empty_df, temp_file.name)
            # Should not raise an exception
            assert os.path.exists(temp_file.name)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

def test_export_data_error_handling():
    """Test error handling in export_data function."""
    # Create a test DataFrame with proper datetime objects
    test_df = pd.DataFrame({
        'title': ['Test Article'],
        'source': ['Test Source'],
        'section': ['Test Section'],
        'published_date': [datetime.now()],
        'url': ['https://example.com'],
        'description': ['Test Description']
    })
    
    # Test Excel export error
    with patch('app.st.sidebar') as mock_sidebar, \
         patch('pandas.DataFrame.to_excel', side_effect=Exception("Test error")), \
         patch('app.st.error') as mock_error, \
         patch('app.os.path.exists', return_value=True), \
         patch('app.os.unlink'):
        mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Exportar a Excel"
        export_data(test_df)
        mock_error.assert_called_with("Error al exportar a Excel: Test error")
    
    # Test PDF export error - first mock the FPDF class
    with patch('app.st.sidebar') as mock_sidebar, \
         patch('app.st.error') as mock_error, \
         patch('app.os.path.exists', return_value=True), \
         patch('app.os.unlink'):
        
        # Create a side effect that will raise an exception when output is called
        def raise_error(*args, **kwargs):
            raise Exception("Test error")
            
        # Mock the FPDF class and its methods
        mock_fpdf = MagicMock()
        mock_fpdf_instance = MagicMock()
        mock_fpdf.return_value = mock_fpdf_instance
        mock_fpdf_instance.output.side_effect = raise_error
        
        # Patch the FPDF class
        with patch('app.FPDF', mock_fpdf):
            mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Generar Informe PDF"
            export_data(test_df)
            
            # The actual error message includes the exception details
            assert mock_error.called
            assert "Error al generar el PDF" in mock_error.call_args[0][0]
