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


    Column {
        width: scrollArea.availableWidth
        spacing: 1

        ClassifierTemplate {
            displayText: "CNN Classifier"
        }

        ClassifierTemplate {
            displayText: "DBN Classifier"
        }
    }
}
