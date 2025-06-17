import os
import sys
import pytest
import pandas as pd
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import streamlit as st

# Add the parent directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the app module after setting up the path
import app

# Sample test data
TEST_DATA = pd.DataFrame({
    'title': ['Test Article 1', 'Test Article 2'],
    'source': ['test_source', 'test_source'],
    'section': ['test_section', 'test_section_2'],
    'published_date': pd.to_datetime(['2023-01-01', '2023-01-02']),
    'url': ['http://example.com/1', 'http://example.com/2']
})

# Fixture to set up the test environment
@pytest.fixture
def setup_test_environment():
    # Create a mock for the load_data function
    with patch('app.load_data') as mock_load_data:
        # Set up the mock to return test data by default
        mock_load_data.return_value = TEST_DATA.copy()
        
        # Create a proper mock for st.session_state that supports attribute access
        class SessionState(dict):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.__dict__ = self
                
        st.session_state = SessionState()
        st.session_state.df = pd.DataFrame()  # Initialize with empty DataFrame
        
        # Create a mock for st.sidebar
        st.sidebar = MagicMock()
        st.sidebar.button.return_value = False
        st.sidebar.selectbox.return_value = 'Todos'
        st.sidebar.date_input.return_value = [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')]
        st.sidebar.subheader = MagicMock()
        st.sidebar.markdown = MagicMock()
        
        # Create a mock for st.spinner
        st.spinner = MagicMock()
        
        # Create a mock for st.rerun
        st.rerun = MagicMock()
        
        # Create a mock for st.error
        st.error = MagicMock()
        
        # Create a mock for st.success
        st.success = MagicMock()
        
        # Create a mock for st.warning
        st.warning = MagicMock()
        
        # Create a mock for st.info
        st.info = MagicMock()
        
        # Create a mock for st.columns
        st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
        
        # Create a mock for st.tabs
        st.tabs = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
        
        # Create a mock for st.metric
        st.metric = MagicMock()
        
        # Create a mock for st.markdown
        st.markdown = MagicMock()
        
        # Create a mock for st.dataframe
        st.dataframe = MagicMock()
        
        # Create a mock for st.download_button
        st.download_button = MagicMock(return_value=True)
        
        # Create a mock for st.selectbox
        st.selectbox = MagicMock(return_value='CSV')
        
        # Create a mock for tempfile.NamedTemporaryFile
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = mock_file
            mock_file.name = '/tmp/test_file.csv'
            mock_tempfile.return_value = mock_file
            
            # Create a mock for os.unlink
            with patch('os.unlink'):
                yield mock_load_data


@patch('pandas.read_csv')
@patch('app.DATA_DIR')
def test_load_data_success(mock_data_dir, mock_read_csv):
    """Test that load_data loads data correctly from CSV."""
    # Arrange
    # Create a mock for the data directory and file
    mock_file = MagicMock()
    mock_file.exists.return_value = True
    
    # Set up the mock to handle the division operator
    mock_data_dir.__truediv__.return_value = mock_file
    
    # Create a copy of the test data to avoid modifying the original
    test_data = TEST_DATA.copy()
    
    # Mock the read_csv function to return our test data
    mock_read_csv.return_value = test_data
    
    # Act - Call load_data directly
    result = app.load_data()
    
    # Assert
    assert not result.empty
    assert len(result) == 2
    assert 'title' in result.columns
    assert 'source' in result.columns
    assert 'section' in result.columns
    assert 'published_date' in result.columns
    assert 'url' in result.columns
    
    # Verify the file existence check was called
    mock_file.exists.assert_called_once()
    
    # Verify read_csv was called with the correct arguments
    mock_read_csv.assert_called_once_with(mock_file, parse_dates=['published_date'])

@patch('pandas.read_csv')
@patch('app.DATA_DIR')
def test_load_data_file_not_found(mock_data_dir, mock_read_csv):
    """Test that load_data handles file not found scenario."""
    # Arrange
    # Create a mock for the data directory and file
    mock_file = MagicMock()
    mock_file.exists.return_value = False  # File doesn't exist
    
    # Set up the mock to handle the division operator
    mock_data_dir.__truediv__.return_value = mock_file
    
    # Mock the parent directory path
    mock_parent = MagicMock()
    mock_file.parent = mock_parent
    
    # Mock the read_csv function to ensure it's not called
    mock_read_csv.side_effect = FileNotFoundError
    
    # Act
    result = app.load_data()
    
    # Assert - should return an empty DataFrame with expected columns
    assert isinstance(result, pd.DataFrame)
    assert result.empty
    
    # Verify it has the expected columns
    expected_columns = ['title', 'source', 'section', 'published_date', 'url']
    assert all(col in result.columns for col in expected_columns)
    
    # Verify the file existence check was called
    mock_file.exists.assert_called_once()
    
    # Note: We don't test os.makedirs here since it's called at module import time
    # and is not part of the function's direct behavior that we're testing

@patch('pandas.read_csv')
@patch('app.DATA_DIR')
def test_load_data_exception_handling(mock_data_dir, mock_read_csv):
    """Test that load_data handles exceptions when reading the CSV file."""
    # Arrange
    # Create a mock for the data directory and file
    mock_file = MagicMock()
    mock_file.exists.return_value = True
    
    # Set up the mock to handle the division operator
    mock_data_dir.__truediv__.return_value = mock_file
    
    # Mock read_csv to raise an exception
    test_exception = Exception("Error de lectura del archivo")
    mock_read_csv.side_effect = test_exception
    
    # Mock the logger to verify the error is logged
    with patch('app.logger') as mock_logger:
        # Act
        result = app.load_data()
        
        # Assert
        # Should return an empty DataFrame
        assert isinstance(result, pd.DataFrame)
        assert result.empty
        
        # Verify the file existence check was called
        mock_file.exists.assert_called_once()
        
        # Verify read_csv was called with the correct arguments
        mock_read_csv.assert_called_once_with(mock_file, parse_dates=['published_date'])
        
        # Verify the error was logged
        mock_logger.error.assert_called_once_with(f"Error al cargar los datos: {test_exception}")


def test_get_data_loaded(setup_test_environment):
    """Test that get_data returns the loaded data."""
    # Arrange
    mock_load_data = setup_test_environment
    
    # Ensure the mock returns test data
    test_data = TEST_DATA.copy()
    mock_load_data.return_value = test_data

    # Act
    result = app.get_data()

    # Assert
    assert not result.empty
    assert len(result) == 2
    assert 'title' in result.columns
    assert 'source' in result.columns
    assert 'section' in result.columns
    assert 'published_date' in result.columns
    assert 'url' in result.columns
    
    # Verify load_data was called
    mock_load_data.assert_called_once()


def test_get_data_cached(setup_test_environment):
    """Test that get_data uses cached data on subsequent calls."""
    # Arrange
    mock_load_data = setup_test_environment
    
    # Set up the mock to return test data
    mock_load_data.return_value = TEST_DATA.copy()

    # First call should load data
    result1 = app.get_data()

    # Reset the mock to track subsequent calls
    mock_load_data.reset_mock()

    # Second call should use cached data
    result2 = app.get_data()

    # Assert
    assert not result2.empty
    assert len(result2) == 2
    assert 'title' in result2.columns
    assert 'source' in result2.columns
    assert 'section' in result2.columns
    assert 'published_date' in result2.columns
    assert 'url' in result2.columns
    
    # Verify load_data was not called again
    mock_load_data.assert_not_called()
    
    # Verify both calls return the same DataFrame
    assert result1 is result2


def test_generate_source_chart():
    """Test that generate_source_chart creates a figure with the correct data."""
    # Arrange
    test_df = TEST_DATA.copy()
    
    # Act
    fig = app.generate_source_chart(test_df)
    
    # Assert
    assert fig is not None
    assert hasattr(fig, 'data')
    assert len(fig.data) > 0
    
    # Check if the figure has the expected data
    if hasattr(fig, 'data') and len(fig.data) > 0:
        assert 'x' in fig.data[0]
        assert 'y' in fig.data[0]
        assert 'type' in fig.data[0]
        assert fig.data[0]['type'] == 'bar'
    
    # Check layout
    assert hasattr(fig, 'layout')
    assert 'title' in fig.layout
    assert 'xaxis' in fig.layout
    assert 'yaxis' in fig.layout


def test_generate_section_chart():
    """Test that generate_section_chart creates a figure with the correct data."""
    # Arrange
    test_df = TEST_DATA.copy()
    top_n = 2
    
    # Act
    fig = app.generate_section_chart(test_df, top_n=top_n)
    
    # Assert
    assert fig is not None
    assert hasattr(fig, 'data')
    assert len(fig.data) > 0
    
    # Check if the figure has the expected data
    if hasattr(fig, 'data') and len(fig.data) > 0:
        assert 'x' in fig.data[0]  # Should be a bar chart, not pie
        assert 'y' in fig.data[0]
        assert 'type' in fig.data[0]
        assert fig.data[0]['type'] == 'bar'
    
    # Check layout
    assert hasattr(fig, 'layout')
    assert 'title' in fig.layout
    assert 'xaxis' in fig.layout
    assert 'yaxis' in fig.layout


@patch('app.FPDF')
def test_generate_pdf_report(mock_fpdf, setup_test_environment, tmp_path):
    """Test that generate_pdf_report creates a PDF file."""
    # Arrange
    test_df = TEST_DATA.copy()
    output_path = str(tmp_path / "test_report.pdf")
    
    # Configure the mock FPDF instance
    mock_pdf = MagicMock()
    mock_fpdf.return_value = mock_pdf
    
    # Act
    app.generate_pdf_report(test_df, output_path)
    
    # Assert that FPDF was instantiated
    mock_fpdf.assert_called_once()
    
    # Assert that the PDF methods were called with expected arguments
    mock_pdf.add_page.assert_called_once()
    
    # Check that output was called with the correct path
    mock_pdf.output.assert_called_once()
    args, kwargs = mock_pdf.output.call_args
    assert args[0] == output_path


def test_main_flow_with_data(setup_test_environment):
    """Test the main application flow when data is available."""
    # Arrange
    mock_load_data = setup_test_environment
    
    # Set up the mock to return test data
    mock_load_data.return_value = TEST_DATA.copy()

    # Act - Simulate the main application flow
    result = app.get_data()

    # Assert
    mock_load_data.assert_called_once()
    assert not result.empty
    assert 'df' in st.session_state
    assert not st.session_state.df.empty
    
    # Verify the session state was updated
    assert st.session_state.df is result
    
    # Test session state caching
    mock_load_data.reset_mock()
    cached_result = app.get_data()
    mock_load_data.assert_not_called()
    assert not cached_result.empty


@patch('app.st.warning')
def test_main_flow_no_data(mock_warning, setup_test_environment):
    """Test the main application flow when no data is available."""
    # Arrange
    mock_load_data = setup_test_environment
    mock_load_data.return_value = pd.DataFrame()  # Empty DataFrame
    
    # Reset the session state
    st.session_state.clear()
    
    # Act - Simulate the main application flow
    result = app.get_data()
    
    # Assert
    mock_load_data.assert_called_once()
    assert 'df' in st.session_state
    assert st.session_state.df.empty
    assert result.empty
    
    # Test that the UI handles empty data gracefully
    app.main()
    
    # Verify warning was shown
    mock_warning.assert_called_once()
    
    # Verify the warning message is about no data matching filters
    args, kwargs = mock_warning.call_args
    assert 'No hay datos que coincidan con los filtros seleccionados' in args[0]


@patch('app.os.unlink')
@patch('builtins.open', new_callable=mock_open)
@patch('app.st.selectbox')
@patch('app.st.success')
@patch('app.st.sidebar')
def test_export_functions(mock_sidebar, mock_success, mock_selectbox, mock_file_open, mock_unlink, setup_test_environment, tmp_path):
    """Test the export functionality."""
    # Setup test data
    test_df = TEST_DATA.copy()
    test_df['published_date'] = pd.to_datetime(test_df['published_date'])
    
    # Mock the session state
    st.session_state.df = test_df
    
    # Create a mock for the download button
    mock_download_button = MagicMock(return_value=True)
    mock_sidebar.download_button = mock_download_button
    
    # Mock the tempfile.NamedTemporaryFile
    mock_temp_file = MagicMock()
    mock_temp_file.name = str(tmp_path / 'temp_file')
    
    # Create a real temporary file for testing
    temp_file_path = tmp_path / 'temp_file.csv'
    temp_file_path.write_text('test data')
    
    # Mock the return value of NamedTemporaryFile
    with patch('tempfile.NamedTemporaryFile', return_value=mock_temp_file) as mock_tempfile:
        # Mock the __enter__ method to return the mock file
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file
        
        # Test CSV export
        with patch('pandas.DataFrame.to_csv') as mock_to_csv:
            # Mock the button to return True only for CSV button
            mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Exportar a CSV"
            
            # Reset mocks
            mock_download_button.reset_mock()
            mock_success.reset_mock()
            
            # Call the export function
            app.export_data(test_df)
            
            # Verify to_csv was called
            mock_to_csv.assert_called_once()
            
            # Verify download button was called once for the download
            assert mock_download_button.call_count == 1, f"Expected 1 call, got {mock_download_button.call_count}"
            
            # Verify success message was shown
            mock_success.assert_called_with("Datos exportados a CSV exitosamente")
        
        # Test Excel export
        with patch('pandas.DataFrame.to_excel') as mock_to_excel:
            # Mock the button to return True only for Excel button
            mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Exportar a Excel"
            
            # Reset mocks
            mock_download_button.reset_mock()
            mock_success.reset_mock()
            
            # Call the export function for Excel
            app.export_data(test_df)
            
            # Verify to_excel was called
            mock_to_excel.assert_called_once()
            
            # Verify download button was called once for the download
            assert mock_download_button.call_count == 1, f"Expected 1 call, got {mock_download_button.call_count}"
            
            # Verify success message was shown
            mock_success.assert_called_with("Datos exportados a Excel exitosamente")
        
        # Test PDF export
        with patch('app.generate_pdf_report') as mock_generate_pdf:
            # Mock the button to return True only for PDF button
            mock_sidebar.button.side_effect = lambda label, **kwargs: label == "Generar Informe PDF"
            
            # Reset mocks
            mock_download_button.reset_mock()
            mock_success.reset_mock()
            
            # Call the export function for PDF
            app.export_data(test_df)
            
            # Verify generate_pdf_report was called
            mock_generate_pdf.assert_called_once()
            
            # Verify download button was called once for the download
            assert mock_download_button.call_count == 1, f"Expected 1 call, got {mock_download_button.call_count}"
            
            # Verify success message was shown
            mock_success.assert_called_with("Informe PDF generado exitosamente")




def test_setup_sidebar_filters():
    """Test the setup_sidebar_filters function."""
    # Create test data
    test_df = pd.DataFrame({
        'title': ['Article 1', 'Article 2', 'Article 3'],
        'source': ['Source A', 'Source B', 'Source A'],
        'section': ['Section 1', 'Section 2', 'Section 1'],
        'published_date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
        'url': ['http://example.com/1', 'http://example.com/2', 'http://example.com/3']
    })
    
    # Mock st.sidebar methods
    with patch('app.st.sidebar') as mock_sidebar:
        # Configure the mock
        mock_sidebar.selectbox.return_value = 'Source A'
        mock_sidebar.date_input.return_value = (
            pd.Timestamp('2023-01-01').to_pydatetime(),
            pd.Timestamp('2023-01-03').to_pydatetime()
        )
        
        # Call the function
        filters = app.setup_sidebar_filters(test_df)
        
        # Assert the expected filters were set
        assert filters['source'] == 'Source A'
        # Convert to datetime.date for comparison
        start_date = pd.Timestamp(filters['start_date']).date() if not isinstance(filters['start_date'], pd.Timestamp) else filters['start_date'].date()
        end_date = pd.Timestamp(filters['end_date']).date() if not isinstance(filters['end_date'], pd.Timestamp) else filters['end_date'].date()
        assert start_date == pd.Timestamp('2023-01-01').date()
        assert end_date == pd.Timestamp('2023-01-03').date()
        
        # Verify the selectbox was called with the correct arguments
        mock_sidebar.selectbox.assert_called_once_with(
            'Fuente',
            ['Todos', 'Source A', 'Source B'],
            index=0
        )


def test_apply_filters():
    """Test the apply_filters function."""
    # Create test data
    test_df = pd.DataFrame({
        'title': ['Article 1', 'Article 2', 'Article 3', 'Article 4'],
        'source': ['Source A', 'Source B', 'Source A', 'Source C'],
        'section': ['Section 1', 'Section 2', 'Section 1', 'Section 3'],
        'published_date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']),
        'url': ['http://example.com/1', 'http://example.com/2', 'http://example.com/3', 'http://example.com/4']
    })
    
    # Test filter by source
    filters = {'source': 'Source A'}
    # Asegurarse de que el DataFrame tenga la columna 'source'
    filtered_df = app.apply_filters(test_df, filters)
    assert len(filtered_df) == 2
    assert all(filtered_df['source'] == 'Source A')
    
    # Test filter by date range
    filters = {
        'start_date': pd.Timestamp('2023-01-02').date(),
        'end_date': pd.Timestamp('2023-01-03').date()
    }
    filtered_df = app.apply_filters(test_df, filters)
    assert len(filtered_df) == 2
    assert all(filtered_df['published_date'].dt.date >= pd.Timestamp('2023-01-02').date())
    assert all(filtered_df['published_date'].dt.date <= pd.Timestamp('2023-01-03').date())
    
    # Test filter by both source and date
    filters = {
        'source': 'Source A',
        'start_date': pd.Timestamp('2023-01-02').date(),
        'end_date': pd.Timestamp('2023-01-03').date()
    }
    filtered_df = app.apply_filters(test_df, filters)
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['title'] == 'Article 3'
    
    # Test with no filters (should return all data)
    filtered_df = app.apply_filters(test_df, {})
    assert len(filtered_df) == 4  # No filters, all rows should be returned



