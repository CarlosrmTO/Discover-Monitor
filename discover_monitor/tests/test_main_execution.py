"""Test the main module execution."""
import os
import sys
import importlib.util
import subprocess
from pathlib import Path
import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_main_execution():
    """Test that the main module can be imported and has the expected functions."""
    # Get the path to the main module
    main_path = project_root / "main.py"
    
    # Check if the file exists
    assert main_path.exists(), f"{main_path} does not exist"
    
    # Import the module directly
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", str(main_path))
    main_module = importlib.util.module_from_spec(spec)
    
    # This will execute the module's code, including the if __name__ == "__main__" block
    # but since we're not running it as __main__, it won't execute the argument parsing
    spec.loader.exec_module(main_module)
    
    # Verify the module has the expected functions
    assert hasattr(main_module, 'main'), "main function not found"
    assert hasattr(main_module, 'parse_arguments'), "parse_arguments function not found"
    assert hasattr(main_module, 'check_requirements'), "check_requirements function not found"

def test_main_import():
    """Test that the main module can be imported."""
    # Import the module directly
    spec = importlib.util.spec_from_file_location(
        "main", 
        str(project_root / "main.py")
    )
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)
    
    # Check that the main function exists
    assert hasattr(main_module, "main"), "main function not found"
    assert callable(main_module.main), "main is not callable"
