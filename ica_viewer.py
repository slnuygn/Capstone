import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import scipy.io

class ICAComponentViewer(QObject):
    """
    Matplotlib-based ICA component viewer that replicates ft_databrowser functionality
    """
    
    # Signals for communication with QML
    componentsLoaded = pyqtSignal(int)  # Signal when components are loaded (number of subjects)
    componentChanged = pyqtSignal(int, int)  # Signal when component changes (subject, component)
    error = pyqtSignal(str)  # Signal for errors
    
    def __init__(self):
        super().__init__()
        self.data_ica = None
        self.current_subject = 0
        self.current_component = 0
        self.num_subjects = 0
        self.num_components = 0
        
        # Real ICA data storage
        self.topo_data = None  # Topographic maps (n_electrodes, n_components)
        self.time_series_data = None  # Time series data (n_components, n_timepoints)
        self.component_labels = []  # Component labels
        self.electrode_labels = []  # Electrode labels
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        
        # Layout for topoplot and time series
        self.ax_topo = None
        self.ax_timeseries = None
        
        # EEG electrode positions (simplified for easycapM11 layout)
        self.electrode_positions = {
            'Fz': (0.0, 0.7),
            'F3': (-0.5, 0.5),
            'F4': (0.5, 0.5),
            'C3': (-0.7, 0.0),
            'Cz': (0.0, 0.0),
            'C4': (0.7, 0.0),
            'P3': (-0.5, -0.5),
            'Pz': (0.0, -0.7),
            'P4': (0.5, -0.5),
            'O1': (-0.3, -0.9),
            'Oz': (0.0, -0.9),
            'O2': (0.3, -0.9)
        }
        
    @pyqtSlot(str)
    def loadICAData(self, file_path):
        """Load ICA data from .mat file"""
        try:
            print(f"Loading ICA data from: {file_path}")
            
            # Load the .mat file
            mat_data = scipy.io.loadmat(file_path)
            print(f"Available variables in .mat file: {list(mat_data.keys())}")
            
            # Look for the ICA data
            ica_data = None
            if 'data_ICApplied' in mat_data:
                print("Found 'data_ICApplied' variable")
                raw_data = mat_data['data_ICApplied']
            elif 'old_ICApplied' in mat_data:
                print("Found 'old_ICApplied' variable")
                raw_data = mat_data['old_ICApplied']
            elif 'data_ICA' in mat_data:
                print("Found 'data_ICA' variable")
                raw_data = mat_data['data_ICA']
            else:
                # Try to find any variable that looks like ICA data
                for key in mat_data.keys():
                    if not key.startswith('__') and ('ica' in key.lower() or 'component' in key.lower()):
                        print(f"Found potential ICA variable: {key}")
                        raw_data = mat_data[key]
                        break
                else:
                    raise ValueError(f"No recognized ICA data structure found. Available variables: {list(mat_data.keys())}")
            
            print(f"Data type: {type(raw_data)}")
            print(f"Data shape: {raw_data.shape}")
                
            # Handle struct array format
            if raw_data.dtype.names and raw_data.size > 0:
                print(f"Struct fields: {raw_data.dtype.names}")
                # Extract the struct from the array
                ica_data = raw_data[0, 0] if raw_data.shape == (1, 1) else raw_data.flat[0]
            elif raw_data.shape == (1, 2) and hasattr(raw_data[0, 0], 'dtype'):
                # Handle case where data is in a cell array
                for i in range(raw_data.shape[1]):
                    elem = raw_data[0, i]
                    if hasattr(elem, 'dtype') and elem.dtype.names:
                        print(f"Found struct in element [0,{i}] with fields: {elem.dtype.names}")
                        if 'topo' in elem.dtype.names and 'trial' in elem.dtype.names:
                            ica_data = elem
                            break
                
                if ica_data is None:
                    ica_data = raw_data[0, 0]  # Default to first element
            else:
                ica_data = raw_data
            
            if ica_data is None:
                raise ValueError("No recognized ICA data structure found")
            
            # Extract key components from the struct
            if hasattr(ica_data, 'dtype') and ica_data.dtype.names:
                fields = ica_data.dtype.names
                print(f"Processing struct with fields: {fields}")
                
                # Extract topographic maps
                if 'topo' in fields:
                    self.topo_data = ica_data['topo']
                    print(f"Topographic data shape: {self.topo_data.shape}")
                else:
                    print("Warning: No 'topo' field found")
                    self.topo_data = None
                
                # Extract time series data
                if 'trial' in fields:
                    trial_data = ica_data['trial']
                    print(f"Trial data shape: {trial_data.shape}")
                    # trial_data is typically (1, n_trials) where each element is (n_components, n_timepoints)
                    if trial_data.size > 0:
                        # Get the first trial for display
                        first_trial = trial_data.flat[0]
                        if hasattr(first_trial, 'shape'):
                            self.time_series_data = first_trial
                            print(f"Time series data shape: {self.time_series_data.shape}")
                        else:
                            print("Warning: Trial data format not recognized")
                            self.time_series_data = None
                    else:
                        self.time_series_data = None
                else:
                    print("Warning: No 'trial' field found")
                    self.time_series_data = None
                
                # Extract component labels
                if 'label' in fields:
                    labels = ica_data['label']
                    self.component_labels = []
                    for i in range(labels.shape[0]):
                        label = labels[i, 0]
                        if hasattr(label, 'flat'):
                            label_str = str(label.flat[0]) if label.size > 0 else f"IC{i+1}"
                        else:
                            label_str = str(label)
                        self.component_labels.append(label_str)
                    print(f"Component labels: {self.component_labels}")
                else:
                    # Generate default labels
                    n_components = self.topo_data.shape[1] if self.topo_data is not None else 12
                    self.component_labels = [f"IC{i+1}" for i in range(n_components)]
                    print(f"Generated default labels: {self.component_labels}")
                
                # Extract electrode labels for topography
                if 'topolabel' in fields:
                    topolabels = ica_data['topolabel']
                    self.electrode_labels = []
                    for i in range(topolabels.shape[0]):
                        label = topolabels[i, 0]
                        if hasattr(label, 'flat'):
                            label_str = str(label.flat[0]) if label.size > 0 else f"E{i+1}"
                        else:
                            label_str = str(label)
                        self.electrode_labels.append(label_str)
                    print(f"Electrode labels: {self.electrode_labels}")
                else:
                    # Default electrode labels
                    n_electrodes = self.topo_data.shape[0] if self.topo_data is not None else 12
                    self.electrode_labels = [f"E{i+1}" for i in range(n_electrodes)]
                    print(f"Generated default electrode labels: {self.electrode_labels}")
                
                # Set up data dimensions
                self.num_subjects = 1  # Single subject for now
                if self.topo_data is not None:
                    self.num_components = self.topo_data.shape[1]
                elif self.time_series_data is not None:
                    self.num_components = self.time_series_data.shape[0]
                else:
                    self.num_components = len(self.component_labels)
                
                print(f"Loaded ICA data: {self.num_subjects} subjects, {self.num_components} components")
                
                # Update the plots
                self.current_subject = 0
                self.current_component = 0
                self.setupPlots()
                self.updateDisplay()
                
                # Emit signal that data is loaded
                self.componentsLoaded.emit(self.num_subjects)
                
            else:
                raise ValueError("ICA data is not in expected struct format")
                
        except Exception as e:
            error_msg = f"Error loading ICA data: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.error.emit(error_msg)
    
    def setupPlots(self):
        """Setup the matplotlib subplot layout to match ft_databrowser"""
        self.figure.clear()
        
        # Create a layout similar to ft_databrowser
        # Left column: topographies, Right column: time series
        gs = self.figure.add_gridspec(1, 2, width_ratios=[1, 3], hspace=0.3, wspace=0.3)
        
        # Left subplot for topographies
        self.ax_topo = self.figure.add_subplot(gs[0])
        self.ax_topo.set_xlim(-1.2, 1.2)
        self.ax_topo.set_ylim(-1.2, 1.2)
        self.ax_topo.set_aspect('equal')
        self.ax_topo.set_title('Component Topographies')
        self.ax_topo.set_xticks([])
        self.ax_topo.set_yticks([])
        
        # Right subplot for time series (will show multiple components)
        self.ax_timeseries = self.figure.add_subplot(gs[1])
        self.ax_timeseries.set_title('Component Time Series')
        self.ax_timeseries.set_xlabel('Time (samples)')
        self.ax_timeseries.set_ylabel('Components')
        
        self.figure.tight_layout()
    
    def updateDisplay(self):
        """Update the display to show all components like ft_databrowser"""
        try:
            # Clear previous plots
            self.ax_topo.clear()
            self.ax_timeseries.clear()
            
            # Setup the layout
            self.setupPlots()
            
            # Plot all component topographies and time series
            self.plotAllComponents()
            
            # Update canvas
            self.canvas.draw()
            
            # Emit signal
            self.componentChanged.emit(self.current_subject + 1, self.current_component + 1)
            
        except Exception as e:
            error_msg = f"Error updating display: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)
    
    def plotAllComponents(self):
        """Plot all components similar to ft_databrowser layout"""
        try:
            if self.topo_data is None or self.time_series_data is None:
                print("No data available, creating demo display")
                self.plotDemoComponents()
                return
            
            # Set up colors for each component
            colors = plt.cm.tab10(np.linspace(0, 1, self.num_components))
            
            # Plot topographies on the left
            self.plotAllTopographies()
            
            # Plot all time series on the right
            self.plotAllTimeSeries(colors)
            
        except Exception as e:
            print(f"Error plotting all components: {e}")
            self.plotDemoComponents()
    
    def plotAllTopographies(self):
        """Plot all component topographies vertically stacked"""
        try:
            # Calculate layout for topographies
            n_rows = min(self.num_components, 10)  # Limit to 10 visible components
            topo_height = 2.0 / n_rows
            
            for comp_idx in range(n_rows):
                if comp_idx >= self.num_components:
                    break
                    
                # Get topographic data for this component
                if self.topo_data is not None and comp_idx < self.topo_data.shape[1]:
                    topo_values = self.topo_data[:, comp_idx]
                else:
                    # Generate dummy data
                    np.random.seed(comp_idx)
                    topo_values = np.random.randn(12) * 0.5 + np.sin(np.linspace(0, 2*np.pi, 12) + comp_idx)
                
                # Calculate position for this topography
                y_center = 1.0 - (comp_idx + 0.5) * topo_height
                topo_radius = topo_height * 0.3
                
                # Draw head outline for this component
                head_circle = patches.Circle((0, y_center), topo_radius, 
                                           fill=False, edgecolor='black', linewidth=1)
                self.ax_topo.add_patch(head_circle)
                
                # Draw nose
                nose_y = y_center + topo_radius
                nose = patches.Polygon([[0, nose_y], [-0.02, nose_y + 0.05], [0.02, nose_y + 0.05]], 
                                     closed=True, fill=True, facecolor='black')
                self.ax_topo.add_patch(nose)
                
                # Normalize topography values
                if len(topo_values) > 1:
                    topo_min, topo_max = np.min(topo_values), np.max(topo_values)
                    if topo_max - topo_min > 1e-10:
                        topo_normalized = (topo_values - topo_min) / (topo_max - topo_min)
                    else:
                        topo_normalized = np.zeros_like(topo_values)
                else:
                    topo_normalized = np.array([0.5])
                
                # Plot electrodes
                electrode_names = list(self.electrode_positions.keys())
                for i, (name, rel_pos) in enumerate(self.electrode_positions.items()):
                    if i < len(topo_values):
                        norm_value = topo_normalized[i]
                    else:
                        norm_value = 0.5
                    
                    # Scale and position electrode
                    electrode_x = rel_pos[0] * topo_radius * 0.8
                    electrode_y = y_center + rel_pos[1] * topo_radius * 0.8
                    
                    # Color based on component weight
                    color = plt.cm.jet(norm_value)
                    
                    # Draw electrode
                    circle = patches.Circle((electrode_x, electrode_y), topo_radius * 0.08, 
                                          facecolor=color, edgecolor='black', linewidth=0.5)
                    self.ax_topo.add_patch(circle)
                
                # Add component label
                component_label = self.component_labels[comp_idx] if comp_idx < len(self.component_labels) else f"IC{comp_idx + 1}"
                # Highlight current component
                label_color = 'red' if comp_idx == self.current_component else 'black'
                label_weight = 'bold' if comp_idx == self.current_component else 'normal'
                
                self.ax_topo.text(-1.1, y_center, component_label, 
                                ha='right', va='center', fontsize=9, 
                                color=label_color, fontweight=label_weight)
            
            self.ax_topo.set_xlim(-1.2, 1.2)
            self.ax_topo.set_ylim(-1.2, 1.2)
            self.ax_topo.set_title('Component Topographies', fontweight='bold')
            
        except Exception as e:
            print(f"Error plotting topographies: {e}")
    
    def plotAllTimeSeries(self, colors):
        """Plot all component time series stacked vertically"""
        try:
            if self.time_series_data is None:
                print("No time series data available")
                return
            
            # Calculate spacing between components
            n_components_to_show = min(self.num_components, 10)
            y_spacing = 1.0
            
            # Determine time vector
            n_timepoints = self.time_series_data.shape[1]
            time_vector = np.arange(n_timepoints)
            
            # If we have time information, use it
            if hasattr(self, 'time_data') and self.time_data is not None:
                try:
                    # Extract time vector from the first trial
                    time_info = self.time_data.flat[0] if self.time_data.size > 0 else None
                    if time_info is not None and hasattr(time_info, 'shape'):
                        time_vector = time_info
                        time_vector = time_vector[:n_timepoints]  # Match data length
                except:
                    pass
            
            # Plot each component time series
            for comp_idx in range(n_components_to_show):
                if comp_idx >= self.num_components:
                    break
                    
                # Get time series for this component
                if comp_idx < self.time_series_data.shape[0]:
                    timeseries = self.time_series_data[comp_idx, :]
                    
                    # Normalize and offset the time series
                    timeseries_norm = (timeseries - np.mean(timeseries)) / (np.std(timeseries) + 1e-10)
                    timeseries_norm = timeseries_norm * 0.3  # Scale amplitude
                    y_offset = (n_components_to_show - comp_idx - 1) * y_spacing
                    timeseries_offset = timeseries_norm + y_offset
                    
                    # Use component-specific color
                    color = colors[comp_idx % len(colors)]
                    
                    # Highlight current component
                    linewidth = 2.0 if comp_idx == self.current_component else 1.0
                    alpha = 1.0 if comp_idx == self.current_component else 0.8
                    
                    # Plot the time series
                    self.ax_timeseries.plot(time_vector, timeseries_offset, 
                                          color=color, linewidth=linewidth, alpha=alpha)
                    
                    # Add component label on the left
                    component_label = self.component_labels[comp_idx] if comp_idx < len(self.component_labels) else f"IC{comp_idx + 1}"
                    label_color = 'red' if comp_idx == self.current_component else 'black'
                    label_weight = 'bold' if comp_idx == self.current_component else 'normal'
                    
                    self.ax_timeseries.text(-0.02, y_offset, component_label, 
                                          transform=self.ax_timeseries.get_yaxis_transform(),
                                          ha='right', va='center', fontsize=9,
                                          color=label_color, fontweight=label_weight)
            
            # Add stimulus marker if we're showing trial data
            if hasattr(self, 'stimulus_time') or True:  # Default stimulus at time 0
                stimulus_time = 0  # Default to time 0
                self.ax_timeseries.axvline(x=stimulus_time, color='red', linestyle='--', 
                                         alpha=0.7, linewidth=2, label='Stimulus')
                
                # Add stimulus label
                self.ax_timeseries.text(stimulus_time, n_components_to_show * y_spacing + 0.2, 
                                      'Stimulus', ha='center', va='bottom', 
                                      color='red', fontweight='bold', fontsize=10)
            
            # Customize the plot
            self.ax_timeseries.set_xlim(0, len(time_vector))
            self.ax_timeseries.set_ylim(-0.5, n_components_to_show * y_spacing + 0.5)
            self.ax_timeseries.set_xlabel('Time (samples)', fontweight='bold')
            self.ax_timeseries.set_ylabel('Components', fontweight='bold')
            self.ax_timeseries.set_title(f'Trial 1/{self.num_components}, Time Series', fontweight='bold')
            
            # Remove y-axis ticks for cleaner look
            self.ax_timeseries.set_yticks([])
            
            # Add grid
            self.ax_timeseries.grid(True, alpha=0.3)
            
        except Exception as e:
            print(f"Error plotting time series: {e}")
    
    def plotDemoComponents(self):
        """Plot demo components when no real data is available"""
        try:
            n_components = 8
            colors = plt.cm.tab10(np.linspace(0, 1, n_components))
            
            # Demo topographies
            for i in range(n_components):
                y_pos = 1.0 - (i + 0.5) * (2.0 / n_components)
                
                # Simple head outline
                head = patches.Circle((0, y_pos), 0.15, fill=False, edgecolor='black')
                self.ax_topo.add_patch(head)
                
                # Demo electrodes
                for j, (name, pos) in enumerate(list(self.electrode_positions.items())[:6]):
                    elec_x = pos[0] * 0.12
                    elec_y = y_pos + pos[1] * 0.12
                    color = plt.cm.jet(np.random.random())
                    circle = patches.Circle((elec_x, elec_y), 0.02, facecolor=color, edgecolor='black')
                    self.ax_topo.add_patch(circle)
                
                self.ax_topo.text(-1.1, y_pos, f'fastica{i+1:03d}', ha='right', va='center', fontsize=9)
            
            # Demo time series
            time_points = np.arange(500)
            for i in range(n_components):
                np.random.seed(i)
                signal = np.cumsum(np.random.randn(500)) * 0.05
                signal += np.sin(time_points * 0.02 + i) * 0.3
                y_offset = (n_components - i - 1) * 0.8
                
                self.ax_timeseries.plot(time_points, signal + y_offset, color=colors[i])
                self.ax_timeseries.text(-10, y_offset, f'fastica{i+1:03d}', 
                                       ha='right', va='center', fontsize=9)
            
            self.ax_timeseries.axvline(x=250, color='red', linestyle='--', label='Stimulus')
            self.ax_timeseries.set_title('Demo: Component Time Series')
            self.ax_timeseries.set_xlabel('Time (samples)')
            self.ax_timeseries.set_yticks([])
            
        except Exception as e:
            print(f"Error creating demo plot: {e}")
    
    @pyqtSlot(int)
    def setSubject(self, subject_index):
        """Set the current subject (1-based index)"""
        if 0 < subject_index <= self.num_subjects:
            self.current_subject = subject_index - 1
            self.updateDisplay()
    
    @pyqtSlot(int)
    def setComponent(self, component_index):
        """Set the current component (1-based index)"""
        if 0 < component_index <= self.num_components:
            self.current_component = component_index - 1
            self.updateDisplay()
    
    @pyqtSlot()
    def nextSubject(self):
        """Move to next subject"""
        if self.current_subject < self.num_subjects - 1:
            self.current_subject += 1
            self.updateDisplay()
    
    @pyqtSlot()
    def previousSubject(self):
        """Move to previous subject"""
        if self.current_subject > 0:
            self.current_subject -= 1
            self.updateDisplay()
    
    @pyqtSlot()
    def nextComponent(self):
        """Move to next component"""
        if self.current_component < self.num_components - 1:
            self.current_component += 1
            self.updateDisplay()
    
    @pyqtSlot()
    def previousComponent(self):
        """Move to previous component"""
        if self.current_component > 0:
            self.current_component -= 1
            self.updateDisplay()

    def getWidget(self):
        """Return the matplotlib canvas widget for embedding in QML"""
        return self.canvas
