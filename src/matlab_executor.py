import os
import sys
import subprocess
import re
import threading
import json
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import scipy.io

# Function to get the resource path (works for both development and PyInstaller)
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MatlabWorkerThread(QThread):
    """Worker thread for running MATLAB commands in the background"""
    finished = pyqtSignal(dict)  # Emits result dictionary
    
    def __init__(self, matlab_path, preprocessing_dir):
        super().__init__()
        self.matlab_path = matlab_path
        self.preprocessing_dir = preprocessing_dir
        
    def run(self):
        """Run MATLAB preprocessing in background thread"""
        try:
            # Run MATLAB with the preprocessing script
            cmd = [
                self.matlab_path, 
                '-batch', 
                f"cd('{self.preprocessing_dir.replace(chr(92), '/')}'); preprocessing"
            ]
            
            print(f"Running MATLAB command in background: {' '.join(cmd)}")
            
            # Run the command in the background
            result = subprocess.run(
                cmd,
                capture_output=True, 
                text=True, 
                timeout=600,  # 10 minute timeout (increased from 5)
                cwd=self.preprocessing_dir,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Emit the result
            self.finished.emit({
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            })
            
        except subprocess.TimeoutExpired:
            self.finished.emit({
                'returncode': -1,
                'stdout': '',
                'stderr': 'Process timed out after 10 minutes'
            })
        except Exception as e:
            self.finished.emit({
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            })


class MatlabExecutor(QObject):
    """Class to handle MATLAB script execution and communicate with QML"""
    
    # Signal to send output to QML
    outputChanged = pyqtSignal(str)
    configSaved = pyqtSignal(str)  # Signal for save confirmation
    fileExplorerRefresh = pyqtSignal()  # Signal to refresh file explorer
    processingFinished = pyqtSignal()  # Signal when ICA processing is complete
    
    def __init__(self):
        super().__init__()
        self._output = "No MATLAB output yet..."
        # Load the current data directory from the MATLAB script at startup
        self._current_data_dir = self.getCurrentDataDirectory()
        self._worker_thread = None  # For background MATLAB execution
        self._project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._preprocessing_qml_path = os.path.join(
            self._project_root,
            "features",
            "preprocessing",
            "ui",
            "preprocessing_page.qml",
        )

    def _update_dropdown_state_in_qml(self, dropdown_id: str, new_state: str) -> bool:
        """Update the dropdownState property for a specific dropdown in the QML file."""
        try:
            if not os.path.exists(self._preprocessing_qml_path):
                print(f"QML file not found when updating state: {self._preprocessing_qml_path}")
                return False

            with open(self._preprocessing_qml_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Match the specific dropdown block and replace its dropdownState value
            pattern = rf'(id\s*:\s*{re.escape(dropdown_id)}[\s\S]*?dropdownState\s*:\s*")(?:[^"]+)(")'
            new_content, count = re.subn(pattern, rf'\1{new_state}\2', content, count=1)

            if count == 0:
                print(f"Could not update dropdownState for {dropdown_id} in QML file")
                return False

            with open(self._preprocessing_qml_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            return True

        except Exception as e:
            print(f"Error updating dropdown state for {dropdown_id}: {str(e)}")
            return False

    @pyqtSlot(str, str, result=bool)
    def setDropdownState(self, dropdown_id: str, new_state: str) -> bool:
        """Public slot for QML to persist dropdown state changes."""
        return self._update_dropdown_state_in_qml(dropdown_id, new_state)

    # ------------------------------------------------------------------
    # Custom dropdown persistence helpers
    # ------------------------------------------------------------------

    def _escape_qml_string(self, value: str) -> str:
        return value.replace('\\', '\\\\').replace('"', '\\"') if value else ""

    def _format_qml_list(self, items) -> str:
        if not items:
            return "[]"
        escaped = [f'"{self._escape_qml_string(str(item))}"' for item in items if str(item)]
        return "[" + ", ".join(escaped) + "]"

    def _coerce_to_list(self, payload) -> list:
        if isinstance(payload, (list, tuple)):
            return [str(item) for item in payload if str(item)]

        if isinstance(payload, str):
            stripped = payload.strip()
            if not stripped:
                return []

            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed if str(item)]
            except json.JSONDecodeError:
                items = [item.strip() for item in stripped.split(',') if item.strip()]
                if items:
                    return items

            return [stripped]

        return []

    def _get_custom_dropdown_block_positions(self, content: str):
        pattern = re.compile(r'(\n\s*DropdownTemplate\s*\{\s*id\s*:\s*(customDropdown\d+)[\s\S]*?\n\s*\})')
        positions = {}
        for match in pattern.finditer(content):
            block_id = match.group(2)
            positions[block_id] = (match.start(1), match.end(1))
        return positions

    def _locate_custom_container_bounds(self, content: str):
        marker = "id: customDropdownContainer"
        marker_index = content.find(marker)
        if marker_index == -1:
            return -1, -1

        open_brace_index = content.rfind('{', 0, marker_index)
        if open_brace_index == -1:
            return -1, -1

        depth = 0
        for idx in range(open_brace_index, len(content)):
            char = content[idx]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return open_brace_index, idx
        return open_brace_index, -1

    def _next_custom_dropdown_index(self, existing_ids) -> int:
        max_index = 0
        for dropdown_id in existing_ids:
            try:
                suffix = int(re.findall(r'(\d+)$', dropdown_id)[0])
                max_index = max(max_index, suffix)
            except (IndexError, ValueError):
                continue
        return max_index + 1 if max_index >= 0 else 1

    def _build_custom_dropdown_snippet(
        self,
        dropdown_id: str,
        label: str,
        matlab_property: str,
        is_multi_select: bool,
        max_selections: int,
        all_items,
        selected_items,
    ) -> str:
        label = label.strip() or dropdown_id
        matlab_property = matlab_property.strip()
        if matlab_property and not matlab_property.startswith("cfg."):
            matlab_property = f"cfg.{matlab_property}"

        all_items_list = self._coerce_to_list(all_items)
        selected_items_list = self._coerce_to_list(selected_items)

        qml_all_items = self._format_qml_list(all_items_list)
        qml_selected_items = self._format_qml_list(selected_items_list)
        qml_model = "[]" if is_multi_select else qml_all_items

        escaped_label = self._escape_qml_string(label)
        escaped_property = self._escape_qml_string(matlab_property)

        lines = [
            "",
            "            DropdownTemplate {",
            f"                id: {dropdown_id}",
            f"                property string persistentId: \"{dropdown_id}\"",
            f"                property string customLabel: \"{escaped_label}\"",
            "                property bool persistenceConnected: false",
            f"                label: \"{escaped_label}\"",
            f"                matlabProperty: \"{escaped_property}\"",
            f"                matlabPropertyDraft: \"{escaped_property}\"",
            "                hasAddFeature: true",
            f"                isMultiSelect: {'true' if is_multi_select else 'false'}",
            f"                maxSelections: {max_selections}",
            f"                model: {qml_model}",
            f"                allItems: {qml_all_items}",
            f"                selectedItems: {qml_selected_items}",
            '                addPlaceholder: "Add option..."',
            '                dropdownState: "default"',
            '                anchors.left: parent.left',
            "            }\n",
        ]

        return "\n".join(lines)

    def _insert_custom_dropdown_snippet(self, content: str, snippet: str):
        start, end = self._locate_custom_container_bounds(content)
        if start == -1 or end == -1:
            print("Custom dropdown container not found in QML when inserting snippet.")
            return content, False

        insertion_point = end
        updated_content = content[:insertion_point] + snippet + content[insertion_point:]
        return updated_content, True

    def _replace_custom_dropdown_block(self, content: str, dropdown_id: str, snippet: str):
        positions = self._get_custom_dropdown_block_positions(content)
        if dropdown_id not in positions:
            return content, False

        start, end = positions[dropdown_id]
        snippet_to_use = snippet if snippet.startswith("\n") else "\n" + snippet
        updated_content = content[:start] + snippet_to_use + content[end:]
        return updated_content, True

    def _remove_custom_dropdown_block(self, content: str, dropdown_id: str):
        positions = self._get_custom_dropdown_block_positions(content)
        if dropdown_id not in positions:
            return content, False

        start, end = positions[dropdown_id]
        updated_content = content[:start] + content[end:]
        return updated_content, True
    
    @pyqtSlot(result=float)
    def getCurrentPrestim(self):
        """Read the current prestim value from preprocess_data.m"""
        try:
            script_path = resource_path("preprocessing/preprocess_data.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            pattern = r'cfg\.trialdef\.prestim\s*=\s*([\d.]+);'
            match = re.search(pattern, content)
            if match:
                return float(match.group(1))
            return 0.5  # default fallback
        except:
            return 0.5
    
    @pyqtSlot(result=float)
    def getCurrentPoststim(self):
        """Read the current poststim value from preprocess_data.m"""
        try:
            script_path = resource_path("preprocessing/preprocess_data.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            pattern = r'cfg\.trialdef\.poststim\s*=\s*([\d.]+);'
            match = re.search(pattern, content)
            if match:
                return float(match.group(1))
            return 1.0  # default fallback
        except:
            return 1.0
    
    @pyqtSlot(result=str)
    def getCurrentTrialfun(self):
        """Read the current trialfun value from preprocess_data.m"""
        try:
            script_path = resource_path("preprocessing/preprocess_data.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            pattern = r'cfg\.trialfun\s*=\s*\'([^\']+)\';'
            match = re.search(pattern, content)
            if match:
                return match.group(1)
            return "ft_trialfun_general"  # default fallback
        except:
            return "ft_trialfun_general"
    
    @pyqtSlot(result=str)
    def getCurrentEventtype(self):
        """Read the current eventtype value from preprocess_data.m"""
        try:
            script_path = resource_path("preprocessing/preprocess_data.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            pattern = r'cfg\.trialdef\.eventtype\s*=\s*\'([^\']+)\';'
            match = re.search(pattern, content)
            if match:
                return match.group(1)
            return "Stimulus"  # default fallback
        except:
            return "Stimulus"
    
    @pyqtSlot(result=list)
    def getCurrentEventvalue(self):
        """Read the current eventvalue array from preprocess_data.m"""
        try:
            script_path = resource_path("preprocessing/preprocess_data.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            pattern = r'cfg\.trialdef\.eventvalue\s*=\s*\{([^}]+)\};'
            match = re.search(pattern, content)
            if match:
                # Extract the values and clean them up
                values_str = match.group(1)
                # Remove quotes and split by spaces/commas
                values = re.findall(r"'([^']+)'", values_str)
                return values
            return ["S200", "S201", "S202"]  # default fallback
        except:
            return ["S200", "S201", "S202"]
    
    @pyqtSlot(result=bool)
    def getCurrentDemean(self):
        """Read the current demean setting from preprocess_data.m"""
        try:
            script_path = resource_path("preprocessing/preprocess_data.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            pattern = r'cfg\.demean\s*=\s*\'([^\']+)\';'
            match = re.search(pattern, content)
            if match:
                return match.group(1).lower() == 'yes'
            return True  # default to True (yes)
        except:
            return True
    
    @pyqtSlot(result=list)
    def getCurrentBaselineWindow(self):
        """Read the current baseline window from preprocess_data.m (including commented lines)"""
        try:
            script_path = resource_path("preprocessing/preprocess_data.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            # First try to find uncommented baseline window
            pattern = r'cfg\.baselinewindow\s*=\s*\[([^\]]+)\];'
            match = re.search(pattern, content)
            
            if match:
                values_str = match.group(1)
                values = [float(x.strip()) for x in values_str.split()]
                return values
            
            # If not found, look for commented baseline window
            commented_pattern = r'%\s*cfg\.baselinewindow\s*=\s*\[([^\]]+)\];'
            commented_match = re.search(commented_pattern, content)
            
            if commented_match:
                values_str = commented_match.group(1)
                values = [float(x.strip()) for x in values_str.split()]
                return values
                
            return [-0.2, 0]  # default values
        except:
            return [-0.2, 0]

    @pyqtSlot(result=bool)
    def getCurrentDftfilter(self):
        """Read the current dftfilter setting from preprocess_data.m"""
        try:
            script_path = resource_path("preprocessing/preprocess_data.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            pattern = r'cfg\.dftfilter\s*=\s*\'([^\']+)\';'
            match = re.search(pattern, content)
            if match:
                return match.group(1).lower() == 'yes'
            return True  # default to True (yes)
        except:
            return True
    
    @pyqtSlot(result=list)
    def getCurrentDftfreq(self):
        """Read the current dftfreq from preprocess_data.m"""
        try:
            script_path = resource_path("preprocessing/preprocess_data.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            pattern = r'cfg\.dftfreq\s*=\s*\[([^\]]+)\];'
            match = re.search(pattern, content)
            if match:
                values_str = match.group(1)
                values = [float(x.strip()) for x in values_str.split()]
                return values
            return [50, 60]  # default values
        except:
            return [50, 60]
    
    @pyqtSlot(result=str)
    def getCurrentDataDirectory(self):
        """Read the current data_dir from preprocessing.m"""
        try:
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "features", "preprocessing", "matlab", "preprocessing.m")
            
            with open(script_path, 'r') as file:
                content = file.read()
            
            # Look for the data_dir line
            import re
            pattern = r"data_dir\s*=\s*'([^']+)';"
            match = re.search(pattern, content)
            
            if match:
                matlab_path = match.group(1)
                
                # Handle file:/// URLs
                if matlab_path.startswith('file:///'):
                    matlab_path = matlab_path[8:]  # Remove file:/// prefix
                    matlab_path = matlab_path.replace('/', '\\')  # Convert to Windows paths
                
                return matlab_path
            else:
                # If no path found or using pwd, return empty string
                return ""
                
        except Exception as e:
            print(f"Error reading current data directory: {str(e)}")
            return ""
    
    @pyqtSlot(str)
    def updateDataDirectory(self, folder_path):
        """Update the data_dir in preprocessing.m with the selected folder path"""
        try:
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "features", "preprocessing", "matlab", "preprocessing.m")
            
            # Convert QML URL to local path if needed
            if folder_path.startswith("file:///"):
                folder_path = folder_path[8:]  # Remove file:/// prefix
            
            # Read the current file
            with open(script_path, 'r') as file:
                content = file.read()
            
            # Replace the data_dir line
            if folder_path.strip():  # If a folder is selected
                # Convert Windows path to MATLAB format (forward slashes work in MATLAB)
                matlab_path = folder_path.replace('\\', '/')
                data_dir_pattern = r'data_dir\s*=\s*[^;]+;'
                data_dir_replacement = f"data_dir = '{matlab_path}';"
            else:  # If no folder selected, use pwd
                data_dir_pattern = r'data_dir\s*=\s*[^;]+;'
                data_dir_replacement = "data_dir = pwd;"
            
            content = re.sub(data_dir_pattern, data_dir_replacement, content)
            
            # Write the updated content back to the file
            with open(script_path, 'w') as file:
                file.write(content)
            
            success_msg = f"Data directory updated to: {folder_path if folder_path.strip() else 'pwd (current directory)'}"
            print(success_msg)
            
        except Exception as e:
            error_msg = f"Error updating data directory: {str(e)}"
            print(error_msg)

    @pyqtSlot(result=str)
    def getCurrentFieldtripPath(self):
        """Read the current FieldTrip path from preprocessing.m"""
        try:
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "features", "preprocessing", "matlab", "preprocessing.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            # Look for the addpath line with FieldTrip
            pattern = r"addpath\('([^']+)'\);"
            match = re.search(pattern, content)
            if match:
                fieldtrip_path = match.group(1)
                # Convert forward slashes to backslashes for Windows display
                return fieldtrip_path.replace('/', '\\')
            return "C:\\FIELDTRIP"  # default fallback
        except Exception as e:
            print(f"Error reading FieldTrip path: {e}")
            return "C:\\FIELDTRIP"

    @pyqtSlot(str)
    def updateFieldtripPath(self, folder_path):
        """Update the FieldTrip path in preprocessing.m with the selected folder path"""
        try:
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "features", "preprocessing", "matlab", "preprocessing.m")
            
            # Convert QML URL to local path if needed
            if folder_path.startswith("file:///"):
                folder_path = folder_path[8:]  # Remove file:/// prefix
            
            # Read the current file
            with open(script_path, 'r') as file:
                content = file.read()
            
            # Convert Windows path to MATLAB format (forward slashes work in MATLAB)
            matlab_path = folder_path.replace('\\', '/')
            
            # Replace the addpath line
            addpath_pattern = r"addpath\('([^']+)'\);"
            addpath_replacement = f"addpath('{matlab_path}');"
            
            content = re.sub(addpath_pattern, addpath_replacement, content)
            
            # Write the updated content back to the file
            with open(script_path, 'w') as file:
                file.write(content)
            
            success_msg = f"FieldTrip path updated to: {folder_path}"
            print(success_msg)
            self.configSaved.emit(success_msg)
            
        except Exception as e:
            error_msg = f"Error updating FieldTrip path: {str(e)}"
            print(error_msg)
            self.configSaved.emit(error_msg)

    @pyqtSlot(float, float, str, str, list, list, bool, float, float, bool, float, float)
    def saveConfiguration(self, prestim_value, poststim_value, trialfun_value, eventtype_value, selected_channels, eventvalue_list, demean_enabled, baseline_start, baseline_end, dftfilter_enabled, dftfreq_start, dftfreq_end):
        """Save prestim, poststim, trialfun, eventtype, eventvalue, demean, baseline window, dftfilter, dftfreq, and selected channels to the MATLAB script"""
        try:
            script_path = resource_path("preprocessing/preprocess_data.m")
            
            # Read the current file
            with open(script_path, 'r') as file:
                content = file.read()
            
            # Replace the prestim line
            prestim_pattern = r'cfg\.trialdef\.prestim\s*=\s*[\d.]+;\s*%\s*in\s*seconds'
            prestim_replacement = f'cfg.trialdef.prestim    = {prestim_value:.1f}; % in seconds'
            content = re.sub(prestim_pattern, prestim_replacement, content)
            
            # Replace the poststim line
            poststim_pattern = r'cfg\.trialdef\.poststim\s*=\s*[\d.]+;\s*%\s*in\s*seconds'
            poststim_replacement = f'cfg.trialdef.poststim   = {poststim_value:.1f}; % in seconds'
            content = re.sub(poststim_pattern, poststim_replacement, content)
            
            # Replace the trialfun line
            trialfun_pattern = r'cfg\.trialfun\s*=\s*\'[^\']+\';\s*%.*'
            trialfun_replacement = f'cfg.trialfun             = \'{trialfun_value}\';     % it will call your function and pass the cfg'
            content = re.sub(trialfun_pattern, trialfun_replacement, content)
            
            # Replace the eventtype line
            eventtype_pattern = r'cfg\.trialdef\.eventtype\s*=\s*\'[^\']+\';'
            eventtype_replacement = f'cfg.trialdef.eventtype  = \'{eventtype_value}\';'
            content = re.sub(eventtype_pattern, eventtype_replacement, content)
            
            # Replace the eventvalue line
            if eventvalue_list:
                eventvalue_str = "' '".join(eventvalue_list)
                eventvalue_replacement = f"cfg.trialdef.eventvalue = {{'{eventvalue_str}'}};"
            else:
                eventvalue_replacement = "cfg.trialdef.eventvalue = {'S200' 'S201' 'S202'};"
            
            eventvalue_pattern = r'cfg\.trialdef\.eventvalue\s*=\s*\{[^}]+\};'
            content = re.sub(eventvalue_pattern, eventvalue_replacement, content)
            
            # Replace the demean line
            demean_value = 'yes' if demean_enabled else 'no'
            demean_pattern = r"cfg\.demean\s*=\s*'[^']*'\s*;"
            demean_replacement = f"cfg.demean = '{demean_value}';"
            content = re.sub(demean_pattern, demean_replacement, content)
            
            # Handle the baseline window line based on demean setting
            if demean_enabled:
                # Uncomment and update the baseline window line if demean is enabled
                # First handle commented lines
                commented_baseline_pattern = r'%\s*cfg\.baselinewindow\s*=\s*\[[^\]]*\]\s*;'
                baseline_replacement = f'cfg.baselinewindow = [{baseline_start:.1f} {baseline_end:.1f}];'
                content = re.sub(commented_baseline_pattern, baseline_replacement, content)
                
                # Then handle uncommented lines  
                baseline_pattern = r'cfg\.baselinewindow\s*=\s*\[[^\]]*\]\s*;'
                content = re.sub(baseline_pattern, baseline_replacement, content)
            else:
                # Comment out the baseline window line if demean is disabled
                baseline_pattern = r'cfg\.baselinewindow\s*=\s*\[[^\]]*\]\s*;'
                baseline_replacement = f'% cfg.baselinewindow = [{baseline_start:.1f} {baseline_end:.1f}];'
                content = re.sub(baseline_pattern, baseline_replacement, content)
            
            # Handle the dftfilter line
            dftfilter_value = 'yes' if dftfilter_enabled else 'no'
            dftfilter_pattern = r"cfg\.dftfilter\s*=\s*'[^']*'\s*;"
            dftfilter_replacement = f"cfg.dftfilter = '{dftfilter_value}';"
            content = re.sub(dftfilter_pattern, dftfilter_replacement, content)
            
            # Handle the dftfreq line based on dftfilter setting
            if dftfilter_enabled:
                # Uncomment and update the dftfreq line if dftfilter is enabled
                # First handle commented lines
                commented_dftfreq_pattern = r'%\s*cfg\.dftfreq\s*=\s*\[[^\]]*\]\s*;'
                dftfreq_replacement = f'cfg.dftfreq = [{dftfreq_start:.0f} {dftfreq_end:.0f}];'
                content = re.sub(commented_dftfreq_pattern, dftfreq_replacement, content)
                
                # Then handle uncommented lines  
                dftfreq_pattern = r'cfg\.dftfreq\s*=\s*\[[^\]]*\]\s*;'
                content = re.sub(dftfreq_pattern, dftfreq_replacement, content)
            else:
                # Comment out the dftfreq line if dftfilter is disabled
                dftfreq_pattern = r'cfg\.dftfreq\s*=\s*\[[^\]]*\]\s*;'
                dftfreq_replacement = f'% cfg.dftfreq = [{dftfreq_start:.0f} {dftfreq_end:.0f}];'
                content = re.sub(dftfreq_pattern, dftfreq_replacement, content)
            
            # Write the updated content back to the file
            with open(script_path, 'w') as file:
                file.write(content)
            
            # Also update the preprocessing.m file with selected channels
            self.updateSelectedChannels(selected_channels)
            
            baseline_info = f" baseline: [{baseline_start:.1f} {baseline_end:.1f}]" if demean_enabled else ""
            success_msg = f"Configuration saved!\nprestim: {prestim_value:.1f}s, poststim: {poststim_value:.1f}s\ntrialfun: {trialfun_value}\neventtype: {eventtype_value}\neventvalue: {', '.join(eventvalue_list)}\ndemean: {'yes' if demean_enabled else 'no'}{baseline_info}\nchannels: {', '.join(selected_channels)}"
            print(success_msg)
            self.configSaved.emit(success_msg)
            
        except Exception as e:
            error_msg = f"Error saving configuration: {str(e)}"
            print(error_msg)
            self.configSaved.emit(error_msg)
    
    @pyqtSlot(list)
    def updateSelectedChannels(self, selected_channels):
        """Update the accepted_channels in preprocessing.m with the selected channels"""
        try:
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "features", "preprocessing", "matlab", "preprocessing.m")
            
            # Read the current file
            with open(script_path, 'r') as file:
                content = file.read()
            
            # Format the channels as a MATLAB cell array
            if selected_channels:
                channels_str = "', '".join(selected_channels)
                matlab_channels = f"{{'{channels_str}'}}"
            else:
                matlab_channels = "{}"
            
            # Replace the accepted_channels line
            channels_pattern = r'accepted_channels\s*=\s*\{[^}]*\};'
            channels_replacement = f'accepted_channels = {matlab_channels};'
            content = re.sub(channels_pattern, channels_replacement, content)
            
            # Write the updated content back to the file
            with open(script_path, 'w') as file:
                file.write(content)
            
            print(f"Updated channels: {selected_channels}")
            
        except Exception as e:
            error_msg = f"Error updating channels: {str(e)}"
            print(error_msg)
    
    @pyqtSlot(float, float, str, str, list, list, bool, float, float, bool, float, float, str)
    def runAndSaveConfiguration(self, prestim_value, poststim_value, trialfun_value, eventtype_value, selected_channels, eventvalue_list, demean_enabled, baseline_start, baseline_end, dftfilter_enabled, dftfreq_start, dftfreq_end, data_path):
        """Save configuration and then run preprocessing.m with the specified data path"""
        try:
            # First save the configuration using the existing method
            self.saveConfiguration(prestim_value, poststim_value, trialfun_value, eventtype_value, selected_channels, eventvalue_list, demean_enabled, baseline_start, baseline_end, dftfilter_enabled, dftfreq_start, dftfreq_end)
            
            # Update the data directory in preprocessing.m
            self.updateDataDirectory(data_path)
            
            # Execute the preprocessing.m script
            self.executePreprocessing()
            
        except Exception as e:
            error_msg = f"Error in run and save configuration: {str(e)}"
            print(error_msg)
            self.configSaved.emit(error_msg)
    
    @pyqtSlot(str)
    def updateDataDirectory(self, data_path):
        """Update the data_dir path in preprocessing.m"""
        try:
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "features", "preprocessing", "matlab", "preprocessing.m")
            
            # Read the current file
            with open(script_path, 'r') as file:
                content = file.read()
            
            # Replace the data_dir line
            # Convert Windows backslashes to forward slashes for MATLAB
            matlab_path = data_path.replace('\\', '/')
            data_dir_pattern = r"data_dir\s*=\s*'[^']*';"
            data_dir_replacement = f"data_dir = '{matlab_path}';"
            content = re.sub(data_dir_pattern, data_dir_replacement, content)
            
            # Write the updated content back to the file
            with open(script_path, 'w') as file:
                file.write(content)
            
            print(f"Updated data directory to: {matlab_path}")
            
        except Exception as e:
            error_msg = f"Error updating data directory: {str(e)}"
            print(error_msg)
            raise e
    
    @pyqtSlot()
    def executePreprocessing(self):
        """Execute preprocessing.m script in background thread"""
        try:
            print("Starting MATLAB execution of preprocessing.m...")
            
            # Check if another MATLAB process is already running
            if self._worker_thread and self._worker_thread.isRunning():
                self.configSaved.emit("MATLAB processing is already running. Please wait for it to complete.")
                return
            
            # Use the path to your MATLAB installation
            matlab_path = r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe"
            
            # Path to the preprocessing directory
            preprocessing_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "features", "preprocessing")
            matlab_scripts_dir = os.path.join(preprocessing_dir, "matlab")
            
            # Emit a status message that processing has started
            self.configSaved.emit("Configuration saved! Starting MATLAB processing...\nProcessing data files in background.\nThe application will remain responsive during processing.")
            
            # Create and start worker thread
            self._worker_thread = MatlabWorkerThread(matlab_path, preprocessing_dir)
            self._worker_thread.finished.connect(self._onMatlabFinished)
            self._worker_thread.start()
            
            print("MATLAB processing started in background thread")
                
        except Exception as e:
            error_msg = f"Error starting MATLAB processing: {str(e)}"
            print(error_msg)
            self.configSaved.emit(error_msg)
    
    def _onMatlabFinished(self, result):
        """Handle completion of MATLAB processing"""
        try:
            print(f"MATLAB execution completed with return code: {result['returncode']}")
            print(f"STDOUT: {result['stdout']}")
            if result['stderr']:
                print(f"STDERR: {result['stderr']}")
            
            if result['returncode'] == 0:
                # Try to get the RAM contents after processing
                try:
                    # Extract number of files processed from MATLAB output
                    output_lines = result['stdout'].split('\n')
                    num_files = 0
                    for line in output_lines:
                        if 'files processed and stored in workspace variable "data"' in line:
                            # Extract the number from the line
                            import re
                            match = re.search(r'(\d+) files processed', line)
                            if match:
                                num_files = int(match.group(1))
                                break
                    
                    success_msg = f"MATLAB processing completed successfully!\n\nProcessed {num_files} files and saved as 'data_ICA.mat'.\nOriginal files remain unchanged.\n\nMATLAB Output:\n{result['stdout']}"
                except Exception as e:
                    success_msg = f"MATLAB processing completed successfully!\n\nFiles processed and saved as 'data_ICA.mat'.\nOriginal files remain unchanged.\n\nMATLAB Output:\n{result['stdout']}"
                
                self.configSaved.emit(success_msg)
                # Emit signal to refresh file explorer after successful processing
                self.fileExplorerRefresh.emit()
                # Emit signal that processing is finished
                self.processingFinished.emit()
            else:
                if result['stderr'] == 'Process timed out after 10 minutes':
                    timeout_msg = "MATLAB processing timed out (10 minutes). The script may still be running in the background.\nCheck the data folder for any completed files."
                    self.configSaved.emit(timeout_msg)
                else:
                    error_msg = f"MATLAB processing failed with return code {result['returncode']}\n\nError:\n{result['stderr']}\n\nOutput:\n{result['stdout']}"
                    self.configSaved.emit(error_msg)
                # Emit processing finished even on failure
                self.processingFinished.emit()
                    
        except Exception as e:
            error_msg = f"Error handling MATLAB completion: {str(e)}"
            print(error_msg)
            self.configSaved.emit(error_msg)
            # Ensure processing finished signal is always emitted
            self.processingFinished.emit()
    
    @pyqtSlot(str)
    def browseICAComponents(self, data_path):
        """Launch MATLAB ICA component browser using the browse_ICA.m script"""
        try:
            print("Starting MATLAB ICA component browser...")
            
            # Use the path to your MATLAB installation
            matlab_path = r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe"
            
            # Get the preprocessing directory (where browse_ICA.m should be)
            preprocessing_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "features", "preprocessing")
            
            # Create the MATLAB command to run the ICA browser
            matlab_command = f"""
            cd('{data_path.replace(chr(92), '/')}');
            addpath('{preprocessing_dir.replace(chr(92), '/')}');
            if exist('data_ICA.mat', 'file')
                load('data_ICA.mat');
                if exist('data_ICApplied', 'var')
                    data_ICA = data_ICApplied;
                    set(groot, 'DefaultFigureColormap', jet);
                    for i = 1:length(data_ICA)
                        cfg = [];
                        cfg.layout = 'easycapM11.lay';
                        cfg.viewmode = 'component';
                        fprintf('Showing components for subject %d\\n', i);
                        ft_databrowser(cfg, data_ICA(i));
                        pause;
                    end
                    fprintf('ICA component browsing completed.\\n');
                else
                    fprintf('Error: data_ICApplied variable not found in data_ICA.mat\\n');
                end
            else
                fprintf('Error: data_ICA.mat file not found. Please run preprocessing first.\\n');
            end
            """
            
            print(f"Running MATLAB ICA browser command...")
            print(f"Data path: {data_path}")
            print(f"Preprocessing dir: {preprocessing_dir}")
            
            # Execute MATLAB command in a new process (non-blocking)
            import threading
            def run_matlab_browser():
                try:
                    result = subprocess.run([
                        matlab_path, 
                        "-batch", matlab_command
                    ], capture_output=True, text=True, cwd=data_path, timeout=300)
                    
                    print(f"MATLAB ICA browser completed with return code: {result.returncode}")
                    print(f"STDOUT: {result.stdout}")
                    if result.stderr:
                        print(f"STDERR: {result.stderr}")
                        
                    if result.returncode == 0:
                        success_msg = f"ICA component browser completed successfully!\n\nMATLAB Output:\n{result.stdout}"
                    else:
                        success_msg = f"ICA browser finished with some issues.\n\nOutput:\n{result.stdout}\nErrors:\n{result.stderr}"
                    
                    self.configSaved.emit(success_msg)
                    
                except subprocess.TimeoutExpired:
                    timeout_msg = "ICA browser timed out (5 minutes). The browser may still be running in MATLAB."
                    print(timeout_msg)
                    self.configSaved.emit(timeout_msg)
                except Exception as e:
                    error_msg = f"Error running ICA browser: {str(e)}"
                    print(error_msg)
                    self.configSaved.emit(error_msg)
            
            # Start the browser in a separate thread so it doesn't block the UI
            browser_thread = threading.Thread(target=run_matlab_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            # Immediate feedback to user
            self.configSaved.emit("Launching ICA component browser in MATLAB...\nThis may take a moment to start.\nEach subject will display in a separate window.\nPress any key in MATLAB to proceed between subjects.")
            
        except Exception as e:
            error_msg = f"Error launching ICA browser: {str(e)}"
            print(error_msg)
            self.configSaved.emit(error_msg)
    
    @pyqtSlot()
    def executeMatlabScript(self):
        """Execute MATLAB script and emit the output"""
        output = self.execute_matlab_script('helloworld.m')
        if output:
            self._output = output
        else:
            self._output = "MATLAB execution failed or timed out"
        self.outputChanged.emit(self._output)
    
    def execute_matlab_script(self, script_path):
        """Execute MATLAB script and return the output"""
        try:
            print(f"Executing MATLAB script: {script_path}")
            
            # Use your specific MATLAB installation path
            matlab_path = r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe"
            
            # Create the full path to the script
            script_full_path = os.path.abspath(script_path)
            
            # Run MATLAB with a more direct approach
            # Using -batch and -sd to set the startup directory
            cmd = [
                matlab_path, 
                '-batch', 
                f"cd('{os.path.dirname(script_full_path)}'); {os.path.basename(script_path)[:-2]}"  # Remove .m extension
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True, 
                text=True, 
                timeout=20,
                cwd=os.path.dirname(script_full_path),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            print(f"Return code: {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            
            if result.returncode == 0:
                # Process the output
                output = result.stdout.strip()
                if output:
                    # Remove MATLAB licensing and startup info
                    lines = output.split('\n')
                    clean_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and not any(skip in line.lower() for skip in [
                            'matlab', 'copyright', 'license', 'mathworks', 'version', 'release'
                        ]):
                            clean_lines.append(line)
                    
                    final_output = '\n'.join(clean_lines) if clean_lines else "Script executed successfully"
                    return f"MATLAB Output:\n{final_output}"
                else:
                    return "MATLAB Output:\nScript executed successfully (no output)"
            else:
                error_output = result.stderr.strip() if result.stderr.strip() else "Unknown error"
                return f"MATLAB Error:\n{error_output}"
                
        except subprocess.TimeoutExpired:
            return "MATLAB execution timed out (>20 seconds)"
        except FileNotFoundError:
            return f"MATLAB not found at: {matlab_path}\nPlease verify the path is correct."
        except Exception as e:
            return f"Error executing MATLAB script: {str(e)}"
    
    @pyqtSlot(result=list)
    def getCurrentChannels(self):
        """Read the current selected channels from preprocessing.m"""
        try:
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "features", "preprocessing", "matlab", "preprocessing.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            pattern = r'accepted_channels\s*=\s*\{([^}]*)\};'
            match = re.search(pattern, content)
            
            if match:
                channels_str = match.group(1)
                
                # More robust parsing for MATLAB cell array
                # Find all quoted strings in the cell array
                channel_matches = re.findall(r"'([^']*)'", channels_str)
                channels = [ch for ch in channel_matches if ch.strip()]
                
                return channels
            else:
                print("No accepted_channels pattern found, using defaults")
                # Default channels if not found (matching what's typically in the file)
                return ['F4', 'Fz', 'C3', 'Pz', 'P3', 'O1', 'Oz', 'O2', 'P4', 'Cz', 'C4']
        except Exception as e:
            print(f"Error reading current channels: {str(e)}")
            return ['F4', 'Fz', 'C3', 'Pz', 'P3', 'O1', 'Oz', 'O2', 'P4', 'Cz', 'C4']

    @pyqtSlot(list)
    def saveChannelsToScript(self, selected_channels):
        """Save the selected channels to preprocessing.m"""
        try:
            script_path = resource_path("preprocessing/preprocessing.m")
            with open(script_path, 'r') as file:
                content = file.read()
            
            # Format channels as MATLAB cell array
            if selected_channels:
                channels_str = "'" + "', '".join(selected_channels) + "'"
            else:
                channels_str = ""
            
            new_line = f"accepted_channels = {{{channels_str}}};"
            
            # Replace the accepted_channels line
            pattern = r'accepted_channels\s*=\s*\{[^}]*\};'
            if re.search(pattern, content):
                content = re.sub(pattern, new_line, content)
            else:
                # If pattern not found, we might need to add it
                print("Warning: accepted_channels line not found in preprocessing.m")
                return False
            
            with open(script_path, 'w') as file:
                file.write(content)
            
            print(f"Updated channels in preprocessing.m: {selected_channels}")
            return True
            
        except Exception as e:
            print(f"Error saving channels to script: {str(e)}")
            return False
    
    @pyqtSlot(str)
    def addCustomTrialfunOption(self, new_option):
        """Add a new custom trialfun option to the QML file directly"""
        success = False
        try:
            qml_file_path = self._preprocessing_qml_path

            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Find the customModel property line
            pattern = r'property var customModel: (\[.*?\])'
            match = re.search(pattern, content)

            if match:
                current_array_str = match.group(1)

                # Parse the current array (simple parsing for quoted strings)
                import ast
                try:
                    current_array = ast.literal_eval(current_array_str)
                except Exception:
                    # Fallback parsing if ast fails
                    current_array = ["ft_trialfun_general", "alternative"]

                # Add the new option if it's not already there
                if new_option not in current_array:
                    current_array.append(new_option)

                    # Create the new array string
                    new_array_str = '["' + '", "'.join(current_array) + '"]'

                    # Replace in the content
                    new_content = re.sub(pattern, f'property var customModel: {new_array_str}', content)

                    # Write back to file
                    with open(qml_file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)

                    print(f"Added '{new_option}' to QML customModel")
                    success = True

        except Exception as e:
            print(f"Error adding custom trialfun option to QML: {str(e)}")
        finally:
            self._update_dropdown_state_in_qml("trialfunDropdown", "default")

        return success
    
    @pyqtSlot(str, int)
    def saveTrialfunSelection(self, selected_option, selected_index):
        """Save the selected trialfun option and index to the QML file"""
        success = False
        try:
            qml_file_path = self._preprocessing_qml_path

            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Update the currentIndex in the QML file
            index_pattern = r'currentIndex: \d+'
            new_content = re.sub(index_pattern, f'currentIndex: {selected_index}', content)

            # Write back to file
            with open(qml_file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            print(f"Saved trialfun selection: '{selected_option}' at index {selected_index}")
            success = True

        except Exception as e:
            print(f"Error saving trialfun selection to QML: {str(e)}")
        finally:
            self._update_dropdown_state_in_qml("trialfunDropdown", "default")

        return success
    
    @pyqtSlot(str)
    def addCustomEventtypeOption(self, new_option):
        """Add a new custom eventtype option to the QML file directly"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Find the eventtype customModel property line
            pattern = r'property var eventtypeCustomModel: (\[.*?\])'
            match = re.search(pattern, content)
            
            if match:
                current_array_str = match.group(1)
                
                # Parse the current array (simple parsing for quoted strings)
                import ast
                try:
                    current_array = ast.literal_eval(current_array_str)
                except:
                    # Fallback parsing if ast fails
                    current_array = ["Stimulus", "alternative"]
                
                # Add the new option if it's not already there
                if new_option not in current_array:
                    current_array.append(new_option)
                    
                    # Create the new array string
                    new_array_str = '["' + '", "'.join(current_array) + '"]'
                    
                    # Replace in the content
                    new_content = re.sub(pattern, f'property var eventtypeCustomModel: {new_array_str}', content)
                    
                    # Write back to file
                    with open(qml_file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    
                    print(f"Added '{new_option}' to QML eventtypeCustomModel")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error adding custom eventtype option to QML: {str(e)}")
            return False
    
    @pyqtSlot(str, int)
    def saveEventtypeSelection(self, selected_option, selected_index):
        """Save the selected eventtype option and index to the QML file"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Update the eventtype currentIndex in the QML file (need to be more specific)
            # Look for the eventtypeComboBox currentIndex specifically
            eventtype_pattern = r'(id: eventtypeComboBox[\s\S]*?currentIndex: )\d+'
            match = re.search(eventtype_pattern, content)
            
            if match:
                new_content = re.sub(eventtype_pattern, f'{match.group(1)}{selected_index}', content)
                
                # Write back to file
                with open(qml_file_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                print(f"Saved eventtype selection: '{selected_option}' at index {selected_index}")
                return True
            else:
                print("Could not find eventtypeComboBox currentIndex pattern")
                return False
            
        except Exception as e:
            print(f"Error saving eventtype selection to QML: {str(e)}")
            return False

    @pyqtSlot(str)
    def launchMatlabICABrowser(self, mat_file_path):
        """Launch MATLAB ft_databrowser for ICA component viewing"""
        try:
            print(f"Launching MATLAB ICA browser for: {mat_file_path}")
            
            # Get the directory containing the .mat file
            data_dir = os.path.dirname(mat_file_path)
            mat_filename = os.path.basename(mat_file_path)
            
            # Debug: Check what's actually in the file
            try:
                import scipy.io as sio
                print(f"Checking contents of: {mat_file_path}")
                mat_data = sio.loadmat(mat_file_path)
                print(f"All variables in file: {list(mat_data.keys())}")
                
                # Look for any variable that might be ICA data (excluding metadata)
                data_vars = [k for k in mat_data.keys() if not k.startswith('__')]
                print(f"Data variables found: {data_vars}")
                
                if not data_vars:
                    print("No data variables found in file")
                    self.configSaved.emit("Error: No data variables found in the .mat file")
                    return
                    
            except Exception as e:
                print(f"Error reading file: {e}")
                self.configSaved.emit(f"Error reading .mat file: {str(e)}")
                return
            
            # Get paths
            preprocessing_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "features", "preprocessing")
            matlab_scripts_dir = os.path.join(preprocessing_dir, "matlab")
            matlab_path = r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe"
            
            # Check if MATLAB exists
            if not os.path.exists(matlab_path):
                error_msg = "MATLAB not found at expected location. Please install MATLAB and try again."
                print(error_msg)
                self.configSaved.emit(error_msg)
                return
            
            # Execute MATLAB command in a new thread (non-blocking)
            import threading
            def run_matlab_ica_browser():
                try:
                    # Use -r flag with desktop mode for GUI interaction
                    matlab_commands = f"""
addpath('{self.getCurrentFieldtripPath().replace(chr(92), '/')}');
ft_defaults;
addpath('{preprocessing_dir.replace(chr(92), '/')}');
addpath(genpath('{matlab_scripts_dir.replace(chr(92), '/')}'));
browse_ICA('{mat_file_path.replace(chr(92), '/')}');
"""
                    
                    print(f"Launching MATLAB with ICA browser...")
                    print(f"MATLAB commands:\\n{matlab_commands}")
                    
                    result = subprocess.run([
                        matlab_path, 
                        "-desktop",
                        "-r", matlab_commands
                    ], timeout=None)  # No timeout for GUI interaction
                    
                    print(f"MATLAB completed with return code: {result.returncode}")
                    
                    if result.returncode == 0:
                        success_msg = "MATLAB ICA browser session completed successfully!"
                    else:
                        success_msg = f"MATLAB session ended with return code: {result.returncode}"
                    
                    self.configSaved.emit(success_msg)
                    
                except subprocess.TimeoutExpired:
                    timeout_msg = "ICA browser session is still running in MATLAB."
                    print(timeout_msg)
                    self.configSaved.emit(timeout_msg)
                except Exception as e:
                    error_msg = f"Error running ICA browser: {str(e)}"
                    print(error_msg)
                    self.configSaved.emit(error_msg)
            
            # Start the browser in a separate thread
            browser_thread = threading.Thread(target=run_matlab_ica_browser)
            browser_thread.daemon = True  # Thread will close when main program closes
            browser_thread.start()
            
            # Immediate feedback to user
            self.configSaved.emit("Launching MATLAB desktop with ICA browser... \n\nA MATLAB window will open shortly. If you don't see it, check your taskbar or use Alt+Tab to find the MATLAB window.")
            
        except Exception as e:
            error_msg = f"Error launching MATLAB ICA browser: {str(e)}"
            print(error_msg)
            self.configSaved.emit(error_msg)

    @pyqtSlot(str)
    def addCustomTrialfunOptionToAllItems(self, new_option):
        """Add a new custom trialfun option to the trialfun dropdown's allItems array"""
        success = False
        try:
            qml_file_path = self._preprocessing_qml_path

            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Find the trialfun allItems array (look for the pattern with ft_trialfun_general)
            pattern = r'allItems: (\["ft_trialfun_general".*?\])'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                current_array_str = match.group(1)

                # Parse the current array
                import ast
                try:
                    current_array = ast.literal_eval(current_array_str)
                except Exception:
                    # Fallback: extract items between quotes
                    items = re.findall(r'"([^"]*)"', current_array_str)
                    current_array = items

                # Add the new option if it's not already there
                if new_option not in current_array:
                    current_array.append(new_option)

                    # Create the new array string
                    new_array_str = '["' + '", "'.join(current_array) + '"]'

                    # Replace in the content
                    new_content = re.sub(pattern, f'allItems: {new_array_str}', content)

                    # Write back to file
                    with open(qml_file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)

                    print(f"Added '{new_option}' to trialfun allItems")
                    success = True

        except Exception as e:
            print(f"Error adding custom trialfun option to allItems: {str(e)}")
        finally:
            self._update_dropdown_state_in_qml("trialfunDropdown", "default")

        return success

    @pyqtSlot(str)
    def addCustomEventtypeOptionToAllItems(self, new_option):
        """Add a new custom eventtype option to the eventtype dropdown's allItems array"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Find the eventtype allItems array (look for the pattern with Stimulus)
            pattern = r'allItems: (\["Stimulus".*?\])'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                current_array_str = match.group(1)
                
                # Parse the current array
                import ast
                try:
                    current_array = ast.literal_eval(current_array_str)
                except:
                    # Fallback: extract items between quotes
                    items = re.findall(r'"([^"]*)"', current_array_str)
                    current_array = items
                
                # Add the new option if it's not already there
                if new_option not in current_array:
                    current_array.append(new_option)
                    
                    # Create the new array string
                    new_array_str = '["' + '", "'.join(current_array) + '"]'
                    
                    # Replace in the content
                    new_content = re.sub(pattern, f'allItems: {new_array_str}', content)
                    
                    # Write back to file
                    with open(qml_file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    
                    print(f"Added '{new_option}' to eventtype allItems")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error adding custom eventtype option to allItems: {str(e)}")
            return False

    @pyqtSlot(str)
    def addCustomEventvalueOptionToAllItems(self, new_option):
        """Add a new custom eventvalue option to the eventvalue dropdown's allItems array"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Find the eventvalue allItems array (look for the pattern with S200)
            pattern = r'allItems: (\["S200".*?\])'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                current_array_str = match.group(1)
                
                # Parse the current array
                import ast
                try:
                    current_array = ast.literal_eval(current_array_str)
                except:
                    # Fallback: extract items between quotes
                    items = re.findall(r'"([^"]*)"', current_array_str)
                    current_array = items
                
                # Add the new option if it's not already there
                if new_option not in current_array:
                    current_array.append(new_option)
                    
                    # Create the new array string
                    new_array_str = '["' + '", "'.join(current_array) + '"]'
                    
                    # Replace in the content
                    new_content = re.sub(pattern, f'allItems: {new_array_str}', content)
                    
                    # Write back to file
                    with open(qml_file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    
                    print(f"Added '{new_option}' to eventvalue allItems")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error adding custom eventvalue option to allItems: {str(e)}")
            return False

    @pyqtSlot(str)
    def addCustomChannelOptionToAllItems(self, new_option):
        """Add a new custom channel option to the channel dropdown's allItems array"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Find the channel allItems array (look for the pattern with Fp1)
            pattern = r'allItems: (\["Fp1".*?\])'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                current_array_str = match.group(1)
                
                # Parse the current array
                import ast
                try:
                    current_array = ast.literal_eval(current_array_str)
                except:
                    # Fallback: extract items between quotes
                    items = re.findall(r'"([^"]*)"', current_array_str)
                    current_array = items
                
                # Add the new option if it's not already there
                if new_option not in current_array:
                    current_array.append(new_option)
                    
                    # Create the new array string
                    new_array_str = '["' + '", "'.join(current_array) + '"]'
                    
                    # Replace in the content
                    new_content = re.sub(pattern, f'allItems: {new_array_str}', content)
                    
                    # Write back to file
                    with open(qml_file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    
                    print(f"Added '{new_option}' to channel allItems")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error adding custom channel option to allItems: {str(e)}")
            return False

    @pyqtSlot(str, str, bool, int, 'QVariant', 'QVariant', result=str)
    def saveCustomDropdown(self, label, matlab_property, is_multi_select, max_selections, all_items, selected_items):
        """Persist a newly created custom dropdown to preprocessing_page.qml and return its assigned id."""
        try:
            if not os.path.exists(self._preprocessing_qml_path):
                print("Preprocessing QML file not found when saving custom dropdown.")
                return ""

            with open(self._preprocessing_qml_path, 'r', encoding='utf-8') as file:
                content = file.read()

            positions = self._get_custom_dropdown_block_positions(content)

            normalized_property = (matlab_property or "").strip()
            if normalized_property and not normalized_property.startswith("cfg."):
                normalized_property = f"cfg.{normalized_property}"
            escaped_property = f'"{self._escape_qml_string(normalized_property)}"'

            # If a dropdown with the same matlab property exists, update it instead of creating duplicate
            for existing_id, (start, end) in positions.items():
                block_text = content[start:end]
                if f'matlabProperty: {escaped_property}' in block_text:
                    snippet = self._build_custom_dropdown_snippet(
                        existing_id,
                        label,
                        normalized_property,
                        is_multi_select,
                        max_selections,
                        all_items,
                        selected_items,
                    )
                    new_content, replaced = self._replace_custom_dropdown_block(content, existing_id, snippet)
                    if replaced:
                        with open(self._preprocessing_qml_path, 'w', encoding='utf-8') as file:
                            file.write(new_content)
                        print(f"Updated existing custom dropdown '{existing_id}' with new settings.")
                    return existing_id

            next_index = self._next_custom_dropdown_index(positions.keys()) or 1
            dropdown_id = f"customDropdown{next_index}"

            snippet = self._build_custom_dropdown_snippet(
                dropdown_id,
                label,
                normalized_property,
                is_multi_select,
                max_selections,
                all_items,
                selected_items,
            )

            new_content, inserted = self._insert_custom_dropdown_snippet(content, snippet)
            if not inserted:
                return ""

            with open(self._preprocessing_qml_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            print(f"Saved new custom dropdown '{dropdown_id}' to QML file.")
            return dropdown_id

        except Exception as e:
            print(f"Error saving custom dropdown: {str(e)}")
            return ""

    @pyqtSlot(str, str, str, bool, int, 'QVariant', 'QVariant', result=bool)
    def updateCustomDropdown(self, dropdown_id, label, matlab_property, is_multi_select, max_selections, all_items, selected_items):
        """Update an existing custom dropdown definition in preprocessing_page.qml."""
        try:
            if not os.path.exists(self._preprocessing_qml_path):
                print("Preprocessing QML file not found when updating custom dropdown.")
                return False

            with open(self._preprocessing_qml_path, 'r', encoding='utf-8') as file:
                content = file.read()

            snippet = self._build_custom_dropdown_snippet(
                dropdown_id,
                label,
                matlab_property,
                is_multi_select,
                max_selections,
                all_items,
                selected_items,
            )

            new_content, replaced = self._replace_custom_dropdown_block(content, dropdown_id, snippet)
            if not replaced:
                print(f"Custom dropdown '{dropdown_id}' not found for update; attempting to append new block.")
                new_content, inserted = self._insert_custom_dropdown_snippet(content, snippet)
                if not inserted:
                    return False

            with open(self._preprocessing_qml_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            print(f"Updated custom dropdown '{dropdown_id}' in QML file.")
            return True

        except Exception as e:
            print(f"Error updating custom dropdown '{dropdown_id}': {str(e)}")
            return False

    @pyqtSlot(str, result=bool)
    def removeCustomDropdown(self, dropdown_id):
        """Remove a custom dropdown definition from preprocessing_page.qml."""
        try:
            if not os.path.exists(self._preprocessing_qml_path):
                print("Preprocessing QML file not found when removing custom dropdown.")
                return False

            with open(self._preprocessing_qml_path, 'r', encoding='utf-8') as file:
                content = file.read()

            new_content, removed = self._remove_custom_dropdown_block(content, dropdown_id)
            if not removed:
                print(f"Custom dropdown '{dropdown_id}' was not found for removal.")
                return False

            with open(self._preprocessing_qml_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            print(f"Removed custom dropdown '{dropdown_id}' from QML file.")
            return True

        except Exception as e:
            print(f"Error removing custom dropdown '{dropdown_id}': {str(e)}")
            return False

    @pyqtSlot(str)
    def deleteCustomTrialfunOptionFromAllItems(self, itemToDelete):
        """Remove a custom trialfun option from the trialfun dropdown's allItems array"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Find the trialfun allItems array (look for the pattern with ft_trialfun_general)
            pattern = r'allItems: (\["ft_trialfun_general".*?\])'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                current_array_str = match.group(1)
                
                # Parse the current array
                import ast
                try:
                    current_array = ast.literal_eval(current_array_str)
                except:
                    # Fallback: extract items between quotes
                    items = re.findall(r'"([^"]*)"', current_array_str)
                    current_array = items
                
                # Remove the item if it exists
                if itemToDelete in current_array:
                    current_array.remove(itemToDelete)
                    
                    # Create the new array string
                    new_array_str = '["' + '", "'.join(current_array) + '"]'
                    
                    # Replace in the content
                    new_content = re.sub(pattern, f'allItems: {new_array_str}', content)
                    
                    # Write back to file
                    with open(qml_file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    
                    print(f"Removed '{itemToDelete}' from trialfun allItems")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error removing custom trialfun option from allItems: {str(e)}")
            return False

    @pyqtSlot(str)
    def deleteCustomEventtypeOptionFromAllItems(self, itemToDelete):
        """Remove a custom eventtype option from the eventtype dropdown's allItems array"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Find the eventtype allItems array (look for the pattern with Stimulus)
            pattern = r'allItems: (\["Stimulus".*?\])'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                current_array_str = match.group(1)
                
                # Parse the current array
                import ast
                try:
                    current_array = ast.literal_eval(current_array_str)
                except:
                    # Fallback: extract items between quotes
                    items = re.findall(r'"([^"]*)"', current_array_str)
                    current_array = items
                
                # Remove the item if it exists
                if itemToDelete in current_array:
                    current_array.remove(itemToDelete)
                    
                    # Create the new array string
                    new_array_str = '["' + '", "'.join(current_array) + '"]'
                    
                    # Replace in the content
                    new_content = re.sub(pattern, f'allItems: {new_array_str}', content)
                    
                    # Write back to file
                    with open(qml_file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    
                    print(f"Removed '{itemToDelete}' from eventtype allItems")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error removing custom eventtype option from allItems: {str(e)}")
            return False

    @pyqtSlot(str)
    def deleteCustomEventvalueOptionFromAllItems(self, itemToDelete):
        """Remove a custom eventvalue option from the eventvalue dropdown's allItems array"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Find the eventvalue allItems array (look for the pattern with S200)
            pattern = r'allItems: (\["S200".*?\])'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                current_array_str = match.group(1)
                
                # Parse the current array
                import ast
                try:
                    current_array = ast.literal_eval(current_array_str)
                except:
                    # Fallback: extract items between quotes
                    items = re.findall(r'"([^"]*)"', current_array_str)
                    current_array = items
                
                # Remove the item if it exists
                if itemToDelete in current_array:
                    current_array.remove(itemToDelete)
                    
                    # Create the new array string
                    new_array_str = '["' + '", "'.join(current_array) + '"]'
                    
                    # Replace in the content
                    new_content = re.sub(pattern, f'allItems: {new_array_str}', content)
                    
                    # Write back to file
                    with open(qml_file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    
                    print(f"Removed '{itemToDelete}' from eventvalue allItems")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error removing custom eventvalue option from allItems: {str(e)}")
            return False

    @pyqtSlot(str)
    def deleteCustomChannelOptionFromAllItems(self, itemToDelete):
        """Remove a custom channel option from the channel dropdown's allItems array"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Find the channel allItems array (look for the pattern with Fp1)
            pattern = r'allItems: (\["Fp1".*?\])'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                current_array_str = match.group(1)
                
                # Parse the current array
                import ast
                try:
                    current_array = ast.literal_eval(current_array_str)
                except:
                    # Fallback: extract items between quotes
                    items = re.findall(r'"([^"]*)"', current_array_str)
                    current_array = items
                
                # Remove the item if it exists
                if itemToDelete in current_array:
                    current_array.remove(itemToDelete)
                    
                    # Create the new array string
                    new_array_str = '["' + '", "'.join(current_array) + '"]'
                    
                    # Replace in the content
                    new_content = re.sub(pattern, f'allItems: {new_array_str}', content)
                    
                    # Write back to file
                    with open(qml_file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    
                    print(f"Removed '{itemToDelete}' from channel allItems")
                    return True
            
            return False
            
            return False
            
        except Exception as e:
            print(f"Error removing custom channel option from allItems: {str(e)}")
            return False

    @pyqtSlot(float, float, float, float)
    def updateBaselineSliderValues(self, from_val, to_val, first_val, second_val):
        """Update the baseline slider values in the QML file"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Update from value
            content = re.sub(r'(id: baselineSlider.*?from:) [\d\.\-]+', f'\\1 {from_val}', content, flags=re.DOTALL)
            
            # Update to value
            content = re.sub(r'(id: baselineSlider.*?to:) [\d\.\-]+', f'\\1 {to_val}', content, flags=re.DOTALL)
            
            # Update firstValue
            content = re.sub(r'(id: baselineSlider.*?firstValue:) [\d\.\-]+', f'\\1 {first_val}', content, flags=re.DOTALL)
            
            # Update secondValue
            content = re.sub(r'(id: baselineSlider.*?secondValue:) [\d\.\-]+', f'\\1 {second_val}', content, flags=re.DOTALL)
            
            # Write back to file
            with open(qml_file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            print(f"Updated baseline slider values: from={from_val}, to={to_val}, firstValue={first_val}, secondValue={second_val}")
            return True
            
        except Exception as e:
            print(f"Error updating baseline slider values: {str(e)}")
            return False

    @pyqtSlot(float, float, float, float)
    def updatePrestimPoststimSliderValues(self, from_val, to_val, first_val, second_val):
        """Update the prestim/poststim slider values in the QML file"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Update from value
            content = re.sub(r'(id: prestimPoststimSlider.*?from:) [\d\.\-]+', f'\\1 {from_val}', content, flags=re.DOTALL)
            
            # Update to value
            content = re.sub(r'(id: prestimPoststimSlider.*?to:) [\d\.\-]+', f'\\1 {to_val}', content, flags=re.DOTALL)
            
            # Update firstValue
            content = re.sub(r'(id: prestimPoststimSlider.*?firstValue:) [\d\.\-]+', f'\\1 {first_val}', content, flags=re.DOTALL)
            
            # Update secondValue
            content = re.sub(r'(id: prestimPoststimSlider.*?secondValue:) [\d\.\-]+', f'\\1 {second_val}', content, flags=re.DOTALL)
            
            # Write back to file
            with open(qml_file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            print(f"Updated prestim/poststim slider values: from={from_val}, to={to_val}, firstValue={first_val}, secondValue={second_val}")
            return True
            
        except Exception as e:
            print(f"Error updating prestim/poststim slider values: {str(e)}")
            return False

    @pyqtSlot(float, float, float, float)
    def updateDftfreqSliderValues(self, from_val, to_val, first_val, second_val):
        """Update the DFT frequency slider values in the QML file"""
        try:
            qml_file_path = self._preprocessing_qml_path
            
            # Read the current QML file
            with open(qml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Update from value
            content = re.sub(r'(id: dftfreqSlider.*?from:) [\d\.\-]+', f'\\1 {from_val}', content, flags=re.DOTALL)
            
            # Update to value
            content = re.sub(r'(id: dftfreqSlider.*?to:) [\d\.\-]+', f'\\1 {to_val}', content, flags=re.DOTALL)
            
            # Update firstValue
            content = re.sub(r'(id: dftfreqSlider.*?firstValue:) [\d\.\-]+', f'\\1 {first_val}', content, flags=re.DOTALL)
            
            # Update secondValue
            content = re.sub(r'(id: dftfreqSlider.*?secondValue:) [\d\.\-]+', f'\\1 {second_val}', content, flags=re.DOTALL)
            
            # Write back to file
            with open(qml_file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            print(f"Updated DFT frequency slider values: from={from_val}, to={to_val}, firstValue={first_val}, secondValue={second_val}")
            return True
            
        except Exception as e:
            print(f"Error updating DFT frequency slider values: {str(e)}")
            return False

    def _get_custom_range_slider_block_positions(self, content: str):
        pattern = re.compile(r'(\n\s*RangeSliderTemplate\s*\{\s*id\s*:\s*(customRangeSlider\d+)[\s\S]*?\n\s*\})')
        positions = {}
        for match in pattern.finditer(content):
            block_id = match.group(2)
            positions[block_id] = (match.start(1), match.end(1))
        return positions

    def _build_custom_range_slider_snippet(
        self,
        range_slider_id: str,
        label: str,
        matlab_property: str,
        from_val: float,
        to_val: float,
        first_value: float,
        second_value: float,
        step_size: float,
        unit: str,
    ) -> str:
        label = label.strip() or range_slider_id
        matlab_property = matlab_property.strip()
        if matlab_property and not matlab_property.startswith("cfg."):
            matlab_property = f"cfg.{matlab_property}"

        escaped_label = self._escape_qml_string(label)
        escaped_property = self._escape_qml_string(matlab_property)
        escaped_unit = self._escape_qml_string(unit)

        lines = [
            "",
            "            RangeSliderTemplate {",
            f"                id: {range_slider_id}",
            f"                property string persistentId: \"{range_slider_id}\"",
            f"                property string customLabel: \"{escaped_label}\"",
            "                property bool persistenceConnected: false",
            f"                label: \"{escaped_label}\"",
            f"                matlabProperty: \"{escaped_property}\"",
            f"                from: {from_val}",
            f"                to: {to_val}",
            f"                firstValue: {first_value}",
            f"                secondValue: {second_value}",
            f"                stepSize: {step_size}",
            f"                unit: \"{escaped_unit}\"",
            '                sliderState: "default"',
            '                sliderId: ""',
            '                matlabPropertyDraft: ""',
            '                anchors.left: parent.left',
            "            }\n",
        ]

        return "\n".join(lines)

    def _insert_custom_range_slider_snippet(self, content: str, snippet: str):
        start_marker = "id: customDropdownContainer"
        start_index = content.find(start_marker)
        if start_index == -1:
            print("Custom dropdown container not found for range slider insertion.")
            return content, False

        # Find the opening brace of the container
        open_brace_index = content.rfind('{', 0, start_index)
        if open_brace_index == -1:
            print("Container opening brace not found for range slider insertion.")
            return content, False

        # Find where to insert - look for the closing brace of the container
        depth = 0
        insert_index = -1
        for idx in range(open_brace_index, len(content)):
            char = content[idx]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    insert_index = idx
                    break

        if insert_index == -1:
            print("Container closing brace not found for range slider insertion.")
            return content, False

        # Insert the snippet before the closing brace
        new_content = content[:insert_index] + snippet + content[insert_index:]
        return new_content, True

    def _replace_custom_range_slider_block(self, content: str, range_slider_id: str, new_snippet: str):
        positions = self._get_custom_range_slider_block_positions(content)
        if range_slider_id not in positions:
            return content, False

        start, end = positions[range_slider_id]
        new_content = content[:start] + new_snippet + content[end:]
        return new_content, True

    def _next_custom_range_slider_index(self, existing_ids):
        max_index = -1
        for id_str in existing_ids:
            match = re.match(r'customRangeSlider(\d+)', id_str)
            if match:
                index = int(match.group(1))
                max_index = max(max_index, index)
        return max_index + 1 if max_index >= 0 else 1

    @pyqtSlot(str, str, float, float, float, float, float, str, result=str)
    def saveCustomRangeSlider(self, label, matlab_property, from_val, to_val, first_value, second_value, step_size, unit):
        """Persist a newly created custom range slider to preprocessing_page.qml and return its assigned id."""
        try:
            if not os.path.exists(self._preprocessing_qml_path):
                print("Preprocessing QML file not found when saving custom range slider.")
                return ""

            with open(self._preprocessing_qml_path, 'r', encoding='utf-8') as file:
                content = file.read()

            positions = self._get_custom_range_slider_block_positions(content)

            normalized_property = (matlab_property or "").strip()
            if normalized_property and not normalized_property.startswith("cfg."):
                normalized_property = f"cfg.{normalized_property}"
            escaped_property = f'"{self._escape_qml_string(normalized_property)}"'

            # If a range slider with the same matlab property exists, update it instead of creating duplicate
            for existing_id, (start, end) in positions.items():
                block_text = content[start:end]
                if f'matlabProperty: {escaped_property}' in block_text:
                    snippet = self._build_custom_range_slider_snippet(
                        existing_id,
                        label,
                        normalized_property,
                        from_val,
                        to_val,
                        first_value,
                        second_value,
                        step_size,
                        unit,
                    )
                    new_content, replaced = self._replace_custom_range_slider_block(content, existing_id, snippet)
                    if replaced:
                        with open(self._preprocessing_qml_path, 'w', encoding='utf-8') as file:
                            file.write(new_content)
                        print(f"Updated existing custom range slider '{existing_id}' with new settings.")
                    return existing_id

            next_index = self._next_custom_range_slider_index(positions.keys()) or 1
            range_slider_id = f"customRangeSlider{next_index}"

            snippet = self._build_custom_range_slider_snippet(
                range_slider_id,
                label,
                normalized_property,
                from_val,
                to_val,
                first_value,
                second_value,
                step_size,
                unit,
            )

            new_content, inserted = self._insert_custom_range_slider_snippet(content, snippet)
            if not inserted:
                return ""

            with open(self._preprocessing_qml_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            print(f"Saved new custom range slider '{range_slider_id}' to QML file.")
            return range_slider_id

        except Exception as e:
            print(f"Error saving custom range slider: {str(e)}")
            return ""

    @pyqtSlot(str, str, str, float, float, float, float, float, str, result=bool)
    def updateCustomRangeSlider(self, range_slider_id, label, matlab_property, from_val, to_val, first_value, second_value, step_size, unit):
        """Update an existing custom range slider definition in preprocessing_page.qml."""
        try:
            if not os.path.exists(self._preprocessing_qml_path):
                print("Preprocessing QML file not found when updating custom range slider.")
                return False

            with open(self._preprocessing_qml_path, 'r', encoding='utf-8') as file:
                content = file.read()

            snippet = self._build_custom_range_slider_snippet(
                range_slider_id,
                label,
                matlab_property,
                from_val,
                to_val,
                first_value,
                second_value,
                step_size,
                unit,
            )

            new_content, replaced = self._replace_custom_range_slider_block(content, range_slider_id, snippet)
            if not replaced:
                print(f"Custom range slider '{range_slider_id}' not found for update; attempting to append new block.")
                new_content, inserted = self._insert_custom_range_slider_snippet(content, snippet)
                if not inserted:
                    return False

            with open(self._preprocessing_qml_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            print(f"Updated custom range slider '{range_slider_id}' in QML file.")
            return True

        except Exception as e:
            print(f"Error updating custom range slider: {str(e)}")
            return False

    @pyqtSlot(str, result=bool)
    def removeCustomRangeSlider(self, range_slider_id):
        """Remove a custom range slider definition from preprocessing_page.qml."""
        try:
            if not os.path.exists(self._preprocessing_qml_path):
                print("Preprocessing QML file not found when removing custom range slider.")
                return False

            with open(self._preprocessing_qml_path, 'r', encoding='utf-8') as file:
                content = file.read()

            positions = self._get_custom_range_slider_block_positions(content)
            if range_slider_id not in positions:
                print(f"Custom range slider '{range_slider_id}' not found for removal.")
                return False

            start, end = positions[range_slider_id]
            new_content = content[:start] + content[end:]
            
            with open(self._preprocessing_qml_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            print(f"Removed custom range slider '{range_slider_id}' from QML file.")
            return True

        except Exception as e:
            print(f"Error removing custom range slider: {str(e)}")
            return False