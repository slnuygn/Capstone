import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import "."

ScrollView {
    id: scrollArea
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

        ModuleTemplate {
            displayText: "ERP Analysis"
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
