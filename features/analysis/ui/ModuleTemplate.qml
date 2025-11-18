import QtQuick 2.15
import QtQuick.Window 2.15

Item {
    id: moduleTemplate
    width: parent.width
    height: rectangle.height + 4 + (expanded ? expandedRect.height + 2 : 0)
    z: 1000 

    property string displayText: "Analysis Module"
    property bool expanded: false
    signal buttonClicked()
    default property alias expandedContent: contentContainer.data

    MouseArea {
        anchors.fill: parent
        onClicked: expanded = !expanded
    }

    Rectangle {
        id: rectangle
        width: parent.width - 10
        height: text.implicitHeight + 10
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

        Text {
            id: arrow
            text: "▼"
            font.pixelSize: 12
            color: "#666"
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: 10
        }
    }

    Rectangle {
        id: expandedRect
        visible: expanded
        width: parent.width - 10
        height: expanded ? Math.max(contentContainer.implicitHeight + 20, 120) : 0
        anchors.top: rectangle.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 1
        color: "#e0e0e0"
        border.color: "#ccc"
        border.width: 1
        radius: 3

        Column {
            id: contentContainer
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 10
            spacing: 10
        }

        Item {
            width: parent.width - 20
            height: moduleButton.implicitHeight
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 10

            Button {
                id: moduleButton
                text: "Feature Extract"
                anchors.right: parent.right
                flat: true
                padding: 10
                background: Rectangle {
                    color: "#2196f3"
                    radius: 4
                    anchors.fill: parent
                }

                onClicked: {
                    moduleTemplate.buttonClicked()
                }
            }
        }
    }
}
