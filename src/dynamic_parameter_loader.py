#!/usr/bin/env python3
"""
Dynamic Parameter Loader for MATLAB Analysis Modules
This script parses MATLAB files and generates UI component configurations.
"""

import sys
import os
import json
from matlab_parameter_parser import MatlabParameterParser, ModuleParameterMapper, create_ui_component

def get_module_parameters(module_name: str) -> dict:
    """Get parameter configurations for a specific module."""
    parser = MatlabParameterParser()
    mapper = ModuleParameterMapper()

    matlab_file = mapper.get_matlab_file(module_name)
    if not matlab_file:
        return {}

    # Convert relative path to absolute path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level from src/
    matlab_file_path = os.path.join(project_root, matlab_file)

    parameters = parser.parse_file(matlab_file_path)

    # Convert parameters to UI components
    ui_components = {}
    for param_name, param_info in parameters.items():
        ui_components[param_name] = create_ui_component(param_name, param_info)

    return ui_components

def main():
    if len(sys.argv) < 2:
        print("Usage: python dynamic_parameter_loader.py <module_name>")
        sys.exit(1)

    module_name = sys.argv[1]
    parameters = get_module_parameters(module_name)

    # Output as JSON for QML to consume
    print(json.dumps(parameters, indent=2))

if __name__ == "__main__":
    main()