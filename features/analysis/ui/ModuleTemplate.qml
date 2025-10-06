import QtQuick 2.15
import QtQuick.Window 2.15

Item {
    id: moduleTemplate
    width: parent.width
    height: Screen.height / 4
    z: 1000 

    property string displayText: "Analysis Module"

    Rectangle {
        anchors.fill: parent
        anchors.margins: 10
        color: "#f0f0f0"
        border.color: "#ccc"
        border.width: 1
        radius: 5

        Text {
            text: displayText
            font.pixelSize: 24
            color: "#333"
            anchors.centerIn: parent
        }
    }
}
