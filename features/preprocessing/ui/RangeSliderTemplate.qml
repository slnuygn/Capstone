import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: rangeSliderTemplate
    width: parent ? parent.width : 300
    height: 80

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

    // Signals
    signal rangeChanged(real firstValue, real secondValue)

    Column {
        width: parent.width
        spacing: 10

        Text {
            text: matlabProperty + " = [" + rangeSlider.first.value.toFixed(1) + unit + " " + rangeSlider.second.value.toFixed(1) + unit + "]"
            font.pixelSize: 12
            color: "#666"
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
    }
}