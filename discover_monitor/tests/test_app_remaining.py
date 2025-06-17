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
    display_metrics,
    display_charts,
    display_table,
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

def test_display_metrics():
    """Test display_metrics function."""
    with patch('app.st.metric') as mock_metric, \
         patch('app.st.columns') as mock_columns:
        # Mock the columns to return a list of 3 mock columns
        mock_cols = [MagicMock(), MagicMock(), MagicMock()]
        mock_columns.return_value = mock_cols
        
        display_metrics(TEST_DATA)
        
        # Verify 3 metrics were called (Total, Unique Sources, Unique Sections)
        assert mock_metric.call_count == 3
        
        # Verify the column context managers were used
        for col in mock_cols:
            col.__enter__.assert_called_once()
            col.__exit__.assert_called_once()

@patch('app.st.tabs')
@patch('app.st.plotly_chart')
@patch('app.generate_source_chart')
@patch('app.generate_section_chart')
def test_display_charts(mock_section_chart, mock_source_chart, mock_plotly, mock_tabs):
    """Test display_charts function."""
    # Setup mocks
    mock_tab1 = MagicMock()
    mock_tab2 = MagicMock()
    mock_tabs.return_value = [mock_tab1, mock_tab2]
    
    # Call the function
    display_charts(TEST_DATA)
    
    # Verify tabs were created
    mock_tabs.assert_called_once_with(["📊 Por fuente", "📈 Por sección"])
    
    # Verify chart generation functions were called
    mock_source_chart.assert_called_once_with(TEST_DATA)
    mock_section_chart.assert_called_once_with(TEST_DATA)
    
    # Verify plotly charts were rendered in their respective tabs
    assert mock_plotly.call_count == 2

@patch('app.st.dataframe')
def test_display_table(mock_dataframe):
    """Test display_table function."""
    display_table(TEST_DATA)
    mock_dataframe.assert_called_once()

def test_export_data_success():
    """Test successful export functionality."""
    # Test CSV export
    with patch('app.st.sidebar') as mock_sidebar, \
         patch('app.tempfile.NamedTemporaryFile') as mock_tempfile, \
         patch('app.os.path.exists', return_value=True), \
         patch('app.os.unlink'), \
         patch('builtins.open', mock_open()) as mock_file, \
         patch('app.st.success') as mock_success:
        
        # Setup mock file
        mock_tempfile.return_value.__enter__.return_value.name = '/tmp/test.csv'
        
        # Simulate CSV export button click
        mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Exportar a CSV"
        
        export_data(TEST_DATA)
        
        # Verify success message
        mock_success.assert_called_with("Datos exportados a CSV exitosamente")

@patch('app.st.set_page_config')
@patch('app.st.title')
@patch('app.st.markdown')
@patch('app.load_data')
@patch('app.setup_sidebar_filters')
@patch('app.apply_filters')
@patch('app.display_metrics')
@patch('app.display_charts')
@patch('app.display_table')
@patch('app.export_data')
@patch('app.pd')
@patch('app.st')
def test_main_success(mock_st, mock_pd, mock_export, mock_table, mock_charts, mock_metrics,
                    mock_apply_filters, mock_setup_filters, mock_load_data,
                    mock_markdown, mock_title, mock_config):
    """Test main function with successful execution."""
    # Setup mocks
    mock_load_data.return_value = TEST_DATA
    mock_setup_filters.return_value = {}
    mock_apply_filters.return_value = TEST_DATA
    
    # Create a mock DataFrame for pd.DataFrame()
    import pandas as pd
    mock_empty_df = pd.DataFrame()
    mock_pd.DataFrame.return_value = mock_empty_df.copy()
    
    # Setup session state mock with attribute access
    mock_session_state = MagicMock()
    mock_session_state.df = mock_empty_df
    mock_session_state.__contains__.side_effect = lambda x: False  # For 'df' not in st.session_state
    mock_st.session_state = mock_session_state
    
    # Mock the sidebar
    mock_sidebar = MagicMock()
    mock_st.sidebar = mock_sidebar
    
    # Call main
    main()
    
    # Verify main components were called
    # load_data is called twice: once during initialization and once in get_data()
    assert mock_load_data.call_count == 2
    mock_setup_filters.assert_called_once_with(TEST_DATA)
    mock_apply_filters.assert_called_once_with(TEST_DATA, {})
    mock_metrics.assert_called_once_with(TEST_DATA)
    mock_charts.assert_called_once_with(TEST_DATA)
    mock_table.assert_called_once_with(TEST_DATA)
    mock_export.assert_called_once_with(TEST_DATA)
    
    # Verify session state was updated with the test data
    # Check that 'df' was set in session state using attribute access
    # We use pd.testing.assert_frame_equal to properly compare DataFrames
    pd.testing.assert_frame_equal(mock_session_state.df, TEST_DATA)
