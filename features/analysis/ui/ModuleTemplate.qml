import QtQuick 2.15
import QtQuick.Window 2.15

Item {
    id: moduleTemplate
    width: parent.width
    height: rectangle.height + 4
    z: 1000 

    property string displayText: "Analysis Module"

    Rectangle {
        id: rectangle
        width: parent.width - 10
        height: text.implicitHeight + 20
        anchors.top: parent.top
        anchors.topMargin: 2
        anchors.horizontalCenter: parent.horizontalCenter
        color: "#f0f0f0"
        border.color: "#ccc"
        border.width: 1
        radius: 3

        Text {
            id: text
            text: displayText
            font.pixelSize: 24
            color: "#333"
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 10
        }
    }
}
