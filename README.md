# Capstone EEG Preprocessing Application

A modern, user-friendly GUI application for EEG data preprocessing using MATLAB and FieldTrip, built with Python and Qt/QML.

## Overview

This application provides an intuitive graphical interface for configuring and executing EEG data preprocessing pipelines. It integrates seamlessly with MATLAB and the FieldTrip toolbox to perform advanced signal processing operations including trial definition, channel selection, baseline correction, DFT filtering, and Independent Component Analysis (ICA).

## Features

### 🎯 Core Functionality

- **Batch Processing**: Process multiple EEG files (.set format) simultaneously
- **Interactive Configuration**: Real-time parameter adjustment with immediate MATLAB script updates
- **Trial Definition**: Flexible trial segmentation based on event markers
- **Channel Selection**: Multi-select interface for choosing relevant EEG channels
- **Baseline Correction**: Configurable baseline window for artifact removal
- **DFT Filtering**: Power line noise removal with adjustable frequency ranges
- **ICA Processing**: Automatic Independent Component Analysis for artifact identification

### 🎨 Modern UI/UX

- **Qt/QML Interface**: Beautiful, responsive graphical user interface
- **Modular Components**: Reusable QML templates for consistent UI elements
- **Real-time Feedback**: Live parameter validation and processing status
- **File Browser Integration**: Intuitive data directory selection and management

### 🔧 Technical Features

- **MATLAB Integration**: Seamless communication with MATLAB engine
- **FieldTrip Compatibility**: Full support for FieldTrip preprocessing functions
- **Background Processing**: Non-blocking MATLAB execution with progress tracking
- **Configuration Persistence**: Automatic saving of preprocessing parameters
- **Error Handling**: Comprehensive error reporting and recovery

## Architecture

### Project Structure

```
Capstone/
├── src/                          # Python source code
│   ├── main.py                   # Application entry point
│   └── matlab_executor.py        # MATLAB integration layer
├── features/                     # Feature modules
│   └── preprocessing/
│       ├── python/               # Python utilities
│       │   └── file_browser.py   # File system operations
│       ├── matlab/               # MATLAB scripts
│       │   ├── preprocessing.m   # Main preprocessing pipeline
│       │   ├── preprocess_data.m # Individual file processing
│       │   ├── applyICA.m        # ICA application
│       │   └── browse_ICA.m      # ICA component browser
│       └── ui/                   # QML user interface
│           ├── preprocessing_page.qml
│           ├── DropdownTemplate.qml
│           └── RangeSliderTemplate.qml
├── UI/                           # Main application UI
│   ├── main.qml                  # Main application window
│   ├── FileBrowserUI.qml         # File browser component
│   └── TopMenu.qml               # Application menu
└── build/                        # PyInstaller build artifacts
```

### Technology Stack

#### Frontend

- **Qt/QML 6**: Modern declarative UI framework
- **Qt Quick Controls**: Pre-built UI components
- **Custom QML Components**: Specialized templates for EEG preprocessing

#### Backend

- **Python 3.8+**: Core application logic
- **PyQt6**: Qt bindings for Python
- **MATLAB Engine**: MATLAB integration for signal processing
- **FieldTrip**: EEG/MEG analysis toolbox

#### Signal Processing

- **FieldTrip**: Comprehensive EEG analysis framework
- **FastICA**: Independent Component Analysis algorithm
- **DFT Filtering**: Digital frequency domain filtering

## Installation

### Prerequisites

1. **Python 3.8 or higher**

   ```bash
   # Download from python.org or use conda
   python --version
   ```

2. **MATLAB R2023a or compatible**

   - Install MATLAB with Signal Processing Toolbox
   - Note the installation path for configuration

3. **FieldTrip Toolbox**
   ```matlab
   % In MATLAB command window
   addpath('C:\path\to\fieldtrip')
   ft_defaults
   ```

### Dependencies

Install Python dependencies:

