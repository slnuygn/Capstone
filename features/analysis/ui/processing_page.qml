import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import "."
import "../../preprocessing/ui"

ScrollView {
    id: scrollArea
    property bool editModeEnabled: false
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    anchors.topMargin: 5
    clip: true
    contentWidth: availableWidth

    function setEditMode(enabled) {
        editModeEnabled = enabled
        var newState = enabled ? "edit" : "default"
        if (erpRangeSlider) {
            erpRangeSlider.sliderState = newState
        }
    }

    function setErpLatencyRange(fromValue, toValue) {
        if (!erpRangeSlider)
            return

        if (typeof fromValue === "number") {
            var snappedFrom = erpRangeSlider.snapValue ? erpRangeSlider.snapValue(fromValue) : fromValue
            if (snappedFrom < erpRangeSlider.from) {
                erpRangeSlider.from = snappedFrom
            }
            erpRangeSlider.firstValue = snappedFrom
        }

        if (typeof toValue === "number") {
            var snappedTo = erpRangeSlider.snapValue ? erpRangeSlider.snapValue(toValue) : toValue
            if (snappedTo > erpRangeSlider.to) {
                erpRangeSlider.to = snappedTo
            }
            erpRangeSlider.secondValue = snappedTo
        }
    }

    Column {
        width: scrollArea.availableWidth
        spacing: 1

        ModuleTemplate {
            displayText: "ERP Analysis"
            expanded: true

            Column {
                width: parent.width
                spacing: 10

                RangeSliderTemplate {
                    id: erpRangeSlider
                    sliderId: "erpRangeSlider"
                    label: "ERP Time Window"
                    matlabProperty: "cfg.latency"
                    from: -1
                    to: 1.5
                    firstValue: 0
                    secondValue: 1
                    stepSize: 0.1
                    unit: " ms"
                    width: parent.width * 0.1
                    backgroundColor: "white"

                    // Removed automatic saving on range change
                }

                Text {
                    id: errorText
                    text: ""
                    color: "red"
                    visible: text !== ""
                    font.pixelSize: 12
                }

                Item {
                    width: parent.width
                    height: decomposeButton.implicitHeight

                    Button {
                        id: decomposeButton
                        text: "Decompose and Timelock"
                        anchors.right: parent.right
                        flat: true
                        padding: 10
                        background: Rectangle {
                            color: "#2196f3"
                            radius: 4
                            anchors.fill: parent
                        }

                        onClicked: {
                            errorText.text = ""
                            var folder = fileBrowser.currentFolder
                            if (!folder) {
                                errorText.text = "No folder selected"
                                return
                            }
                            var contents = fileBrowser.folderContents
                            var targetFileName = "data_ICApplied_clean.mat"
                            var foundCleanMat = false
                            for (var i = 0; i < contents.length; i++) {
                                var rawEntry = contents[i]
                                var sanitizedEntry = rawEntry.replace(/^[^\w]+/, '').trim()
                                if (sanitizedEntry.toLowerCase() === targetFileName.toLowerCase()) {
                                    foundCleanMat = true
                                    break
                                }
                            }
                            if (!foundCleanMat) {
                                errorText.text = "data_ICApplied_clean.mat not found in the selected folder"
                                return
                            }
                            var sanitizedFolder = folder.replace(/^[^\w]+/, '').trim()
                            var basePath = sanitizedFolder.length > 0 ? sanitizedFolder : folder
                            var normalizedFolder = basePath.replace(/\\/g, "/")
                            var escapedFolder = normalizedFolder.replace(/'/g, "\\'")
                            // Save current slider values to MATLAB before running the function
                            matlabExecutor.saveRangeSliderPropertyToMatlab("cfg.latency", erpRangeSlider.firstValue, erpRangeSlider.secondValue, " ms")
                            // Trigger MATLAB analysis for the cleaned ICA data in the selected folder
                            matlabExecutor.runMatlabScriptInteractive("decomp_timelock_func('" + escapedFolder + "')", true)
                        }
                    }
                }
            }
        }
        ModuleTemplate {
            displayText: "Time-Frequency Analysis"
        }

        ModuleTemplate {
            displayText: "Connectivity Analysis"
        }
        ModuleTemplate {
            displayText: "Spectral Analysis"
        }
    }
}
