import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: triSliderTemplate
    width: parent ? parent.width * 0.75 : 225
    height: Math.max(80, contentColumn ? contentColumn.implicitHeight : 80)

    // Properties for customization
    property string label: "Tri Slider Label"
    property string matlabProperty: "cfg.property"
    property real from: 0.0
    property real to: 1.0
    property real firstValue: 0.0
    property real secondValue: 0.5
    property real thirdValue: 1.0
    property real stepSize: 0.1
    property string unit: ""
    property bool enabled: true
    property string sliderState: "default"  // "default", "edit", or "add"
    property string matlabPropertyDraft: matlabProperty
    property string sliderId: ""  // Identifier for the slider instance
    property color backgroundColor: "#e0e0e0"

    function calculateDecimalPlaces(step) {
        if (step <= 0) {
            return 3
        }
        var stepString = step.toString()
        var scientificIndex = stepString.indexOf("e-")
        if (scientificIndex !== -1) {
            var exponentText = stepString.substring(scientificIndex + 2)
            var exponentValue = parseInt(exponentText)
            if (!isNaN(exponentValue)) {
                return Math.min(6, Math.max(0, exponentValue))
            }
        }
        var decimalIndex = stepString.indexOf('.')
        if (decimalIndex !== -1) {
            return Math.min(6, Math.max(0, stepString.length - decimalIndex - 1))
        }
        return 0
    }

    function formatValue(value) {
        var precision = triSliderTemplate.decimalPlaces
        if (precision < 0) {
            precision = 0
        } else if (precision > 6) {
            precision = 6
        }
        var factor = Math.pow(10, precision)
        var rounded = Math.round(Number(value) * factor) / factor
        var fixedString = rounded.toFixed(precision)
        if (precision > 0) {
            fixedString = fixedString.replace(/(\.\d*?[1-9])0+$/, '$1')
            fixedString = fixedString.replace(/\.0+$/, '')
        }
        if (fixedString === "-0") {
            fixedString = "0"
        }
        return fixedString
    }

    property int decimalPlaces: calculateDecimalPlaces(stepSize)

    onDecimalPlacesChanged: {
        if (fromInput && !fromInput.activeFocus) {
            fromInput.text = formatValue(from)
        }
        if (toInput && !toInput.activeFocus) {
            toInput.text = formatValue(to)
        }
        if (firstValueInput && !firstValueInput.activeFocus) {
            firstValueInput.text = formatValue(firstValue)
        }
        if (secondValueInput && !secondValueInput.activeFocus) {
            secondValueInput.text = formatValue(secondValue)
        }
        if (thirdValueInput && !thirdValueInput.activeFocus) {
            thirdValueInput.text = formatValue(thirdValue)
        }
    }

    // Dynamic z-index management
    property int baseZ: 1000
    property int activeZ: 2000

    onActiveFocusChanged: {
        z = activeFocus ? activeZ : baseZ
    }

    onMatlabPropertyChanged: {
        if (sliderState !== "add") {
            matlabPropertyDraft = matlabProperty
        }
    }

    onFromChanged: {
        if (fromInput && !fromInput.activeFocus) {
            fromInput.text = formatValue(from)
        }
    }

    onToChanged: {
        if (toInput && !toInput.activeFocus) {
            toInput.text = formatValue(to)
        }
    }

    onFirstValueChanged: {
        if (firstValueInput && !firstValueInput.activeFocus) {
            firstValueInput.text = formatValue(firstValue)
        }
    }

    onSecondValueChanged: {
        if (secondValueInput && !secondValueInput.activeFocus) {
            secondValueInput.text = formatValue(secondValue)
        }
    }

    onThirdValueChanged: {
        if (thirdValueInput && !thirdValueInput.activeFocus) {
            thirdValueInput.text = formatValue(thirdValue)
        }
    }

    onSliderStateChanged: {
        if (sliderState === "add") {
            matlabPropertyDraft = matlabProperty
            if (propertyInput) {
                Qt.callLater(function() {
                    propertyInput.forceActiveFocus()
                    propertyInput.selectAll()
                })
            }
        }
    }

    // Signals
    signal rangeChanged(real firstValue, real secondValue, real thirdValue)

    function snapValue(value) {
        if (triSlider && typeof triSlider.snapToStep === "function") {
            return triSlider.snapToStep(value)
        }
        return value
    }
    signal deleteRequested()
    signal propertySaveRequested(string propertyValue, real firstValue, real secondValue, real thirdValue, string unit)

    Column {
        id: contentColumn
        width: parent.width
        spacing: 10

        Item {
            width: parent.width
            implicitHeight: propertyDisplay.visible ? propertyDisplay.implicitHeight : propertyEditColumn.implicitHeight

            Text {
                id: propertyDisplay
                visible: sliderState !== "add"
                text: matlabProperty + " = [" + triSliderTemplate.formatValue(triSlider.firstValue) + unit + " " +
                      triSliderTemplate.formatValue(triSlider.secondValue) + unit + " " +
                      triSliderTemplate.formatValue(triSlider.thirdValue) + unit + "]"
                font.pixelSize: 12
                color: "#666"
                wrapMode: Text.Wrap
                width: parent.width

                MouseArea {
                    anchors.fill: parent
                    onDoubleClicked: {
                        sliderState = "edit"
                    }
                }
            }

            Row {
                id: propertyEditColumn
                visible: sliderState === "add"
                width: parent.width
                spacing: 8

                Rectangle {
                    width: parent.width * 0.33
                    height: 32
                    color: "#f5f5f5"
                    border.color: "#ccc"
                    border.width: 1
                    radius: 3

                    TextInput {
                        id: propertyInput
                        anchors.fill: parent
                        anchors.margins: 6
                        text: triSliderTemplate.matlabPropertyDraft
                        font.pixelSize: 12
                        color: "#333"
                        selectByMouse: true
                        verticalAlignment: TextInput.AlignVCenter
                        topPadding: 0
                        bottomPadding: 0
                        onTextChanged: {
                            if (triSliderTemplate.matlabPropertyDraft !== text) {
                                triSliderTemplate.matlabPropertyDraft = text
                                triSliderTemplate.matlabProperty = text
                            }
                        }
                    }

                    Text {
                        anchors.verticalCenter: propertyInput.verticalCenter
                        anchors.left: propertyInput.left
                        anchors.right: propertyInput.right
                        anchors.leftMargin: 6
                        anchors.rightMargin: 6
                        text: "cfg."
                        font.pixelSize: 12
                        color: "#999"
                        elide: Text.ElideRight
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignLeft
                        visible: propertyInput.text.length === 0 && !propertyInput.activeFocus
                    }
                }

                Text {
                    id: valuePreview
                    anchors.verticalCenter: parent.verticalCenter
                    text: "= [" + triSliderTemplate.formatValue(triSlider.firstValue) + unit + " " +
                          triSliderTemplate.formatValue(triSlider.secondValue) + unit + " " +
                          triSliderTemplate.formatValue(triSlider.thirdValue) + unit + "]"
                    font.pixelSize: 12
                    color: "#666"
                    wrapMode: Text.NoWrap
                    elide: Text.ElideRight
                    width: parent.width - propertyEditColumn.spacing - (parent.width * 0.33)
                }
            }
        }

        // Custom TriSlider implementation
        Item {
            id: triSlider
            width: parent.width
            height: 40
            property real firstValue: triSliderTemplate.firstValue
            property real secondValue: triSliderTemplate.secondValue
            property real thirdValue: triSliderTemplate.thirdValue

            // Background track
            Rectangle {
                id: track
                x: 10
                y: parent.height / 2 - height / 2
                width: parent.width - 20
                height: 6
                radius: 3
                color: backgroundColor

                // First range (from start to first handle)
                Rectangle {
                    x: 0
                    width: firstHandle.x - track.x
                    height: parent.height
                    color: triSlider.enabled ? "#e3f2fd" : "#f5f5f5"
                    radius: 3
                }

                // Second range (between first and second handles)
                Rectangle {
                    x: firstHandle.x - track.x
                    width: secondHandle.x - firstHandle.x
                    height: parent.height
                    color: triSlider.enabled ? "#bbdefb" : "#eeeeee"
                    radius: 3
                }

                // Third range (between second and third handles)
                Rectangle {
                    x: secondHandle.x - track.x
                    width: thirdHandle.x - secondHandle.x
                    height: parent.height
                    color: triSlider.enabled ? "#90caf9" : "#e0e0e0"
                    radius: 3
                }

                // Fourth range (from third handle to end)
                Rectangle {
                    x: thirdHandle.x - track.x
                    width: track.width - (thirdHandle.x - track.x)
                    height: parent.height
                    color: triSlider.enabled ? "#64b5f6" : "#cccccc"
                    radius: 3
                }
            }

            // First handle
            Rectangle {
                id: firstHandle
                x: track.x + (triSlider.firstValue - triSliderTemplate.from) / (triSliderTemplate.to - triSliderTemplate.from) * track.width - width / 2
                y: track.y - height / 2 + track.height / 2
                width: 20
                height: 20
                radius: 10
                color: triSlider.enabled ? "#2196f3" : "#cccccc"
                border.color: triSlider.enabled ? "#1976d2" : "#999999"
                border.width: 2
                visible: triSlider.enabled

                MouseArea {
                    id: firstMouseArea
                    anchors.fill: parent
                    drag.target: firstHandle
                    drag.axis: Drag.XAxis
                    drag.minimumX: track.x - firstHandle.width / 2
                    drag.maximumX: secondHandle.x - firstHandle.width / 2

                    onPositionChanged: {
                        if (drag.active) {
                            var newValue = triSliderTemplate.from + (firstHandle.x + firstHandle.width / 2 - track.x) / track.width * (triSliderTemplate.to - triSliderTemplate.from)
                            var snapped = snapToStep(newValue)
                            triSlider.firstValue = snapped
                            triSliderTemplate.firstValue = snapped
                            rangeChanged(triSlider.firstValue, triSlider.secondValue, triSlider.thirdValue)
                            updateQmlFile()
                        }
                    }
                }
            }

            // Second handle
            Rectangle {
                id: secondHandle
                x: track.x + (triSlider.secondValue - triSliderTemplate.from) / (triSliderTemplate.to - triSliderTemplate.from) * track.width - width / 2
                y: track.y - height / 2 + track.height / 2
                width: 20
                height: 20
                radius: 10
                color: triSlider.enabled ? "#2196f3" : "#cccccc"
                border.color: triSlider.enabled ? "#1976d2" : "#999999"
                border.width: 2
                visible: triSlider.enabled

                MouseArea {
                    id: secondMouseArea
                    anchors.fill: parent
                    drag.target: secondHandle
                    drag.axis: Drag.XAxis
                    drag.minimumX: firstHandle.x + firstHandle.width / 2
                    drag.maximumX: thirdHandle.x - secondHandle.width / 2

                    onPositionChanged: {
                        if (drag.active) {
                            var newValue = triSliderTemplate.from + (secondHandle.x + secondHandle.width / 2 - track.x) / track.width * (triSliderTemplate.to - triSliderTemplate.from)
                            var snapped = snapToStep(newValue)
                            triSlider.secondValue = snapped
                            triSliderTemplate.secondValue = snapped
                            rangeChanged(triSlider.firstValue, triSlider.secondValue, triSlider.thirdValue)
                            updateQmlFile()
                        }
                    }
                }
            }

            // Third handle
            Rectangle {
                id: thirdHandle
                x: track.x + (triSlider.thirdValue - triSliderTemplate.from) / (triSliderTemplate.to - triSliderTemplate.from) * track.width - width / 2
                y: track.y - height / 2 + track.height / 2
                width: 20
                height: 20
                radius: 10
                color: triSlider.enabled ? "#2196f3" : "#cccccc"
                border.color: triSlider.enabled ? "#1976d2" : "#999999"
                border.width: 2
                visible: triSlider.enabled

                MouseArea {
                    id: thirdMouseArea
                    anchors.fill: parent
                    drag.target: thirdHandle
                    drag.axis: Drag.XAxis
                    drag.minimumX: secondHandle.x + secondHandle.width / 2
                    drag.maximumX: track.x + track.width - thirdHandle.width / 2

                    onPositionChanged: {
                        if (drag.active) {
                            var newValue = triSliderTemplate.from + (thirdHandle.x + thirdHandle.width / 2 - track.x) / track.width * (triSliderTemplate.to - triSliderTemplate.from)
                            var snapped = snapToStep(newValue)
                            triSlider.thirdValue = snapped
                            triSliderTemplate.thirdValue = snapped
                            rangeChanged(triSlider.firstValue, triSlider.secondValue, triSlider.thirdValue)
                            updateQmlFile()
                        }
                    }
                }
            }

            function snapToStep(value) {
                var step = triSliderTemplate.stepSize > 0 ? triSliderTemplate.stepSize : 0.1
                var snapped = Math.round((value - triSliderTemplate.from) / step) * step + triSliderTemplate.from
                var precision = triSliderTemplate.decimalPlaces
                var factor = Math.pow(10, precision)
                return Math.round(snapped * factor) / factor
            }
        }

        // Edit mode inputs
        Column {
            width: parent.width
            spacing: 5
            visible: sliderState === "edit" || sliderState === "add"

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
                    Component.onCompleted: text = triSliderTemplate.formatValue(triSliderTemplate.from)
                    onActiveFocusChanged: {
                        if (!activeFocus) {
                            text = formatValue(triSliderTemplate.from)
                        }
                    }
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
                    Component.onCompleted: text = triSliderTemplate.formatValue(triSliderTemplate.to)
                    onActiveFocusChanged: {
                        if (!activeFocus) {
                            text = formatValue(triSliderTemplate.to)
                        }
                    }
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
                    font.pixelSize: 11
                    color: "#333"
                    background: Rectangle {
                        color: "#f5f5f5"
                        border.color: "#ccc"
                        border.width: 1
                        radius: 3
                    }
                    validator: DoubleValidator { bottom: triSliderTemplate.from; top: triSliderTemplate.to }
                    onAccepted: updateFirstValue()
                    Component.onCompleted: text = triSliderTemplate.formatValue(triSliderTemplate.firstValue)
                    onActiveFocusChanged: {
                        if (!activeFocus) {
                            text = formatValue(triSliderTemplate.firstValue)
                        }
                    }
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
                    font.pixelSize: 11
                    color: "#333"
                    background: Rectangle {
                        color: "#f5f5f5"
                        border.color: "#ccc"
                        border.width: 1
                        radius: 3
                    }
                    validator: DoubleValidator { bottom: triSliderTemplate.from; top: triSliderTemplate.to }
                    onAccepted: updateSecondValue()
                    Component.onCompleted: text = triSliderTemplate.formatValue(triSliderTemplate.secondValue)
                    onActiveFocusChanged: {
                        if (!activeFocus) {
                            text = formatValue(triSliderTemplate.secondValue)
                        }
                    }
                }
            }

            // Third Value input
            Row {
                spacing: 10
                Text {
                    text: "Third Value:"
                    font.pixelSize: 11
                    color: "#666"
                    anchors.verticalCenter: parent.verticalCenter
                    width: 80
                }
                TextField {
                    id: thirdValueInput
                    width: 80
                    font.pixelSize: 11
                    color: "#333"
                    background: Rectangle {
                        color: "#f5f5f5"
                        border.color: "#ccc"
                        border.width: 1
                        radius: 3
                    }
                    validator: DoubleValidator { bottom: triSliderTemplate.from; top: triSliderTemplate.to }
                    onAccepted: updateThirdValue()
                    Component.onCompleted: text = triSliderTemplate.formatValue(triSliderTemplate.thirdValue)
                    onActiveFocusChanged: {
                        if (!activeFocus) {
                            text = formatValue(triSliderTemplate.thirdValue)
                        }
                    }
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

    // Icons - only visible in edit/add mode, positioned to the right of the slider bar
    Column {
        x: triSlider.x + triSlider.width + 15
        y: triSlider.y + triSlider.height / 2 - height / 2
        spacing: 5
        visible: sliderState === "edit" || sliderState === "add"

        // Save icon
        Rectangle {
            width: 25
            height: 25
            color: "transparent"
            border.color: "#ccc"
            border.width: 1
            radius: 3
            visible: sliderState === "add"

            Text {
                anchors.centerIn: parent
                text: "💾"
                font.pixelSize: 12
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    triSliderTemplate.matlabPropertyDraft = propertyInput.text
                    triSliderTemplate.matlabProperty = triSliderTemplate.matlabPropertyDraft

                    if (typeof matlabExecutor !== "undefined" && matlabExecutor.saveTriSliderPropertyToMatlab) {
                        matlabExecutor.saveTriSliderPropertyToMatlab(
                                    triSliderTemplate.matlabProperty,
                                    triSlider.firstValue,
                                    triSlider.secondValue,
                                    triSlider.thirdValue,
                                    triSliderTemplate.stepSize,
                                    triSliderTemplate.unit)
                    }

                    propertySaveRequested(triSliderTemplate.matlabProperty,
                                           triSlider.firstValue,
                                           triSlider.secondValue,
                                           triSlider.thirdValue,
                                           triSliderTemplate.unit)
                    propertyInput.focus = false
                    triSliderTemplate.sliderState = "default"
                }
            }
        }

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
                    if (triSliderTemplate.matlabProperty && typeof matlabExecutor !== "undefined" && matlabExecutor.removeMatlabProperty) {
                        matlabExecutor.removeMatlabProperty(triSliderTemplate.matlabProperty)
                    }
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
        if (thirdValue < newFrom) thirdValue = newFrom
        fromInput.text = formatValue(from)
        warningText.text = ""
        rangeChanged(firstValue, secondValue, thirdValue)
        updateQmlFile()
        console.log("Updated from:", from, "firstValue:", firstValue, "secondValue:", secondValue, "thirdValue:", thirdValue)
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
        if (thirdValue > newTo) thirdValue = newTo
        toInput.text = formatValue(to)
        warningText.text = ""
        rangeChanged(firstValue, secondValue, thirdValue)
        updateQmlFile()
        console.log("Updated to:", to, "firstValue:", firstValue, "secondValue:", secondValue, "thirdValue:", thirdValue)
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
        firstValue = triSlider.snapToStep(newFirst)
        firstValueInput.text = formatValue(firstValue)
        warningText.text = ""
        rangeChanged(firstValue, secondValue, thirdValue)
        updateQmlFile()
        console.log("Updated firstValue:", firstValue, "secondValue:", secondValue, "thirdValue:", thirdValue)
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
        if (newSecond <= firstValue || newSecond >= thirdValue) {
            warningText.text = "Second value must be between first and third values"
            return
        }
        secondValue = triSlider.snapToStep(newSecond)
        secondValueInput.text = formatValue(secondValue)
        warningText.text = ""
        rangeChanged(firstValue, secondValue, thirdValue)
        updateQmlFile()
        console.log("Updated secondValue:", secondValue, "firstValue:", firstValue, "thirdValue:", thirdValue)
    }

    function updateThirdValue() {
        var newThird = parseFloat(thirdValueInput.text)
        if (isNaN(newThird)) {
            warningText.text = "Invalid third value"
            return
        }
        if (newThird < from || newThird > to) {
            warningText.text = "Third value must be between " + from.toFixed(1) + " and " + to.toFixed(1)
            return
        }
        if (newThird <= secondValue) {
            warningText.text = "Third value must be greater than second value"
            return
        }
        thirdValue = triSlider.snapToStep(newThird)
        thirdValueInput.text = formatValue(thirdValue)
        warningText.text = ""
        rangeChanged(firstValue, secondValue, thirdValue)
        updateQmlFile()
        console.log("Updated thirdValue:", thirdValue, "firstValue:", firstValue, "secondValue:", secondValue)
    }

    // Function to update QML file with current values
    function updateQmlFile() {
        // Add tri-slider specific updates here if needed
        console.log("TriSlider values updated:", firstValue, secondValue, thirdValue)
    }
}
