import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import "."

ScrollView {
    anchors.fill: parent
    clip: true

    Column {
        width: parent.width
        spacing: 10

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
