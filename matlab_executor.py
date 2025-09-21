import os
import sys
import subprocess
import re
import threading
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
    ramContentsUpdated = pyqtSignal(list)  # Signal for RAM contents
    dataInfoReady = pyqtSignal(list)  # Signal for data viewer information
    matFileLoaded = pyqtSignal(list)  # Signal for loaded .mat file data
    matFileError = pyqtSignal(str)  # Signal for .mat file loading errors
    fileExplorerRefresh = pyqtSignal()  # Signal to refresh file explorer
    structExpanded = pyqtSignal(str, list)  # Signal for expanded struct data
    openStructTab = pyqtSignal(str, list)  # Signal to open struct in new tab
    openDataTab = pyqtSignal(str, list)  # Signal to open 2D data in spreadsheet tab
    updateSpreadsheetModel = pyqtSignal(object)  # Signal to update spreadsheet model with numpy data
    processingFinished = pyqtSignal()  # Signal when ICA processing is complete
    
    def __init__(self):
        super().__init__()
        self._output = "No MATLAB output yet..."
        # Load the current data directory from the MATLAB script at startup
        self._current_data_dir = self.getCurrentDataDirectory()
        self._worker_thread = None  # For background MATLAB execution
        self.current_file_data = {}  # Store current loaded .mat file data for expansion
    
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
            script_path = resource_path("preprocessing/preprocessing.m")
            
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
            script_path = resource_path("preprocessing/preprocessing.m")
            
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
            script_path = resource_path("preprocessing/preprocessing.m")
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
            script_path = resource_path("preprocessing/preprocessing.m")
            
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
            script_path = resource_path("preprocessing/preprocessing.m")
            
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
            script_path = resource_path("preprocessing/preprocessing.m")
            
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
            preprocessing_dir = resource_path("preprocessing")
            
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
    
    @pyqtSlot()
    def checkWorkspaceVariables(self):
        """Check what variables exist in MATLAB workspace"""
        try:
            print("Checking MATLAB workspace variables...")
            
            # Use the path to your MATLAB installation
            matlab_path = r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe"
            
            # Create MATLAB command to list workspace variables
            matlab_command = """
            vars = who;
            if ~isempty(vars)
                for i = 1:length(vars)
                    fprintf('%s\\n', vars{i});
                end
            else
                fprintf('No variables in workspace\\n');
            end
            """
            
            print("Running MATLAB command to check workspace...")
            
            # Execute MATLAB command
            result = subprocess.run([
                matlab_path, 
                "-batch", matlab_command
            ], capture_output=True, text=True, cwd=self._current_data_dir)
            
            print(f"MATLAB workspace check completed with return code: {result.returncode}")
            
            if result.returncode == 0:
                # Parse the output to get variable names
                variables = []
                if result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and line != "No variables in workspace":
                            variables.append(f"🧠 {line}")
                
                print(f"Found variables: {variables}")
                self.ramContentsUpdated.emit(variables)
            else:
                print(f"MATLAB workspace check failed: {result.stderr}")
                self.ramContentsUpdated.emit([])
                
        except Exception as e:
            print(f"Error checking workspace variables: {str(e)}")
            self.ramContentsUpdated.emit([])
    
    @pyqtSlot(str)
    def getDataInfo(self, data_name):
        """Get detailed information about a MATLAB variable"""
        try:
            print(f"Getting information for MATLAB variable: {data_name}")
            
            # Use the path to your MATLAB installation
            matlab_path = r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe"
            
            # Create MATLAB command to inspect the data
            matlab_command = f"""
            if exist('{data_name}', 'var')
                dataInfo = [];
                if iscell({data_name})
                    for i = 1:length({data_name})
                        item = {data_name}{{i}};
                        info = struct();
                        info.index = i;
                        info.type = class(item);
                        if isstruct(item) && isfield(item, 'label')
                            info.channels = length(item.label);
                        else
                            info.channels = 'N/A';
                        end
                        if isstruct(item) && isfield(item, 'trial')
                            info.trials = length(item.trial);
                            if ~isempty(item.trial)
                                info.timePoints = size(item.trial{{1}}, 2);
                            else
                                info.timePoints = 'N/A';
                            end
                        else
                            info.trials = 'N/A';
                            info.timePoints = 'N/A';
                        end
                        if isstruct(item) && isfield(item, 'fsample')
                            info.sampleRate = item.fsample;
                        else
                            info.sampleRate = 'N/A';
                        end
                        dataInfo = [dataInfo; info];
                    end
                else
                    info = struct();
                    info.index = 1;
                    info.type = class({data_name});
                    info.size = sprintf('%s', mat2str(size({data_name})));
                    info.channels = 'N/A';
                    info.trials = 'N/A';
                    info.timePoints = 'N/A';
                    info.sampleRate = 'N/A';
                    dataInfo = info;
                end
                
                % Display info
                for i = 1:length(dataInfo)
                    fprintf('DATAINFO|%d|%s|%s|%s|%s|%s|%s\\n', ...
                        dataInfo(i).index, dataInfo(i).type, ...
                        num2str(dataInfo(i).channels), num2str(dataInfo(i).trials), ...
                        num2str(dataInfo(i).timePoints), num2str(dataInfo(i).sampleRate), ...
                        sprintf('Item %d', i));
                end
            else
                fprintf('Variable {data_name} does not exist\\n');
            end
            """
            
            cmd = [
                matlab_path,
                '-batch',
                matlab_command
            ]
            
            print(f"Running MATLAB command for data inspection...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            print(f"MATLAB data inspection completed with return code: {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            
            if result.returncode == 0:
                # Parse the data info from MATLAB output
                data_info = []
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.startswith('DATAINFO|'):
                        parts = line.split('|')
                        if len(parts) >= 7:
                            info = {
                                'index': parts[1],
                                'type': parts[2],
                                'channels': parts[3],
                                'trials': parts[4],
                                'timePoints': parts[5],
                                'sampleRate': parts[6],
                                'size': f"{parts[3]} channels × {parts[4]} trials × {parts[5]} time points"
                            }
                            data_info.append(info)
                
                self.dataInfoReady.emit(data_info)
            else:
                error_msg = f"Failed to get data info: {result.stderr}"
                print(error_msg)
                self.dataInfoReady.emit([])
                
        except subprocess.TimeoutExpired:
            print("MATLAB data inspection timed out")
            self.dataInfoReady.emit([])
        except Exception as e:
            error_msg = f"Error getting data info: {str(e)}"
            print(error_msg)
            self.dataInfoReady.emit([])
    
    @pyqtSlot(str)
    def browseICAComponents(self, data_path):
        """Launch MATLAB ICA component browser using the browse_ICA.m script"""
        try:
            print("Starting MATLAB ICA component browser...")
            
            # Use the path to your MATLAB installation
            matlab_path = r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe"
            
            # Get the preprocessing directory (where browse_ICA.m should be)
            preprocessing_dir = resource_path("preprocessing")
            
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
    
    @pyqtSlot(str)
    def loadMatFile(self, filePath):
        """Load and inspect a .mat file using scipy (much faster than MATLAB)"""
        try:
            print(f"Loading .mat file: {filePath}")
            
            # Convert file path format if needed
            if filePath.startswith("file:///"):
                filePath = filePath[8:]
            filePath = filePath.replace('/', '\\')
            
            # Load .mat file using scipy
            mat_data = []
            data = scipy.io.loadmat(filePath, struct_as_record=False, squeeze_me=True)
            
            # Store the raw data for expansion purposes
            self.current_file_data = data
            
            # Process each variable in the .mat file
            for var_name, var_value in data.items():
                # Skip internal MATLAB variables
                if var_name.startswith('__'):
                    continue
                
                # Get variable type
                from scipy.io.matlab._mio5_params import mat_struct
                import numpy as np
                
                if isinstance(var_value, mat_struct):
                    var_type = "struct"
                elif isinstance(var_value, np.ndarray) and var_value.size > 0 and isinstance(var_value.flat[0], mat_struct):
                    var_type = "struct array"
                elif isinstance(var_value, list) and len(var_value) > 0 and isinstance(var_value[0], mat_struct):
                    var_type = "struct array"
                else:
                    var_type = type(var_value).__name__
                
                # Get variable size
                if isinstance(var_value, np.ndarray):
                    if len(var_value.shape) == 0:
                        size_str = "1x1"
                    elif len(var_value.shape) == 1:
                        size_str = f"{var_value.shape[0]}x1"
                    else:
                        size_str = 'x'.join(map(str, var_value.shape))
                elif hasattr(var_value, 'shape'):
                    if len(var_value.shape) == 0:
                        size_str = "1x1"
                    else:
                        size_str = 'x'.join(map(str, var_value.shape))
                elif isinstance(var_value, list):
                    size_str = f"{len(var_value)}x1"
                else:
                    size_str = "1x1"
                
                # Get a preview of the value
                value_str = self._getValuePreview(var_value)
                
                var_info = {
                    'variable': var_name,
                    'type': var_type,
                    'size': size_str,
                    'value': value_str
                }
                mat_data.append(var_info)
            
            print(f"Successfully loaded {len(mat_data)} variables from .mat file")
            if len(mat_data) > 0:
                print("First variable:", mat_data[0])  # Debug output
            
            self.matFileLoaded.emit(mat_data)
            
        except Exception as e:
            error_msg = f"Error loading .mat file: {str(e)}"
            print(error_msg)
            self.matFileError.emit(error_msg)
    
    def _getValuePreview(self, value):
        """Get a preview string for a variable value"""
        try:
            import numpy as np
            from scipy.io.matlab._mio5_params import mat_struct
            
            if isinstance(value, (int, float)):
                return str(value)
            elif isinstance(value, str):
                return f"'{value[:50]}'" if len(value) <= 50 else f"'{value[:47]}...'"
            elif isinstance(value, np.ndarray):
                # Check if it's an array of mat_struct objects
                if value.size > 0 and isinstance(value.flat[0], mat_struct):
                    return f"array of {value.size} structs"
                elif value.size <= 10 and value.ndim <= 1:
                    return str(value.tolist())
                else:
                    return f"array with {value.size} elements"
            elif isinstance(value, mat_struct):  # Handle scipy mat_struct objects
                field_names = value._fieldnames if hasattr(value, '_fieldnames') else []
                if len(field_names) <= 3:
                    return f"struct with fields: {', '.join(field_names)}"
                else:
                    return f"struct with {len(field_names)} fields"
            elif hasattr(value, '_fieldnames'):  # MATLAB struct
                field_names = getattr(value, '_fieldnames', [])
                if len(field_names) <= 3:
                    return f"struct with fields: {', '.join(field_names)}"
                else:
                    return f"struct with {len(field_names)} fields"
            elif isinstance(value, list):
                if len(value) <= 5:
                    # Check if list contains mat_struct objects
                    if len(value) > 0 and isinstance(value[0], mat_struct):
                        return f"array of {len(value)} structs"
                    else:
                        return str(value)
                else:
                    if len(value) > 0 and isinstance(value[0], mat_struct):
                        return f"array of {len(value)} structs"
                    else:
                        return f"list with {len(value)} elements"
            else:
                return f"<{type(value).__name__} object>"
        except Exception as e:
            return f"<preview error: {str(e)}>"
    
    @pyqtSlot(str, str)
    def expandNestedStruct(self, parentVariable, fieldPath):
        """Open a nested struct field in a new tab"""
        try:
            print(f"DEBUG: Opening nested struct in new tab: parent='{parentVariable}', field='{fieldPath}'")
            
            # Get the parent variable
            if parentVariable not in self.current_file_data:
                print(f"ERROR: Parent variable '{parentVariable}' not found in {list(self.current_file_data.keys())}")
                self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
                return
            
            var_value = self.current_file_data[parentVariable]
            print(f"DEBUG: Parent variable type: {type(var_value)}")
            
            from scipy.io.matlab._mio5_params import mat_struct
            import numpy as np
            
            # Handle array indexing for struct arrays
            if fieldPath.startswith('[') and fieldPath.endswith(']'):
                # This is a struct array element like [0] or [1]
                try:
                    index = int(fieldPath[1:-1])  # Extract index from [0]
                    print(f"DEBUG: Accessing array index {index}")
                    
                    if isinstance(var_value, np.ndarray) and hasattr(var_value, 'flat'):
                        if index < len(var_value.flat):
                            struct_item = var_value.flat[index]
                            print(f"DEBUG: Found struct item type: {type(struct_item)}")
                            
                            if isinstance(struct_item, mat_struct):
                                field_names = getattr(struct_item, '_fieldnames', [])
                                print(f"DEBUG: Struct fields: {field_names}")
                                expanded_data = self._getStructFields(struct_item, "", 0)  # Start at indent level 0 for new tab
                                print(f"DEBUG: Generated {len(expanded_data)} items for new tab")
                                
                                # Create a descriptive tab name
                                tab_name = f"{parentVariable}[{index+1}] contents"
                                self.openStructTab.emit(tab_name, expanded_data)
                                return
                            else:
                                print(f"ERROR: Array element is not a mat_struct: {type(struct_item)}")
                        else:
                            print(f"ERROR: Index {index} out of range for array of size {len(var_value.flat)}")
                    else:
                        print(f"ERROR: Parent is not a numpy array or has no flat attribute")
                        
                except (ValueError, IndexError) as e:
                    print(f"ERROR: Error accessing array index: {e}")
            else:
                # Regular field navigation
                print(f"DEBUG: Navigating to regular field: {fieldPath}")
                field_value = self._getNestedField(var_value, fieldPath)
                if field_value is not None:
                    expanded_data = self._getStructFields(field_value, "", 0)  # Start at indent level 0 for new tab
                    tab_name = f"{parentVariable}.{fieldPath} contents"
                    self.openStructTab.emit(tab_name, expanded_data)
                    return
                else:
                    print(f"ERROR: Could not find field: {fieldPath}")
            
            print(f"WARNING: Could not open nested field in tab: {fieldPath}")
            self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
            
        except Exception as e:
            error_msg = f"Error opening nested struct in tab: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
    
    @pyqtSlot(str, str)
    def openDataSpreadsheet(self, parentVariable, fieldPath):
        """Open numerical data in a spreadsheet-style tab"""
        try:
            print(f"DEBUG: Opening data spreadsheet: parent='{parentVariable}', field='{fieldPath}'")
            
            # Get the data
            data_value = None
            
            # Handle cases where parentVariable might be like "data[1]" from tab names
            if '[' in parentVariable and parentVariable.endswith(']'):
                # Extract the base variable and index
                base_var = parentVariable.split('[')[0]
                index_part = parentVariable.split('[')[1].rstrip(']')
                try:
                    index = int(index_part) - 1  # Convert to 0-based index
                    
                    if base_var in self.current_file_data:
                        base_value = self.current_file_data[base_var]
                        from scipy.io.matlab._mio5_params import mat_struct
                        import numpy as np
                        
                        if isinstance(base_value, np.ndarray) and hasattr(base_value, 'flat'):
                            if index < len(base_value.flat):
                                struct_item = base_value.flat[index]
                                if isinstance(struct_item, mat_struct) and hasattr(struct_item, fieldPath):
                                    data_value = getattr(struct_item, fieldPath)
                                    print(f"DEBUG: Found field '{fieldPath}' in struct array element")
                                else:
                                    print(f"ERROR: Field '{fieldPath}' not found in struct array element")
                            else:
                                print(f"ERROR: Index {index} out of range")
                        else:
                            print(f"ERROR: Base variable is not an array")
                    else:
                        print(f"ERROR: Base variable '{base_var}' not found")
                except ValueError:
                    print(f"ERROR: Could not parse index from '{index_part}'")
            elif parentVariable in self.current_file_data:
                if fieldPath:
                    # Navigate to nested field
                    parent_value = self.current_file_data[parentVariable]
                    data_value = self._getNestedFieldData(parent_value, fieldPath)
                else:
                    # Use parent variable directly
                    data_value = self.current_file_data[parentVariable]
            
            if data_value is None:
                print(f"ERROR: Could not find data for {parentVariable}.{fieldPath}")
                self.openDataTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
                return
            
            print(f"DEBUG: Converting to spreadsheet, data type: {type(data_value)}")
            
            # Convert to numpy array for the spreadsheet model
            import numpy as np
            try:
                if isinstance(data_value, np.ndarray):
                    np_data = data_value
                elif hasattr(data_value, '__iter__') and not isinstance(data_value, str):
                    np_data = np.array(list(data_value))
                else:
                    np_data = np.array([data_value])
                
                print(f"DEBUG: Array shape: {np_data.shape}, ndim: {np_data.ndim}")
                
                # Emit signal to update spreadsheet model
                self.updateSpreadsheetModel.emit(np_data)
                
                # Also emit the old format for tab creation
                spreadsheet_data = self._convertToSpreadsheet(data_value)
                tab_name = f"{parentVariable}.{fieldPath} data" if fieldPath else f"{parentVariable} data"
                
                print(f"DEBUG: Generated spreadsheet with {len(spreadsheet_data)} rows")
                self.openDataTab.emit(tab_name, spreadsheet_data)
                
            except Exception as e:
                print(f"ERROR: Could not convert data to numpy array: {e}")
                # Fallback to old format
                spreadsheet_data = self._convertToSpreadsheet(data_value)
                tab_name = f"{parentVariable}.{fieldPath} data" if fieldPath else f"{parentVariable} data"
                self.openDataTab.emit(tab_name, spreadsheet_data)
            
        except Exception as e:
            error_msg = f"Error opening data spreadsheet: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.openDataTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
    
    def _getNestedFieldData(self, struct_obj, fieldPath):
        """Get the actual data from a nested field (not just preview)"""
        from scipy.io.matlab._mio5_params import mat_struct
        import numpy as np
        
        # Handle array indexing
        if fieldPath.startswith('[') and fieldPath.endswith(']'):
            try:
                index = int(fieldPath[1:-1])
                if isinstance(struct_obj, np.ndarray) and hasattr(struct_obj, 'flat'):
                    if index < len(struct_obj.flat):
                        return struct_obj.flat[index]
            except (ValueError, IndexError):
                return None
        else:
            # Regular field navigation
            current = struct_obj
            for field_name in fieldPath.split('.'):
                field_name = field_name.strip()
                if isinstance(current, mat_struct) and hasattr(current, field_name):
                    current = getattr(current, field_name)
                else:
                    return None
            return current
        return None
    
    def _convertToSpreadsheet(self, data_value):
        """Convert any data to spreadsheet format"""
        import numpy as np
        from scipy.io.matlab._mio5_params import mat_struct
        
        try:
            print(f"DEBUG: Converting to spreadsheet, data type: {type(data_value)}")
            
            # Handle special MATLAB types first
            if isinstance(data_value, mat_struct):
                # This shouldn't happen since structs are handled separately, but just in case
                return [{
                    'row': 1,
                    'col': 1,
                    'value': "struct (use struct expansion instead)",
                    'isHeader': False
                }]
            
            # Handle strings/character arrays
            if isinstance(data_value, (str, bytes)):
                return [{
                    'row': 1,
                    'col': 1,
                    'value': str(data_value),
                    'isHeader': False
                }]
            
            # Try to convert to numpy array for consistent handling
            if not isinstance(data_value, np.ndarray):
                try:
                    if isinstance(data_value, (list, tuple)):
                        data_value = np.array(data_value)
                    elif hasattr(data_value, '__iter__') and not isinstance(data_value, (str, bytes)):
                        # Handle iterables like MATLAB cell arrays
                        data_list = list(data_value)
                        data_value = np.array(data_list)
                    else:
                        # Single scalar value
                        print(f"DEBUG: Single scalar value: {data_value}")
                        return [{
                            'row': 1,
                            'col': 1,
                            'value': str(data_value),
                            'isHeader': False
                        }]
                except Exception as conv_error:
                    print(f"DEBUG: Could not convert to array: {conv_error}, treating as scalar")
                    return [{
                        'row': 1,
                        'col': 1,
                        'value': str(data_value),
                        'isHeader': False
                    }]
            
            print(f"DEBUG: Array shape: {data_value.shape}, ndim: {data_value.ndim}")
            spreadsheet_data = []
            
            # Handle different dimensions
            if data_value.ndim == 0:
                # Scalar numpy array
                spreadsheet_data.append({
                    'row': 1,
                    'col': 1, 
                    'value': str(data_value.item()),
                    'isHeader': False
                })
            elif data_value.ndim == 1:
                # 1D array - display as column
                print(f"DEBUG: Creating 1D spreadsheet with {len(data_value)} items")
                for i, val in enumerate(data_value):
                    spreadsheet_data.append({
                        'row': i + 1,
                        'col': 1,
                        'value': str(val),
                        'isHeader': False
                    })
            elif data_value.ndim == 2:
                # 2D array - proper spreadsheet
                rows, cols = data_value.shape
                print(f"DEBUG: Creating 2D spreadsheet: {rows}x{cols}")
                for i in range(rows):
                    for j in range(cols):
                        spreadsheet_data.append({
                            'row': i + 1,
                            'col': j + 1,
                            'value': str(data_value[i, j]),
                            'isHeader': False
                        })
            else:
                # Higher dimensions - flatten to 2D
                print(f"DEBUG: Flattening {data_value.ndim}D array to 2D")
                reshaped = data_value.reshape(data_value.shape[0], -1)
                rows, cols = reshaped.shape
                for i in range(rows):
                    for j in range(cols):
                        spreadsheet_data.append({
                            'row': i + 1,
                            'col': j + 1,
                            'value': str(reshaped[i, j]),
                            'isHeader': False
                        })
            
            print(f"DEBUG: Generated {len(spreadsheet_data)} spreadsheet cells")
            return spreadsheet_data
            
        except Exception as e:
            print(f"Error converting to spreadsheet: {e}")
            import traceback
            traceback.print_exc()
            return [{
                'row': 1,
                'col': 1,
                'value': f"Error: {str(e)}",
                'isHeader': False
            }]
    
    @pyqtSlot(str, str)
    def expandNestedStruct(self, parentVariable, fieldPath):
        """Open a nested struct field in a new tab"""
        try:
            print(f"DEBUG: Opening nested struct in new tab: parent='{parentVariable}', field='{fieldPath}'")
            
            # Get the parent variable
            if parentVariable not in self.current_file_data:
                print(f"ERROR: Parent variable '{parentVariable}' not found in {list(self.current_file_data.keys())}")
                self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
                return
            
            var_value = self.current_file_data[parentVariable]
            print(f"DEBUG: Parent variable type: {type(var_value)}")
            
            from scipy.io.matlab._mio5_params import mat_struct
            import numpy as np
            
            # Handle array indexing for struct arrays
            if fieldPath.startswith('[') and fieldPath.endswith(']'):
                # This is a struct array element like [0] or [1]
                try:
                    index = int(fieldPath[1:-1])  # Extract index from [0]
                    print(f"DEBUG: Accessing array index {index}")
                    
                    if isinstance(var_value, np.ndarray) and hasattr(var_value, 'flat'):
                        if index < len(var_value.flat):
                            struct_item = var_value.flat[index]
                            print(f"DEBUG: Found struct item type: {type(struct_item)}")
                            
                            if isinstance(struct_item, mat_struct):
                                field_names = getattr(struct_item, '_fieldnames', [])
                                print(f"DEBUG: Struct fields: {field_names}")
                                expanded_data = self._getStructFields(struct_item, "", 0)  # Start at indent level 0 for new tab
                                print(f"DEBUG: Generated {len(expanded_data)} items for new tab")
                                
                                # Create a descriptive tab name
                                tab_name = f"{parentVariable}[{index+1}] contents"
                                self.openStructTab.emit(tab_name, expanded_data)
                                return
                            else:
                                print(f"ERROR: Array element is not a mat_struct: {type(struct_item)}")
                        else:
                            print(f"ERROR: Index {index} out of range for array of size {len(var_value.flat)}")
                    else:
                        print(f"ERROR: Parent is not a numpy array or has no flat attribute")
                        
                except (ValueError, IndexError) as e:
                    print(f"ERROR: Error accessing array index: {e}")
            else:
                # Regular field navigation
                print(f"DEBUG: Navigating to regular field: {fieldPath}")
                field_value = self._getNestedField(var_value, fieldPath)
                if field_value is not None:
                    expanded_data = self._getStructFields(field_value, "", 0)  # Start at indent level 0 for new tab
                    tab_name = f"{parentVariable}.{fieldPath} contents"
                    self.openStructTab.emit(tab_name, expanded_data)
                    return
                else:
                    print(f"ERROR: Could not find field: {fieldPath}")
            
            print(f"WARNING: Could not open nested field in tab: {fieldPath}")
            self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
            
        except Exception as e:
            error_msg = f"Error opening nested struct in tab: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
    
    @pyqtSlot(str, str)
    def openDataSpreadsheet(self, parentVariable, fieldPath):
        """Open numerical data in a spreadsheet-style tab"""
        try:
            print(f"DEBUG: Opening data spreadsheet: parent='{parentVariable}', field='{fieldPath}'")
            
            # Get the data
            data_value = None
            
            # Handle cases where parentVariable might be like "data[1]" from tab names
            if '[' in parentVariable and parentVariable.endswith(']'):
                # Extract the base variable and index
                base_var = parentVariable.split('[')[0]
                index_part = parentVariable.split('[')[1].rstrip(']')
                try:
                    index = int(index_part) - 1  # Convert to 0-based index
                    
                    if base_var in self.current_file_data:
                        base_value = self.current_file_data[base_var]
                        from scipy.io.matlab._mio5_params import mat_struct
                        import numpy as np
                        
                        if isinstance(base_value, np.ndarray) and hasattr(base_value, 'flat'):
                            if index < len(base_value.flat):
                                struct_item = base_value.flat[index]
                                if isinstance(struct_item, mat_struct) and hasattr(struct_item, fieldPath):
                                    data_value = getattr(struct_item, fieldPath)
                                    print(f"DEBUG: Found field '{fieldPath}' in struct array element")
                                else:
                                    print(f"ERROR: Field '{fieldPath}' not found in struct array element")
                            else:
                                print(f"ERROR: Index {index} out of range")
                        else:
                            print(f"ERROR: Base variable is not an array")
                    else:
                        print(f"ERROR: Base variable '{base_var}' not found")
                except ValueError:
                    print(f"ERROR: Could not parse index from '{index_part}'")
            elif parentVariable in self.current_file_data:
                if fieldPath:
                    # Navigate to nested field
                    parent_value = self.current_file_data[parentVariable]
                    data_value = self._getNestedFieldData(parent_value, fieldPath)
                else:
                    # Use parent variable directly
                    data_value = self.current_file_data[parentVariable]
            
            if data_value is None:
                print(f"ERROR: Could not find data for {parentVariable}.{fieldPath}")
                self.openDataTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
                return
            
            print(f"DEBUG: Converting to spreadsheet, data type: {type(data_value)}")
            
            # Convert to numpy array for the spreadsheet model
            import numpy as np
            try:
                if isinstance(data_value, np.ndarray):
                    np_data = data_value
                elif hasattr(data_value, '__iter__') and not isinstance(data_value, str):
                    np_data = np.array(list(data_value))
                else:
                    np_data = np.array([data_value])
                
                print(f"DEBUG: Array shape: {np_data.shape}, ndim: {np_data.ndim}")
                
                # Emit signal to update spreadsheet model
                self.updateSpreadsheetModel.emit(np_data)
                
                # Also emit the old format for tab creation
                spreadsheet_data = self._convertToSpreadsheet(data_value)
                tab_name = f"{parentVariable}.{fieldPath} data" if fieldPath else f"{parentVariable} data"
                
                print(f"DEBUG: Generated spreadsheet with {len(spreadsheet_data)} rows")
                self.openDataTab.emit(tab_name, spreadsheet_data)
                
            except Exception as e:
                print(f"ERROR: Could not convert data to numpy array: {e}")
                # Fallback to old format
                spreadsheet_data = self._convertToSpreadsheet(data_value)
                tab_name = f"{parentVariable}.{fieldPath} data" if fieldPath else f"{parentVariable} data"
                self.openDataTab.emit(tab_name, spreadsheet_data)
            
        except Exception as e:
            error_msg = f"Error opening data spreadsheet: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.openDataTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
    
    def _getNestedFieldData(self, struct_obj, fieldPath):
        """Get the actual data from a nested field (not just preview)"""
        from scipy.io.matlab._mio5_params import mat_struct
        import numpy as np
        
        # Handle array indexing
        if fieldPath.startswith('[') and fieldPath.endswith(']'):
            try:
                index = int(fieldPath[1:-1])
                if isinstance(struct_obj, np.ndarray) and hasattr(struct_obj, 'flat'):
                    if index < len(struct_obj.flat):
                        return struct_obj.flat[index]
            except (ValueError, IndexError):
                return None
        else:
            # Regular field navigation
            current = struct_obj
            for field_name in fieldPath.split('.'):
                field_name = field_name.strip()
                if isinstance(current, mat_struct) and hasattr(current, field_name):
                    current = getattr(current, field_name)
                else:
                    return None
            return current
        return None
    
    def _convertToSpreadsheet(self, data_value):
        """Convert any data to spreadsheet format"""
        import numpy as np
        from scipy.io.matlab._mio5_params import mat_struct
        
        try:
            print(f"DEBUG: Converting to spreadsheet, data type: {type(data_value)}")
            
            # Handle special MATLAB types first
            if isinstance(data_value, mat_struct):
                # This shouldn't happen since structs are handled separately, but just in case
                return [{
                    'row': 1,
                    'col': 1,
                    'value': "struct (use struct expansion instead)",
                    'isHeader': False
                }]
            
            # Handle strings/character arrays
            if isinstance(data_value, (str, bytes)):
                return [{
                    'row': 1,
                    'col': 1,
                    'value': str(data_value),
                    'isHeader': False
                }]
            
            # Try to convert to numpy array for consistent handling
            if not isinstance(data_value, np.ndarray):
                try:
                    if isinstance(data_value, (list, tuple)):
                        data_value = np.array(data_value)
                    elif hasattr(data_value, '__iter__') and not isinstance(data_value, (str, bytes)):
                        # Handle iterables like MATLAB cell arrays
                        data_list = list(data_value)
                        data_value = np.array(data_list)
                    else:
                        # Single scalar value
                        print(f"DEBUG: Single scalar value: {data_value}")
                        return [{
                            'row': 1,
                            'col': 1,
                            'value': str(data_value),
                            'isHeader': False
                        }]
                except Exception as conv_error:
                    print(f"DEBUG: Could not convert to array: {conv_error}, treating as scalar")
                    return [{
                        'row': 1,
                        'col': 1,
                        'value': str(data_value),
                        'isHeader': False
                    }]
            
            print(f"DEBUG: Array shape: {data_value.shape}, ndim: {data_value.ndim}")
            spreadsheet_data = []
            
            # Handle different dimensions
            if data_value.ndim == 0:
                # Scalar numpy array
                spreadsheet_data.append({
                    'row': 1,
                    'col': 1, 
                    'value': str(data_value.item()),
                    'isHeader': False
                })
            elif data_value.ndim == 1:
                # 1D array - display as column
                print(f"DEBUG: Creating 1D spreadsheet with {len(data_value)} items")
                for i, val in enumerate(data_value):
                    spreadsheet_data.append({
                        'row': i + 1,
                        'col': 1,
                        'value': str(val),
                        'isHeader': False
                    })
            elif data_value.ndim == 2:
                # 2D array - proper spreadsheet
                rows, cols = data_value.shape
                print(f"DEBUG: Creating 2D spreadsheet: {rows}x{cols}")
                for i in range(rows):
                    for j in range(cols):
                        spreadsheet_data.append({
                            'row': i + 1,
                            'col': j + 1,
                            'value': str(data_value[i, j]),
                            'isHeader': False
                        })
            else:
                # Higher dimensions - flatten to 2D
                print(f"DEBUG: Flattening {data_value.ndim}D array to 2D")
                reshaped = data_value.reshape(data_value.shape[0], -1)
                rows, cols = reshaped.shape
                for i in range(rows):
                    for j in range(cols):
                        spreadsheet_data.append({
                            'row': i + 1,
                            'col': j + 1,
                            'value': str(reshaped[i, j]),
                            'isHeader': False
                        })
            
            print(f"DEBUG: Generated {len(spreadsheet_data)} spreadsheet cells")
            return spreadsheet_data
            
        except Exception as e:
            print(f"Error converting to spreadsheet: {e}")
            import traceback
            traceback.print_exc()
            return [{
                'row': 1,
                'col': 1,
                'value': f"Error: {str(e)}",
                'isHeader': False
            }]
    
    @pyqtSlot(str, str)
    def expandNestedStruct(self, parentVariable, fieldPath):
        """Open a nested struct field in a new tab"""
        try:
            print(f"DEBUG: Opening nested struct in new tab: parent='{parentVariable}', field='{fieldPath}'")
            
            # Get the parent variable
            if parentVariable not in self.current_file_data:
                print(f"ERROR: Parent variable '{parentVariable}' not found in {list(self.current_file_data.keys())}")
                self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
                return
            
            var_value = self.current_file_data[parentVariable]
            print(f"DEBUG: Parent variable type: {type(var_value)}")
            
            from scipy.io.matlab._mio5_params import mat_struct
            import numpy as np
            
            # Handle array indexing for struct arrays
            if fieldPath.startswith('[') and fieldPath.endswith(']'):
                # This is a struct array element like [0] or [1]
                try:
                    index = int(fieldPath[1:-1])  # Extract index from [0]
                    print(f"DEBUG: Accessing array index {index}")
                    
                    if isinstance(var_value, np.ndarray) and hasattr(var_value, 'flat'):
                        if index < len(var_value.flat):
                            struct_item = var_value.flat[index]
                            print(f"DEBUG: Found struct item type: {type(struct_item)}")
                            
                            if isinstance(struct_item, mat_struct):
                                field_names = getattr(struct_item, '_fieldnames', [])
                                print(f"DEBUG: Struct fields: {field_names}")
                                expanded_data = self._getStructFields(struct_item, "", 0)  # Start at indent level 0 for new tab
                                print(f"DEBUG: Generated {len(expanded_data)} items for new tab")
                                
                                # Create a descriptive tab name
                                tab_name = f"{parentVariable}[{index+1}] contents"
                                self.openStructTab.emit(tab_name, expanded_data)
                                return
                            else:
                                print(f"ERROR: Array element is not a mat_struct: {type(struct_item)}")
                        else:
                            print(f"ERROR: Index {index} out of range for array of size {len(var_value.flat)}")
                    else:
                        print(f"ERROR: Parent is not a numpy array or has no flat attribute")
                        
                except (ValueError, IndexError) as e:
                    print(f"ERROR: Error accessing array index: {e}")
            else:
                # Regular field navigation
                print(f"DEBUG: Navigating to regular field: {fieldPath}")
                field_value = self._getNestedField(var_value, fieldPath)
                if field_value is not None:
                    expanded_data = self._getStructFields(field_value, "", 0)  # Start at indent level 0 for new tab
                    tab_name = f"{parentVariable}.{fieldPath} contents"
                    self.openStructTab.emit(tab_name, expanded_data)
                    return
                else:
                    print(f"ERROR: Could not find field: {fieldPath}")
            
            print(f"WARNING: Could not open nested field in tab: {fieldPath}")
            self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
            
        except Exception as e:
            error_msg = f"Error opening nested struct in tab: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
    
    @pyqtSlot(str, str)
    def openDataSpreadsheet(self, parentVariable, fieldPath):
        """Open numerical data in a spreadsheet-style tab"""
        try:
            print(f"DEBUG: Opening data spreadsheet: parent='{parentVariable}', field='{fieldPath}'")
            
            # Get the data
            data_value = None
            
            # Handle cases where parentVariable might be like "data[1]" from tab names
            if '[' in parentVariable and parentVariable.endswith(']'):
                # Extract the base variable and index
                base_var = parentVariable.split('[')[0]
                index_part = parentVariable.split('[')[1].rstrip(']')
                try:
                    index = int(index_part) - 1  # Convert to 0-based index
                    
                    if base_var in self.current_file_data:
                        base_value = self.current_file_data[base_var]
                        from scipy.io.matlab._mio5_params import mat_struct
                        import numpy as np
                        
                        if isinstance(base_value, np.ndarray) and hasattr(base_value, 'flat'):
                            if index < len(base_value.flat):
                                struct_item = base_value.flat[index]
                                if isinstance(struct_item, mat_struct) and hasattr(struct_item, fieldPath):
                                    data_value = getattr(struct_item, fieldPath)
                                    print(f"DEBUG: Found field '{fieldPath}' in struct array element")
                                else:
                                    print(f"ERROR: Field '{fieldPath}' not found in struct array element")
                            else:
                                print(f"ERROR: Index {index} out of range")
                        else:
                            print(f"ERROR: Base variable is not an array")
                    else:
                        print(f"ERROR: Base variable '{base_var}' not found")
                except ValueError:
                    print(f"ERROR: Could not parse index from '{index_part}'")
            elif parentVariable in self.current_file_data:
                if fieldPath:
                    # Navigate to nested field
                    parent_value = self.current_file_data[parentVariable]
                    data_value = self._getNestedFieldData(parent_value, fieldPath)
                else:
                    # Use parent variable directly
                    data_value = self.current_file_data[parentVariable]
            
            if data_value is None:
                print(f"ERROR: Could not find data for {parentVariable}.{fieldPath}")
                self.openDataTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
                return
            
            print(f"DEBUG: Converting to spreadsheet, data type: {type(data_value)}")
            
            # Convert to numpy array for the spreadsheet model
            import numpy as np
            try:
                if isinstance(data_value, np.ndarray):
                    np_data = data_value
                elif hasattr(data_value, '__iter__') and not isinstance(data_value, str):
                    np_data = np.array(list(data_value))
                else:
                    np_data = np.array([data_value])
                
                print(f"DEBUG: Array shape: {np_data.shape}, ndim: {np_data.ndim}")
                
                # Emit signal to update spreadsheet model
                self.updateSpreadsheetModel.emit(np_data)
                
                # Also emit the old format for tab creation
                spreadsheet_data = self._convertToSpreadsheet(data_value)
                tab_name = f"{parentVariable}.{fieldPath} data" if fieldPath else f"{parentVariable} data"
                
                print(f"DEBUG: Generated spreadsheet with {len(spreadsheet_data)} rows")
                self.openDataTab.emit(tab_name, spreadsheet_data)
                
            except Exception as e:
                print(f"ERROR: Could not convert data to numpy array: {e}")
                # Fallback to old format
                spreadsheet_data = self._convertToSpreadsheet(data_value)
                tab_name = f"{parentVariable}.{fieldPath} data" if fieldPath else f"{parentVariable} data"
                self.openDataTab.emit(tab_name, spreadsheet_data)
            
        except Exception as e:
            error_msg = f"Error opening data spreadsheet: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.openDataTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
    
    def _getNestedFieldData(self, struct_obj, fieldPath):
        """Get the actual data from a nested field (not just preview)"""
        from scipy.io.matlab._mio5_params import mat_struct
        import numpy as np
        
        # Handle array indexing
        if fieldPath.startswith('[') and fieldPath.endswith(']'):
            try:
                index = int(fieldPath[1:-1])
                if isinstance(struct_obj, np.ndarray) and hasattr(struct_obj, 'flat'):
                    if index < len(struct_obj.flat):
                        return struct_obj.flat[index]
            except (ValueError, IndexError):
                return None
        else:
            # Regular field navigation
            current = struct_obj
            for field_name in fieldPath.split('.'):
                field_name = field_name.strip()
                if isinstance(current, mat_struct) and hasattr(current, field_name):
                    current = getattr(current, field_name)
                else:
                    return None
            return current
        return None
    
    def _convertToSpreadsheet(self, data_value):
        """Convert any data to spreadsheet format"""
        import numpy as np
        from scipy.io.matlab._mio5_params import mat_struct
        
        try:
            print(f"DEBUG: Converting to spreadsheet, data type: {type(data_value)}")
            
            # Handle special MATLAB types first
            if isinstance(data_value, mat_struct):
                # This shouldn't happen since structs are handled separately, but just in case
                return [{
                    'row': 1,
                    'col': 1,
                    'value': "struct (use struct expansion instead)",
                    'isHeader': False
                }]
            
            # Handle strings/character arrays
            if isinstance(data_value, (str, bytes)):
                return [{
                    'row': 1,
                    'col': 1,
                    'value': str(data_value),
                    'isHeader': False
                }]
            
            # Try to convert to numpy array for consistent handling
            if not isinstance(data_value, np.ndarray):
                try:
                    if isinstance(data_value, (list, tuple)):
                        data_value = np.array(data_value)
                    elif hasattr(data_value, '__iter__') and not isinstance(data_value, (str, bytes)):
                        # Handle iterables like MATLAB cell arrays
                        data_list = list(data_value)
                        data_value = np.array(data_list)
                    else:
                        # Single scalar value
                        print(f"DEBUG: Single scalar value: {data_value}")
                        return [{
                            'row': 1,
                            'col': 1,
                            'value': str(data_value),
                            'isHeader': False
                        }]
                except Exception as conv_error:
                    print(f"DEBUG: Could not convert to array: {conv_error}, treating as scalar")
                    return [{
                        'row': 1,
                        'col': 1,
                        'value': str(data_value),
                        'isHeader': False
                    }]
            
            print(f"DEBUG: Array shape: {data_value.shape}, ndim: {data_value.ndim}")
            spreadsheet_data = []
            
            # Handle different dimensions
            if data_value.ndim == 0:
                # Scalar numpy array
                spreadsheet_data.append({
                    'row': 1,
                    'col': 1, 
                    'value': str(data_value.item()),
                    'isHeader': False
                })
            elif data_value.ndim == 1:
                # 1D array - display as column
                print(f"DEBUG: Creating 1D spreadsheet with {len(data_value)} items")
                for i, val in enumerate(data_value):
                    spreadsheet_data.append({
                        'row': i + 1,
                        'col': 1,
                        'value': str(val),
                        'isHeader': False
                    })
            elif data_value.ndim == 2:
                # 2D array - proper spreadsheet
                rows, cols = data_value.shape
                print(f"DEBUG: Creating 2D spreadsheet: {rows}x{cols}")
                for i in range(rows):
                    for j in range(cols):
                        spreadsheet_data.append({
                            'row': i + 1,
                            'col': j + 1,
                            'value': str(data_value[i, j]),
                            'isHeader': False
                        })
            else:
                # Higher dimensions - flatten to 2D
                print(f"DEBUG: Flattening {data_value.ndim}D array to 2D")
                reshaped = data_value.reshape(data_value.shape[0], -1)
                rows, cols = reshaped.shape
                for i in range(rows):
                    for j in range(cols):
                        spreadsheet_data.append({
                            'row': i + 1,
                            'col': j + 1,
                            'value': str(reshaped[i, j]),
                            'isHeader': False
                        })
            
            print(f"DEBUG: Generated {len(spreadsheet_data)} spreadsheet cells")
            return spreadsheet_data
            
        except Exception as e:
            print(f"Error converting to spreadsheet: {e}")
            import traceback
            traceback.print_exc()
            return [{
                'row': 1,
                'col': 1,
                'value': f"Error: {str(e)}",
                'isHeader': False
            }]
    
    @pyqtSlot(str, str)
    def expandNestedStruct(self, parentVariable, fieldPath):
        """Open a nested struct field in a new tab"""
        try:
            print(f"DEBUG: Opening nested struct in new tab: parent='{parentVariable}', field='{fieldPath}'")
            
            # Get the parent variable
            if parentVariable not in self.current_file_data:
                print(f"ERROR: Parent variable '{parentVariable}' not found in {list(self.current_file_data.keys())}")
                self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
                return
            
            var_value = self.current_file_data[parentVariable]
            print(f"DEBUG: Parent variable type: {type(var_value)}")
            
            from scipy.io.matlab._mio5_params import mat_struct
            import numpy as np
            
            # Handle array indexing for struct arrays
            if fieldPath.startswith('[') and fieldPath.endswith(']'):
                # This is a struct array element like [0] or [1]
                try:
                    index = int(fieldPath[1:-1])  # Extract index from [0]
                    print(f"DEBUG: Accessing array index {index}")
                    
                    if isinstance(var_value, np.ndarray) and hasattr(var_value, 'flat'):
                        if index < len(var_value.flat):
                            struct_item = var_value.flat[index]
                            print(f"DEBUG: Found struct item type: {type(struct_item)}")
                            
                            if isinstance(struct_item, mat_struct):
                                field_names = getattr(struct_item, '_fieldnames', [])
                                print(f"DEBUG: Struct fields: {field_names}")
                                expanded_data = self._getStructFields(struct_item, "", 0)  # Start at indent level 0 for new tab
                                print(f"DEBUG: Generated {len(expanded_data)} items for new tab")
                                
                                # Create a descriptive tab name
                                tab_name = f"{parentVariable}[{index+1}] contents"
                                self.openStructTab.emit(tab_name, expanded_data)
                                return
                            else:
                                print(f"ERROR: Array element is not a mat_struct: {type(struct_item)}")
                        else:
                            print(f"ERROR: Index {index} out of range for array of size {len(var_value.flat)}")
                    else:
                        print(f"ERROR: Parent is not a numpy array or has no flat attribute")
                        
                except (ValueError, IndexError) as e:
                    print(f"ERROR: Error accessing array index: {e}")
            else:
                # Regular field navigation
                print(f"DEBUG: Navigating to regular field: {fieldPath}")
                field_value = self._getNestedField(var_value, fieldPath)
                if field_value is not None:
                    expanded_data = self._getStructFields(field_value, "", 0)  # Start at indent level 0 for new tab
                    tab_name = f"{parentVariable}.{fieldPath} contents"
                    self.openStructTab.emit(tab_name, expanded_data)
                    return
                else:
                    print(f"ERROR: Could not find field: {fieldPath}")
            
            print(f"WARNING: Could not open nested field in tab: {fieldPath}")
            self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
            
        except Exception as e:
            error_msg = f"Error opening nested struct in tab: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.openStructTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
    
    @pyqtSlot(str, str)
    def openDataSpreadsheet(self, parentVariable, fieldPath):
        """Open numerical data in a spreadsheet-style tab"""
        try:
            print(f"DEBUG: Opening data spreadsheet: parent='{parentVariable}', field='{fieldPath}'")
            
            # Get the data
            data_value = None
            
            # Handle cases where parentVariable might be like "data[1]" from tab names
            if '[' in parentVariable and parentVariable.endswith(']'):
                # Extract the base variable and index
                base_var = parentVariable.split('[')[0]
                index_part = parentVariable.split('[')[1].rstrip(']')
                try:
                    index = int(index_part) - 1  # Convert to 0-based index
                    
                    if base_var in self.current_file_data:
                        base_value = self.current_file_data[base_var]
                        from scipy.io.matlab._mio5_params import mat_struct
                        import numpy as np
                        
                        if isinstance(base_value, np.ndarray) and hasattr(base_value, 'flat'):
                            if index < len(base_value.flat):
                                struct_item = base_value.flat[index]
                                if isinstance(struct_item, mat_struct) and hasattr(struct_item, fieldPath):
                                    data_value = getattr(struct_item, fieldPath)
                                    print(f"DEBUG: Found field '{fieldPath}' in struct array element")
                                else:
                                    print(f"ERROR: Field '{fieldPath}' not found in struct array element")
                            else:
                                print(f"ERROR: Index {index} out of range")
                        else:
                            print(f"ERROR: Base variable is not an array")
                    else:
                        print(f"ERROR: Base variable '{base_var}' not found")
                except ValueError:
                    print(f"ERROR: Could not parse index from '{index_part}'")
            elif parentVariable in self.current_file_data:
                if fieldPath:
                    # Navigate to nested field
                    parent_value = self.current_file_data[parentVariable]
                    data_value = self._getNestedFieldData(parent_value, fieldPath)
                else:
                    # Use parent variable directly
                    data_value = self.current_file_data[parentVariable]
            
            if data_value is None:
                print(f"ERROR: Could not find data for {parentVariable}.{fieldPath}")
                self.openDataTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
                return
            
            print(f"DEBUG: Converting to spreadsheet, data type: {type(data_value)}")
            
            # Convert to numpy array for the spreadsheet model
            import numpy as np
            try:
                if isinstance(data_value, np.ndarray):
                    np_data = data_value
                elif hasattr(data_value, '__iter__') and not isinstance(data_value, str):
                    np_data = np.array(list(data_value))
                else:
                    np_data = np.array([data_value])
                
                print(f"DEBUG: Array shape: {np_data.shape}, ndim: {np_data.ndim}")
                
                # Emit signal to update spreadsheet model
                self.updateSpreadsheetModel.emit(np_data)
                
                # Also emit the old format for tab creation
                spreadsheet_data = self._convertToSpreadsheet(data_value)
                tab_name = f"{parentVariable}.{fieldPath} data" if fieldPath else f"{parentVariable} data"
                
                print(f"DEBUG: Generated spreadsheet with {len(spreadsheet_data)} rows")
                self.openDataTab.emit(tab_name, spreadsheet_data)
                
            except Exception as e:
                print(f"ERROR: Could not convert data to numpy array: {e}")
                # Fallback to old format
                spreadsheet_data = self._convertToSpreadsheet(data_value)
                tab_name = f"{parentVariable}.{fieldPath} data" if fieldPath else f"{parentVariable} data"
                self.openDataTab.emit(tab_name, spreadsheet_data)
            
        except Exception as e:
            error_msg = f"Error opening data spreadsheet: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.openDataTab.emit(f"ERROR: {parentVariable}.{fieldPath}", [])
    
    def _getNestedFieldData(self, struct_obj, fieldPath):
        """Get the actual data from a nested field (not just preview)"""
        from scipy.io.matlab._mio5_params import mat_struct
        import numpy as np
        
        # Handle array indexing
        if fieldPath.startswith('[') and fieldPath.endswith(']'):
            try:
                index = int(fieldPath[1:-1])
                if isinstance(struct_obj, np.ndarray) and hasattr(struct_obj, 'flat'):
                    if index < len(struct_obj.flat):
                        return struct_obj.flat[index]
            except (ValueError, IndexError):
                return None
        else:
            # Regular field navigation
            current = struct_obj
            for field_name in fieldPath.split('.'):
                field_name = field_name.strip()
                if isinstance(current, mat_struct) and hasattr(current, field_name):
                    current = getattr(current, field_name)
                else:
                    return None
            return current
        return None
    
    def _convertToSpreadsheet(self, data_value):
        """Convert any data to spreadsheet format"""
        import numpy as np
        from scipy.io.matlab._mio5_params import mat_struct
        
        try:
            print(f"DEBUG: Converting to spreadsheet, data type: {type(data_value)}")
            
            # Handle special MATLAB types first
            if isinstance(data_value, mat_struct):
                # This shouldn't happen since structs are handled separately, but just in case
                return [{
                    'row': 1,
                    'col': 1,
                    'value': "struct (use struct expansion instead)",
                    'isHeader': False
                }]
            
            # Handle strings/character arrays
            if isinstance(data_value, (str, bytes)):
                return [{
                    'row': 1,
                    'col': 1,
                    'value': str(data_value),
                    'isHeader': False
                }]
            
            # Try to convert to numpy array for consistent handling
            if not isinstance(data_value, np.ndarray):
                try:
                    if isinstance(data_value, (list, tuple)):
                        data_value = np.array(data_value)
                    elif hasattr(data_value, '__iter__') and not isinstance(data_value, (str, bytes)):
                        # Handle iterables like MATLAB cell arrays
                        data_list = list(data_value)
                        data_value = np.array(data_list)
                    else:
                        # Single scalar value
                        print(f"DEBUG: Single scalar value: {data_value}")
                        return [{
                            'row': 1,
                            'col': 1,
                            'value': str(data_value),
                            'isHeader': False
                        }]
                except Exception as conv_error:
                    print(f"DEBUG: Could not convert to array: {conv_error}, treating as scalar")
                    return [{
                        'row': 1,
                        'col': 1,
                        'value': str(data_value),
                        'isHeader': False
                    }]
            
            print(f"DEBUG: Array shape: {data_value.shape}, ndim: {data_value.ndim}")
            spreadsheet_data = []
            
            # Handle different dimensions
            if data_value.ndim == 0:
                # Scalar numpy array
                spreadsheet_data.append({
                    'row': 1,
                    'col': 1, 
                    'value': str(data_value.item()),
                    'isHeader': False
                })
            elif data_value.ndim == 1:
                # 1D array - display as column
                print(f"DEBUG: Creating 1D spreadsheet with {len(data_value)} items")
                for i, val in enumerate(data_value):
                    spreadsheet_data.append({
                        'row': i + 1,
                        'col': 1,
                        'value': str(val),
                        'isHeader': False
                    })
            elif data_value.ndim == 2:
                # 2D array - proper spreadsheet
                rows, cols = data_value.shape
                print(f"DEBUG: Creating 2D spreadsheet: {rows}x{cols}")
                for i in range(rows):
                    for j in range(cols):
                        spreadsheet_data.append({
                            'row': i + 1,
                            'col': j + 1,
                            'value': str(data_value[i, j]),
                            'isHeader': False
                        })
            else:
                # Higher dimensions - flatten to 2D
                print(f"DEBUG: Flattening {data_value.ndim}D array to 2D")
                reshaped = data_value.reshape(data_value.shape[0], -1)
                rows, cols = reshaped.shape
                for i in range(rows):
                    for j in range(cols):
                        spreadsheet_data.append({
                            'row': i + 1,
                            'col': j + 1,
                            'value': str(reshaped[i, j]),
                            'isHeader': False
                        })
            
            print(f"DEBUG: Generated {len(spreadsheet_data)} spreadsheet cells")
            return spreadsheet_data
            
        except Exception as e:
            print(f"Error converting to spreadsheet: {e}")
            import traceback
            traceback.print_exc()
            return [{
                'row': 1,
                'col': 1,
                'value': f"Error: {str(e)}",
                'isHeader': False
            }]
    
    @pyqtSlot(str)
    def expandStruct(self, variableName):
        """Open a struct variable in a new tab"""
        try:
            # Always open in new tab instead of toggle
            if variableName not in self.current_file_data:
                self.openStructTab.emit(f"ERROR: {variableName}", [])
                return
            
            var_value = self.current_file_data[variableName]
            expanded_data = self._getStructFields(var_value, "", 0)  # Start at indent level 0 for new tab
            
            # Create a user-friendly tab name
            tab_name = f"{variableName} contents"
            self.openStructTab.emit(tab_name, expanded_data)
            
        except Exception as e:
            error_msg = f"Error opening struct: {str(e)}"
            print(error_msg)
            self.openStructTab.emit(f"ERROR: {variableName}", [])
    
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
            script_path = resource_path("preprocessing/preprocessing.m")
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
        try:
            qml_file_path = "UI/preprocessing_page.qml"
            
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
                except:
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
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error adding custom trialfun option to QML: {str(e)}")
            return False
    
    @pyqtSlot(str, int)
    def saveTrialfunSelection(self, selected_option, selected_index):
        """Save the selected trialfun option and index to the QML file"""
        try:
            qml_file_path = "UI/preprocessing_page.qml"
            
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
            return True
            
        except Exception as e:
            print(f"Error saving trialfun selection to QML: {str(e)}")
            return False
    
    @pyqtSlot(str)
    def addCustomEventtypeOption(self, new_option):
        """Add a new custom eventtype option to the QML file directly"""
        try:
            qml_file_path = "UI/preprocessing_page.qml"
            
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
            qml_file_path = "UI/preprocessing_page.qml"
            
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
            preprocessing_dir = resource_path("preprocessing")
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
                    # Launch MATLAB in desktop mode and execute commands directly
                    matlab_commands = f"""
                    try
                        % Add FieldTrip path
                        addpath('{self.getCurrentFieldtripPath().replace(chr(92), '/')}');
                        ft_defaults;
                        
                        % Load the file
                        fprintf('Loading file: {mat_file_path.replace(chr(92), '/')}\\n');
                        loaded_data = load('{mat_file_path.replace(chr(92), '/')}');
                        
                        % Display what variables we found
                        var_names = fieldnames(loaded_data);
                        fprintf('Variables in file: %s\\n', strjoin(var_names, ', '));
                        
                        % Try to find ICA data variable automatically
                        data_to_browse = [];
                        var_used = '';
                        
                        % Check common variable names
                        if isfield(loaded_data, 'data_ICApplied')
                            data_to_browse = loaded_data.data_ICApplied;
                            var_used = 'data_ICApplied';
                        elseif isfield(loaded_data, 'data_ICA')
                            data_to_browse = loaded_data.data_ICA;
                            var_used = 'data_ICA';
                        elseif isfield(loaded_data, 'old_ICApplied')
                            data_to_browse = loaded_data.old_ICApplied;
                            var_used = 'old_ICApplied';
                        else
                            % Use the first variable that's not metadata
                            for i = 1:length(var_names)
                                if ~startsWith(var_names{{i}}, '__')
                                    data_to_browse = loaded_data.(var_names{{i}});
                                    var_used = var_names{{i}};
                                    break;
                                end
                            end
                        end
                        
                        if isempty(data_to_browse)
                            error('No suitable data variable found in file');
                        end
                        
                        fprintf('Using variable: %s\\n', var_used);
                        
                        % Check data structure
                        if length(data_to_browse) > 0
                            fprintf('Data contains %d subject(s)\\n', length(data_to_browse));
                        else
                            error('Data variable is empty');
                        end
                        
                        % Set colormap and launch ft_databrowser
                        set(groot, 'DefaultFigureColormap', jet);
                        
                        cfg = [];
                        cfg.layout = 'easycapM11.lay';
                        cfg.viewmode = 'component';
                        cfg.allowoverlap = 'yes';
                        
                        fprintf('Launching ft_databrowser for subject 1...\\n');
                        ft_databrowser(cfg, data_to_browse(1));
                        
                        fprintf('ICA component browser is now open. Close the browser window when finished.\\n');
                        
                    catch ME
                        fprintf('Error: %s\\n', ME.message);
                        fprintf('Stack trace:\\n');
                        for i = 1:length(ME.stack)
                            fprintf('  %s (line %d)\\n', ME.stack(i).name, ME.stack(i).line);
                        end
                    end
                    """
                    
                    result = subprocess.run([
                        matlab_path, 
                        "-desktop",  # Launch full MATLAB desktop
                        "-r", matlab_commands
                    ], timeout=None)  # Remove timeout to let user interact
                    
                    print(f"MATLAB ICA browser completed with return code: {result.returncode}")
                    
                    if result.returncode == 0:
                        success_msg = "MATLAB ICA browser session completed successfully!"
                    else:
                        success_msg = f"MATLAB ICA browser session ended with return code: {result.returncode}"
                    
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