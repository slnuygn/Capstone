#!/usr/bin/env python3
"""
Auto-sync script for ft_databrowser_modified.m

Checks if ft_databrowser_modified.m is updated, if so updates original ft_databrowser.
If not updated, prints "up to date".
"""

import os
import re
from pathlib import Path

def auto_sync():
    """Check if modified file is updated, sync if needed"""
    
    # File paths
    script_dir = Path(__file__).parent
    modified_file = script_dir / "preprocessing" / "ft_databrowser_modified.m"
    
    # Find FieldTrip path from preprocessing.m
    preprocessing_file = script_dir / "preprocessing" / "preprocessing.m"
    fieldtrip_path = None
    
    if preprocessing_file.exists():
        with open(preprocessing_file, 'r') as f:
            content = f.read()
            pattern = r"addpath\('([^']+)'\).*FieldTrip"
            match = re.search(pattern, content)
            if match:
                fieldtrip_path = Path(match.group(1))
    
    if not fieldtrip_path:
        fieldtrip_path = Path("C:/FIELDTRIP")
    
    original_file = fieldtrip_path / "ft_databrowser.m"
    
    # Check files exist
    if not modified_file.exists():
        print(f"Error: {modified_file} not found!")
        return
    
    if not original_file.exists():
        print(f"Error: {original_file} not found!")
        return
    
    # Check if modified file is newer than original
    modified_time = os.path.getmtime(modified_file)
    original_time = os.path.getmtime(original_file)
    
    if modified_time <= original_time:
        print("up to date")
        return
    
    # Update needed - sync files
    try:
        # Read modified file and remove our initialization block
        with open(modified_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove our custom FieldTrip initialization
        init_pattern = r'% Initialize FieldTrip using the recommended method.*?end\n\n'
        content = re.sub(init_pattern, '', content, flags=re.DOTALL)
        
        # Write to original file
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated: {original_file}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    auto_sync()