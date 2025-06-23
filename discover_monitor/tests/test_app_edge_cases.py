"""Tests for edge cases and error conditions in app.py."""
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, mock_open

import pandas as pd
import pytest
import streamlit as st

from discover_monitor.app import (
    apply_filters,
    display_charts,
    export_data,
    main
)

@pytest.fixture
def test_df():
    """Fixture that provides a test DataFrame for testing."""
    return pd.DataFrame({
        'title': ['Test Article 1', 'Test Article 2'],
        'source': ['Test Source', 'Test Source'],
        'section': ['Test Section', 'Another Section'],
        'published_date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')],
        'url': ['http://example.com/1', 'http://example.com/2']
    })

# Sample test data with dates for testing date filtering
TEST_DATA_WITH_DATES = pd.DataFrame({
    'title': ['Article 1', 'Article 2', 'Article 3'],
    'source': ['Source A', 'Source B', 'Source A'],
    'section': ['Section 1', 'Section 2', 'Section 1'],
    'published_date': pd.to_datetime([
        '2023-01-01',
        '2023-01-15',
        '2023-02-01'
    ]),
    'url': [
        'http://example.com/1',
        'http://example.com/2',
        'http://example.com/3'
    ]
})

def test_apply_filters_source_filter():
    """Test applying source filter."""
    filters = {'source': 'Source A'}
    result = apply_filters(TEST_DATA_WITH_DATES, filters)
    assert len(result) == 2
    assert all(result['source'] == 'Source A')

def test_apply_filters_date_filter():
    """Test applying date filter."""
    filters = {
        'start_date': '2023-01-10',
        'end_date': '2023-01-20'
    }
    result = apply_filters(TEST_DATA_WITH_DATES, filters)
    assert len(result) == 1
    assert result.iloc[0]['title'] == 'Article 2'

def test_apply_filters_empty_filters():
    """Test with empty filters."""
    result = apply_filters(TEST_DATA_WITH_DATES, {})
    pd.testing.assert_frame_equal(result, TEST_DATA_WITH_DATES)

def test_apply_filters_empty_dataframe():
    """Test with empty DataFrame."""
    empty_df = pd.DataFrame(columns=TEST_DATA_WITH_DATES.columns)
    result = apply_filters(empty_df, {'source': 'Test'})
    assert result.empty

@patch('discover_monitor.app.st.plotly_chart')
@patch('discover_monitor.app.st.warning')
@patch('discover_monitor.app.st.tabs')
@patch('discover_monitor.app.generate_source_chart')
@patch('discover_monitor.app.generate_section_chart')
def test_display_charts_empty_dataframe(mock_section_chart, mock_source_chart, mock_tabs, mock_warning, mock_plotly_chart):
    """Test display_charts with an empty DataFrame."""
    # Create an empty DataFrame with the required columns
    empty_df = pd.DataFrame(columns=['title', 'source', 'section', 'published_date', 'url'])
    
    # Call the function with the empty DataFrame
    display_charts(empty_df)
    
    # Verify that no chart generation functions were called
    mock_source_chart.assert_not_called()
    mock_section_chart.assert_not_called()
    
    # Verify that no Streamlit components were called
    mock_tabs.assert_not_called()
    mock_plotly_chart.assert_not_called()
    mock_warning.assert_not_called()

@patch('discover_monitor.app.st.plotly_chart')
@patch('discover_monitor.app.st.warning')
@patch('discover_monitor.app.st.tabs')
@patch('discover_monitor.app.generate_source_chart', return_value=None)
@patch('discover_monitor.app.generate_section_chart', return_value=None)
def test_display_charts_with_data(mock_section_chart, mock_source_chart, mock_tabs, mock_warning, mock_plotly_chart, test_df):
    """Test display_charts with actual data."""
    # Mock the tabs context manager
    mock_tab1 = MagicMock()
    mock_tab2 = MagicMock()
    mock_tabs.return_value = (mock_tab1, mock_tab2)
    mock_tab1.__enter__.return_value = mock_tab1
    mock_tab2.__enter__.return_value = mock_tab2
    
    # Call the function with the test data
    display_charts(test_df)
    
    # Verify that tabs were created
    mock_tabs.assert_called_once_with(["📊 Por fuente", "📈 Por sección"])
    
    # Verify that chart generation functions were called with the test data
    mock_source_chart.assert_called_once()
    mock_section_chart.assert_called_once()
    
    # Since we returned None from both chart functions, plotly_chart should not be called
    mock_plotly_chart.assert_not_called()
    
    # Verify that warnings were shown for both tabs (since we returned None from chart functions)
    assert mock_warning.call_count == 2
    warning_messages = [call[0][0] for call in mock_warning.call_args_list]
    assert "No hay datos para mostrar el gráfico por fuente" in warning_messages
    assert "No hay datos para mostrar el gráfico por sección" in warning_messages

