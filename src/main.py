import sys
import os

# Set Qt Quick Controls style to Fusion (supports customization)
os.environ['QT_QUICK_CONTROLS_STYLE'] = 'Fusion'

# Add the project root to Python path so we can import from features/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
from PyQt6.QtWidgets import QApplication  # Changed from QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtCore import QStandardPaths
import features

# Import our custom classes
from features.preprocessing.python.file_browser import FileBrowser
from src.matlab_executor import MatlabExecutor

# Function to get the resource path (works for both development and PyInstaller)
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = QApplication(sys.argv)  # Changed to QApplication for widget support

# Register classes with QML
qmlRegisterType(MatlabExecutor, "MatlabExecutor", 1, 0, "MatlabExecutor")
qmlRegisterType(FileBrowser, "FileBrowser", 1, 0, "FileBrowser")


# Create instances
matlab_executor = MatlabExecutor()
file_browser = FileBrowser()

engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)

# Add import paths for QML
engine.addImportPath(os.path.join(project_root, "features", "preprocessing", "ui"))
engine.addImportPath(os.path.join(project_root, "UI"))

# Make instances available to QML
engine.rootContext().setContextProperty("matlabExecutor", matlab_executor)
engine.rootContext().setContextProperty("fileBrowser", file_browser)

engine.load(QUrl.fromLocalFile(os.path.join(project_root, 'UI', 'main.qml')))

# Initialize file browser with the current data directory from MATLAB script
current_data_dir = matlab_executor.getCurrentDataDirectory()
if current_data_dir:
    file_browser.initializeWithPath(current_data_dir)

sys.exit(app.exec())