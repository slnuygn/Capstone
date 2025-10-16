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
                    firstValue: -1
                    secondValue: 1.5
                    stepSize: 0.1
                    unit: " ms"
                    width: parent.width * 0.1
                    backgroundColor: "white"

                    onRangeChanged: function(first, second) {
                        if (typeof matlabExecutor !== "undefined" && matlabExecutor.saveRangeSliderPropertyToMatlab) {
                            matlabExecutor.saveRangeSliderPropertyToMatlab(matlabProperty, first, second, unit)
                        }
                    }
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
                            radius: 3
                            anchors.fill: parent
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