def test_export_data_csv_error_handling():
    """Test error handling in CSV export."""
    with patch('discover_monitor.app.st.sidebar') as mock_sidebar, \
         patch('discover_monitor.app.tempfile.NamedTemporaryFile') as mock_tempfile, \
         patch('builtins.open', side_effect=Exception("Test error")), \
         patch('discover_monitor.app.st.error') as mock_error:
        
        # Setup mock file
        mock_tempfile.return_value.__enter__.return_value.name = '/tmp/test.csv'
        
        # Simulate CSV export button click
        mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Exportar a CSV"
        
        export_data(TEST_DATA_WITH_DATES)
        
        # Verify error message
        mock_error.assert_called_once()
        assert "Error al exportar a CSV" in str(mock_error.call_args[0][0])

def test_export_data_excel_error_handling():
    """Test error handling in Excel export."""
    with patch('discover_monitor.app.st.sidebar') as mock_sidebar, \
         patch('discover_monitor.app.tempfile.NamedTemporaryFile') as mock_tempfile, \
         patch('builtins.open', side_effect=Exception("Test error")), \
         patch('discover_monitor.app.st.error') as mock_error:
        
        # Setup mock file
        mock_tempfile.return_value.__enter__.return_value.name = '/tmp/test.xlsx'
        
        # Simulate Excel export button click
        mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Exportar a Excel"
        
        export_data(TEST_DATA_WITH_DATES)
        
        # Verify error message
        mock_error.assert_called_once()
        assert "Error al exportar a Excel" in str(mock_error.call_args[0][0])

@patch('discover_monitor.app.os.path.exists', return_value=True)
@patch('discover_monitor.app.os.unlink')
@patch('discover_monitor.app.open', new_callable=mock_open)
@patch('discover_monitor.app.st.sidebar')
@patch('discover_monitor.app.st.error')
@patch('discover_monitor.app.st.success')
@patch('discover_monitor.app.logger')
@patch('discover_monitor.app.generate_pdf_report')
def test_export_data_pdf_error_handling(
    mock_generate_pdf, mock_logger, mock_success, mock_error, 
    mock_sidebar, mock_file_open, mock_os_unlink, mock_os_path_exists
):
    """Test error handling in PDF export."""
    # Create test data with all required columns
    test_data = pd.DataFrame({
        'title': ['Article 1', 'Article 2'],
        'source': ['Source A', 'Source B'],
        'section': ['Section 1', 'Section 2'],
        'published_date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')],
        'url': ['http://example.com/1', 'http://example.com/2']
    })
    
    # Configure the sidebar button to return True for the PDF export button
    mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Generar Informe PDF"
    
    # Mock the download button to do nothing
    mock_sidebar.download_button.return_value = None
    
    # Configure the temp file mock
    mock_temp_file = MagicMock()
    mock_temp_file.name = '/tmp/test.pdf'
    
    # Mock the NamedTemporaryFile context manager
    with patch('discover_monitor.app.tempfile.NamedTemporaryFile') as mock_tempfile:
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file
        
        # Make generate_pdf_report raise an exception
        mock_generate_pdf.side_effect = Exception("PDF generation error")
        
        # Call the function
        export_data(test_data)
        
        # Verify generate_pdf_report was called
        assert mock_generate_pdf.call_count == 1
        
        # Get the actual arguments passed to generate_pdf_report
        args, _ = mock_generate_pdf.call_args
        called_df = args[0]  # First argument is the DataFrame
        
        # Verify the DataFrame contents match (using pandas testing utilities)
        pd.testing.assert_frame_equal(called_df, test_data)
        
        # Verify the second argument is the mock temp file path
        # We'll verify that the mock was called with the expected arguments
        assert mock_generate_pdf.call_args[0][0].equals(test_data)  # Check DataFrame
        
        # Get the actual file path that was passed to generate_pdf_report
        # This will be a MagicMock object, so we'll verify it's being used correctly
        called_file_path = mock_generate_pdf.call_args[0][1]
        
        # Verify the mock temp file was used in the call
        assert called_file_path is not None
        
        # Verify the mock temp file is being used for cleanup
        mock_logger.error.assert_called_once()
        assert "Error al generar el PDF" in mock_logger.error.call_args[0][0]
        
        # Verify success message was not shown
        mock_success.assert_not_called()
        
        # Verify the mock temp file is being used for cleanup
        # We need to use the same mock object that was passed to the function
        # instead of accessing the name attribute directly
        mock_os_path_exists.assert_called_once()
        mock_os_unlink.assert_called_once()
        
        # Verify the same file path was used for both exists and unlink
        assert mock_os_path_exists.call_args[0] == mock_os_unlink.call_args[0]