```bash
pip install PyQt6 scipy
```

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Capstone
   ```

2. **Configure MATLAB Path**

   - Open `src/matlab_executor.py`
   - Update the `matlab_path` variable to point to your MATLAB executable:

   ```python
   matlab_path = r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe"
   ```

3. **Configure FieldTrip Path**
   - Open `features/preprocessing/matlab/preprocessing.m`
   - Update the FieldTrip path:
   ```matlab
   addpath('C:\path\to\your\fieldtrip\installation');
   ```

## Usage

### Running the Application

```bash
cd src
python main.py
```

### Workflow

1. **Data Directory Setup**

   - Use the file browser to select your EEG data directory
   - Ensure .set files are present in the selected directory

2. **Preprocessing Configuration**

   - **Trial Definition**: Set prestimulus and poststimulus windows
   - **Event Selection**: Choose stimulus event types and values
   - **Channel Selection**: Select relevant EEG channels
   - **Baseline Correction**: Configure baseline window for artifact removal
   - **DFT Filtering**: Set frequency range for power line noise removal

3. **Execute Processing**

   - Click "Preprocess and Run ICA" to start batch processing
   - Monitor progress in the application status area
   - View results in MATLAB workspace and saved .mat files

4. **ICA Component Analysis** (Optional)
   - Use the ICA browser to inspect and remove artifact components
   - Save cleaned data for further analysis

### Configuration Parameters

| Parameter                 | Description                     | Default                    | Range      |
| ------------------------- | ------------------------------- | -------------------------- | ---------- |
| `cfg.trialfun`            | Trial definition function       | `ft_trialfun_general`      | -          |
| `cfg.trialdef.eventtype`  | Event type for trials           | `Stimulus`                 | -          |
| `cfg.trialdef.eventvalue` | Event values to process         | `['S200', 'S201', 'S202']` | -          |
| `cfg.trialdef.prestim`    | Pre-stimulus window (s)         | `0.5`                      | 0.0 - 2.0  |
| `cfg.trialdef.poststim`   | Post-stimulus window (s)        | `1.0`                      | 0.0 - 5.0  |
| `cfg.baselinewindow`      | Baseline correction window (s)  | `[-0.2, 0.0]`              | -1.0 - 1.0 |
| `cfg.dftfreq`             | DFT filter frequency range (Hz) | `[50, 60]`                 | 1 - 100    |

## MATLAB Integration

The application communicates with MATLAB through a custom executor that:

- **Reads Configuration**: Parses preprocessing.m for current settings
- **Updates Parameters**: Modifies MATLAB script variables in real-time
- **Executes Processing**: Runs preprocessing pipeline in background threads
- **Handles Output**: Captures MATLAB console output and errors
- **Manages State**: Maintains MATLAB workspace variables between operations

### Key MATLAB Functions

- `preprocess_data()`: Individual file preprocessing with configurable parameters
- `applyICA()`: Independent Component Analysis for artifact removal
- `ft_preprocessing()`: FieldTrip core preprocessing function
- `ft_componentanalysis()`: ICA decomposition using FastICA algorithm

## Development

### Building from Source

```bash
# Install development dependencies
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed src/main.py
```

### Code Structure

#### Python Components

- **`main.py`**: Application initialization and Qt setup
- **`matlab_executor.py`**: MATLAB process management and communication
- **`file_browser.py`**: File system operations and path management

#### QML Components

- **`main.qml`**: Main application window and navigation
- **`preprocessing_page.qml`**: Parameter configuration interface
- **`DropdownTemplate.qml`**: Reusable dropdown component with multi-select
- **`RangeSliderTemplate.qml`**: Configurable range slider component

#### MATLAB Scripts

- **`preprocessing.m`**: Main batch processing script
- **`preprocess_data.m`**: Single file preprocessing logic
- **`applyICA.m`**: ICA application function

### Adding New Features

1. **UI Components**: Create new QML templates in `features/preprocessing/ui/`
2. **Processing Logic**: Add MATLAB functions in `features/preprocessing/matlab/`
3. **Python Integration**: Extend `matlab_executor.py` for new operations
4. **Configuration**: Update parameter handling in preprocessing.m

## Troubleshooting

### Common Issues

**MATLAB Path Not Found**

```
Error: MATLAB executable not found
```

- Verify MATLAB installation path in `matlab_executor.py`
- Ensure MATLAB is in system PATH

**FieldTrip Not Loaded**

```
Error: Undefined function 'ft_defaults'
```

- Check FieldTrip path in `preprocessing.m`
- Run `ft_defaults` in MATLAB to verify installation

**File Access Errors**

```
Error reading current data directory
```

- Ensure data directory exists and contains .set files
- Check file permissions and MATLAB working directory

**Qt Rendering Issues**

```
QPainter::begin: Paint device returned engine == 0
```

- Run application in graphical environment
- Check Qt installation and display drivers

### Debug Mode

Enable verbose logging:

```python
# In matlab_executor.py
print(f"Debug: {variable_name}")
```

### Performance Optimization

- Process files in batches to manage memory usage
- Use background threads for long-running MATLAB operations
- Monitor MATLAB workspace size for large datasets

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

### Code Standards

- Follow PEP 8 for Python code
- Use QML best practices for UI components
- Document MATLAB functions with comments
- Test changes with sample EEG datasets

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **FieldTrip**: Open-source MATLAB toolbox for MEG/EEG analysis
- **Qt Project**: Cross-platform application framework
- **MATLAB**: Technical computing environment
- **EEG Community**: For open-source tools and methodologies

## Support

For issues, questions, or contributions:

- Create an issue in the repository
- Check the troubleshooting section
- Review the code documentation

---

**Note**: This application requires MATLAB and FieldTrip licenses for full functionality. Ensure compliance with institutional software licensing policies.</content>
<parameter name="filePath">c:\Users\mamam\Desktop\Capstone\README.md
