import QtQuick 2.15

Rectangle {
    property int lineWidth: 1
    property int lineHeight: 20
    property color lineColor: "#2a2a2aff"
    property color borderColor: "#2a2a2aff"

    width: lineWidth
    height: lineHeight
    color: lineColor
    border.color: borderColor
    anchors.horizontalCenter: parent.horizontalCenter
}