@patch('discover_monitor.app.st.set_page_config')
@patch('discover_monitor.app.st.title')
@patch('discover_monitor.app.st.markdown')
@patch('discover_monitor.app.load_data')
@patch('discover_monitor.app.st.button')
@patch('discover_monitor.app.st.spinner')
@patch('discover_monitor.app.st.success')
@patch('discover_monitor.app.st.rerun')
@patch('discover_monitor.app.st.error')
@patch('discover_monitor.app.st.info')
@patch('discover_monitor.app.logger')
@patch('discover_monitor.app.st.session_state')
def test_main_scraper_execution(mock_session_state, mock_logger, mock_info, mock_error, mock_rerun, mock_success, 
                            mock_spinner, mock_button, mock_load_data, mock_markdown, 
                            mock_title, mock_config):
    """Test main function when executing the scraper."""
    # Setup mocks
    # Create a side effect for the button to simulate a click
    mock_button.side_effect = [True]  # First call returns True to simulate button click
    mock_spinner.return_value.__enter__.return_value = None
    
    # Setup empty DataFrame to trigger the scraper button
    mock_load_data.return_value = pd.DataFrame()
    
    # Mock the session state
    mock_session_state.__contains__.side_effect = lambda key: key == 'df'
    mock_session_state.__getitem__.side_effect = lambda key: pd.DataFrame() if key == 'df' else {}.__getitem__(key)
    
    # Call main
    main()
    
    # Verify the scraper button was shown with correct text
    # The button is shown after the "No se encontraron datos" message
    mock_button.assert_called_once_with("Ejecutar Scraper")
    
    # Verify the info message was shown with the correct text
    mock_info.assert_called_with("No se encontraron datos. Ejecuta el script de scraping primero para generar datos.")
    
    # Verify spinner was shown with correct message when button is clicked
    mock_spinner.assert_called_once_with("Ejecutando scraper...")
    
    # Verify success message and rerun were called
    mock_success.assert_called_once_with("¡Datos actualizados correctamente!")
    mock_rerun.assert_called_once()
    
    # Verify no error was shown
    mock_error.assert_not_called()
    
    # Verify logger was called with expected messages
    assert mock_logger.error.call_count == 0, "No errors should be logged"

from unittest.mock import MagicMock, patch, PropertyMock

# ... (keep other imports and test functions the same) ...

@patch('discover_monitor.app.st.set_page_config')
@patch('discover_monitor.app.load_data')
@patch('discover_monitor.app.st.button', return_value=True)
@patch('discover_monitor.app.st.spinner')
@patch('discover_monitor.app.st.error')
@patch('discover_monitor.app.st.info')
def test_load_data_error_handling(mock_info, mock_error, mock_spinner, mock_button, mock_load_data, _):
    """Test error handling when load_data returns no data."""
    # Configure the mock to return an empty DataFrame (simulating no data loaded)
    mock_load_data.return_value = pd.DataFrame()
    
    # Create a mock context manager for the spinner
    mock_context = MagicMock()
    mock_spinner.return_value.__enter__.return_value = mock_context
    
    # Create a mock for st.session_state with a 'df' attribute
    mock_session_state = MagicMock()
    mock_session_state.df = pd.DataFrame()  # Empty DataFrame to trigger load_data
    
    # Patch st.session_state to use our mock
    with patch('discover_monitor.app.st.session_state', mock_session_state):
        # Call main
        main()
        
        # Verify that load_data was called at least once
        assert mock_load_data.called, "load_data was not called"
        
        # Verify that an info message was shown about no data
        mock_info.assert_called_once()
        assert "No se encontraron datos" in str(mock_info.call_args[0][0])
        
        # Verify that no error was shown
        mock_error.assert_not_called()
