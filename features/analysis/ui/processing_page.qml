import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import "."
import "../../preprocessing/ui"

ScrollView {
    id: scrollArea
    property bool editModeEnabled: false
    property string currentFolder: ""
    property var folderContents: []
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    anchors.topMargin: 5
    clip: true
    contentWidth: availableWidth

    Column {
        width: scrollArea.availableWidth
        spacing: 1

        ModuleTemplate {
            displayText: "ERP Analysis"
            moduleName: "ERP Analysis"
            currentFolder: scrollArea.currentFolder
            folderContents: scrollArea.folderContents

            onButtonClicked: {
                if (!validateTargetFile()) {
                    errorText.text = errorMessage
                    return
                }
                
                errorText.text = ""
                var sanitizedFolder = currentFolder.replace(/^[^\w]+/, '').trim()
                var basePath = sanitizedFolder.length > 0 ? sanitizedFolder : currentFolder
                var normalizedFolder = basePath.replace(/\\/g, "/")
                var escapedFolder = normalizedFolder.replace(/'/g, "\\'")
                // Trigger MATLAB analysis for the cleaned ICA data in the selected folder
                matlabExecutor.runMatlabScriptInteractive("decomp_timelock_func('" + escapedFolder + "')", true)
            }
        }
        ModuleTemplate {
            displayText: "Time-Frequency Analysis"
            moduleName: "Time-Frequency Analysis"
        }

        ModuleTemplate {
            displayText: "Inter-Trial Coherence Analysis"
            moduleName: "Inter-Trial Coherence Analysis"
        }

        ModuleTemplate {
            displayText: "Channel-Wise Coherence Analysis"
            moduleName: "Channel-Wise Coherence Analysis"
        }

        ModuleTemplate {
            displayText: "Spectral Analysis"
            moduleName: "Spectral Analysis"
        }
    }
}
