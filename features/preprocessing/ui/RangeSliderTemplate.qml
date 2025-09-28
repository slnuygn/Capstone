import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: rangeSliderTemplate
    width: parent ? parent.width * 0.75 : 225
    height: (sliderState === "edit") ? 200 : 80

    // Properties for customization
    property string label: "Range Slider Label"
    property string matlabProperty: "cfg.property"
    property real from: 0.0
    property real to: 1.0
    property real firstValue: 0.0
    property real secondValue: 1.0
    property real stepSize: 0.1
    property string unit: ""
    property bool enabled: true
    property string sliderState: "default"  // "default" or "edit"
    property string sliderId: ""  // Identifier for the slider instance

    // Signals
    signal rangeChanged(real firstValue, real secondValue)
    signal deleteRequested()

    Column {
        width: parent.width
        spacing: 10

        Text {
            id: valueText
            text: matlabProperty + " = [" + rangeSlider.first.value.toFixed(1) + unit + " " + rangeSlider.second.value.toFixed(1) + unit + "]"
            font.pixelSize: 12
            color: "#666"

            // Double-click to enter edit mode
            MouseArea {
                anchors.fill: parent
                onDoubleClicked: {
                    sliderState = "edit"
                }
            }
        }

        RangeSlider {
            id: rangeSlider
            width: parent.width
            from: rangeSliderTemplate.from
            to: rangeSliderTemplate.to
            first.value: rangeSliderTemplate.firstValue
            second.value: rangeSliderTemplate.secondValue
            stepSize: rangeSliderTemplate.stepSize
            enabled: rangeSliderTemplate.enabled

            background: Rectangle {
                x: rangeSlider.leftPadding
                y: rangeSlider.topPadding + rangeSlider.availableHeight / 2 - height / 2
                implicitWidth: 200
                implicitHeight: 6
                width: rangeSlider.availableWidth
                height: implicitHeight
                radius: 3
                color: "#e0e0e0"

                // Active range
                Rectangle {
                    x: rangeSlider.first.visualPosition * parent.width
                    width: (rangeSlider.second.visualPosition - rangeSlider.first.visualPosition) * parent.width
                    height: parent.height
                    color: rangeSlider.enabled ? "#2196f3" : "#cccccc"
                    radius: 3
                }
            }

            first.handle: Rectangle {
                x: rangeSlider.leftPadding + rangeSlider.first.visualPosition * (rangeSlider.availableWidth - width)
                y: rangeSlider.topPadding + rangeSlider.availableHeight / 2 - height / 2
                implicitWidth: 20
                implicitHeight: 20
                radius: 10
                color: rangeSlider.first.pressed ? "#1976d2" : (rangeSlider.enabled ? "#2196f3" : "#cccccc")
                border.color: rangeSlider.enabled ? "#1976d2" : "#999999"
                border.width: 2
                visible: rangeSlider.enabled
            }

            second.handle: Rectangle {
                x: rangeSlider.leftPadding + rangeSlider.second.visualPosition * (rangeSlider.availableWidth - width)
                y: rangeSlider.topPadding + rangeSlider.availableHeight / 2 - height / 2
                implicitWidth: 20
                implicitHeight: 20
                radius: 10
                color: rangeSlider.second.pressed ? "#1976d2" : (rangeSlider.enabled ? "#2196f3" : "#cccccc")
                border.color: rangeSlider.enabled ? "#1976d2" : "#999999"
                border.width: 2
                visible: rangeSlider.enabled
            }

            first.onValueChanged: function() {
                rangeChanged(first.value, second.value)
            }

            second.onValueChanged: function() {
                rangeChanged(first.value, second.value)
            }
        }

        // Optional value display
        Row {
            width: parent.width
            spacing: 20
            visible: sliderState === "default"

            Text {
                text: "Min: " + rangeSlider.first.value.toFixed(1) + unit
                font.pixelSize: 11
                color: "#888"
            }

            Text {
                text: "Max: " + rangeSlider.second.value.toFixed(1) + unit
                font.pixelSize: 11
                color: "#888"
            }
        }

        // Edit mode inputs
        Column {
            width: parent.width
            spacing: 5
            visible: sliderState === "edit"

            // From input
            Row {
                spacing: 10
                Text {
                    text: "From:"
                    font.pixelSize: 11
                    color: "#666"
                    anchors.verticalCenter: parent.verticalCenter
                    width: 80
                }
                TextField {
                    id: fromInput
                    width: 80
                    font.pixelSize: 11
                    color: "#333"
                    background: Rectangle {
                        color: "#f5f5f5"
                        border.color: "#ccc"
                        border.width: 1
                        radius: 3
                    }
                    onAccepted: updateFrom()
                    Component.onCompleted: text = rangeSliderTemplate.from
                }
            }

            // To input
            Row {
                spacing: 10
                Text {
                    text: "To:"
                    font.pixelSize: 11
                    color: "#666"
                    anchors.verticalCenter: parent.verticalCenter
                    width: 80
                }
                TextField {
                    id: toInput
                    width: 80
                    font.pixelSize: 11
                    color: "#333"
                    background: Rectangle {
                        color: "#f5f5f5"
                        border.color: "#ccc"
                        border.width: 1
                        radius: 3
                    }
                    onAccepted: updateTo()
                    Component.onCompleted: text = rangeSliderTemplate.to
                }
            }

            // First Value input
            Row {
                spacing: 10
                Text {
                    text: "First Value:"
                    font.pixelSize: 11
                    color: "#666"
                    anchors.verticalCenter: parent.verticalCenter
                    width: 80
                }
                TextField {
                    id: firstValueInput
                    width: 80
                    text: rangeSlider.first.value
                    font.pixelSize: 11
                    color: "#333"
                    background: Rectangle {
                        color: "#f5f5f5"
                        border.color: "#ccc"
                        border.width: 1
                        radius: 3
                    }
                    validator: DoubleValidator { bottom: rangeSliderTemplate.from; top: rangeSliderTemplate.to }
                    onAccepted: updateFirstValue()
                }
            }

            // Second Value input
            Row {
                spacing: 10
                Text {
                    text: "Second Value:"
                    font.pixelSize: 11
                    color: "#666"
                    anchors.verticalCenter: parent.verticalCenter
                    width: 80
                }
                TextField {
                    id: secondValueInput
                    width: 80
                    text: rangeSlider.second.value
                    font.pixelSize: 11
                    color: "#333"
                    background: Rectangle {
                        color: "#f5f5f5"
                        border.color: "#ccc"
                        border.width: 1
                        radius: 3
                    }
                    validator: DoubleValidator { bottom: rangeSliderTemplate.from; top: rangeSliderTemplate.to }
                    onAccepted: updateSecondValue()
                }
            }

            // Warning text
            Text {
                id: warningText
                text: ""
                font.pixelSize: 10
                color: "red"
                visible: text !== ""
            }
        }
    }

    // Icons - only visible in edit mode, positioned to the right of the slider bar
    Column {
        x: rangeSlider.x + rangeSlider.width + 15
        y: rangeSlider.y + rangeSlider.height / 2 - height / 2
        spacing: 5
        visible: sliderState === "edit"

        // Trash icon
        Rectangle {
            width: 25
            height: 25
            color: "transparent"
            border.color: "#ccc"
            border.width: 1
            radius: 3

            Text {
                anchors.centerIn: parent
                text: "🗑️"
                font.pixelSize: 12
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    deleteRequested()
                }
            }
        }
    }

    // Functions for edit mode
    function updateFrom() {
        var newFrom = parseFloat(fromInput.text)
        if (isNaN(newFrom)) {
            warningText.text = "Invalid 'from' value"
            return
        }
        if (newFrom >= to) {
            warningText.text = "'From' must be less than 'to'"
            return
        }
        from = newFrom
        // Adjust values if necessary
        if (firstValue < newFrom) firstValue = newFrom
        if (secondValue < newFrom) secondValue = newFrom
        warningText.text = ""
        rangeChanged(firstValue, secondValue)
        updateQmlFile()
        console.log("Updated from:", from, "firstValue:", firstValue, "secondValue:", secondValue)
    }

    function updateTo() {
        var newTo = parseFloat(toInput.text)
        if (isNaN(newTo)) {
            warningText.text = "Invalid 'to' value"
            return
        }
        if (newTo <= from) {
            warningText.text = "'To' must be greater than 'from'"
            return
        }
        to = newTo
        // Adjust values if necessary
        if (firstValue > newTo) firstValue = newTo
        if (secondValue > newTo) secondValue = newTo
        warningText.text = ""
        rangeChanged(firstValue, secondValue)
        updateQmlFile()
        console.log("Updated to:", to, "firstValue:", firstValue, "secondValue:", secondValue)
    }

    function updateFirstValue() {
        var newFirst = parseFloat(firstValueInput.text)
        if (isNaN(newFirst)) {
            warningText.text = "Invalid first value"
            return
        }
        if (newFirst < from || newFirst > to) {
            warningText.text = "First value must be between " + from.toFixed(1) + " and " + to.toFixed(1)
            return
        }
        if (newFirst >= secondValue) {
            warningText.text = "First value must be less than second value"
            return
        }
        firstValue = newFirst
        warningText.text = ""
        rangeChanged(firstValue, secondValue)
        updateQmlFile()
        console.log("Updated firstValue:", firstValue, "secondValue:", secondValue)
    }

    function updateSecondValue() {
        var newSecond = parseFloat(secondValueInput.text)
        if (isNaN(newSecond)) {
            warningText.text = "Invalid second value"
            return
        }
        if (newSecond < from || newSecond > to) {
            warningText.text = "Second value must be between " + from.toFixed(1) + " and " + to.toFixed(1)
            return
        }
        if (newSecond <= firstValue) {
            warningText.text = "Second value must be greater than first value"
            return
        }
        secondValue = newSecond
        warningText.text = ""
        rangeChanged(firstValue, secondValue)
        updateQmlFile()
        console.log("Updated secondValue:", secondValue, "firstValue:", firstValue)
    }

    // Function to update QML file with current values
    function updateQmlFile() {
        if (sliderId === "baselineSlider") {
            matlabExecutor.updateBaselineSliderValues(from, to, firstValue, secondValue)
        } else if (sliderId === "dftfreqSlider") {
            matlabExecutor.updateDftfreqSliderValues(from, to, firstValue, secondValue)
        } else if (sliderId === "prestimPoststimSlider") {
            matlabExecutor.updatePrestimPoststimSliderValues(from, to, firstValue, secondValue)
        }
    }
}