import sys
import os
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
from PyQt6.QtWidgets import QApplication  # Changed from QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtCore import QStandardPaths

# Import our custom classes
from file_browser import FileBrowser
from matlab_executor import MatlabExecutor

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

# Import and create ICA viewer
from ica_viewer import ICAComponentViewer
ica_viewer = ICAComponentViewer()

engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)

# Make instances available to QML
engine.rootContext().setContextProperty("matlabExecutor", matlab_executor)
engine.rootContext().setContextProperty("fileBrowser", file_browser)
engine.rootContext().setContextProperty("icaViewer", ica_viewer)

engine.load(QUrl.fromLocalFile(resource_path('UI/main.qml')))

# Initialize file browser with the current data directory from MATLAB script
current_data_dir = matlab_executor.getCurrentDataDirectory()
if current_data_dir:
    file_browser.initializeWithPath(current_data_dir)

sys.exit(app.exec())