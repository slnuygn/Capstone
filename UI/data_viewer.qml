import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: dataViewerWindow
    title: "MATLAB Data Viewer - " + dataName
    width: 1000
    height: 700
    minimumWidth: 600
    minimumHeight: 400
    
    property string dataName: "data"
    property var dataInfo: []
    
    signal requestDataInfo(string dataName)
    
    Component.onCompleted: {
        requestDataInfo(dataName)
    }
    
    Rectangle {
        anchors.fill: parent
        color: "#f8f9fa"
        
        Column {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 15
            
            // Header
            Row {
                width: parent.width
                spacing: 10
                
                Text {
                    text: "MATLAB Variable: " + dataName
                    font.pixelSize: 18
                    font.bold: true
                    color: "#333"
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Rectangle {
                    width: 100
                    height: 30
                    color: "#6f42c1"
                    radius: 15
                    anchors.verticalCenter: parent.verticalCenter
                    
                    Text {
                        anchors.centerIn: parent
                        text: "In RAM"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
                
                Item { width: parent.width - 200; height: 1 } // Spacer
                
                Button {
                    text: "Refresh"
                    width: 80
                    height: 30
                    
                    background: Rectangle {
                        color: parent.pressed ? "#0056b3" : (parent.hovered ? "#007bff" : "#007bff")
                        radius: 4
                    }
                    
                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    onClicked: {
                        requestDataInfo(dataName)
                    }
                }
            }
            
            // Data Table
            Rectangle {
                width: parent.width
                height: parent.height - 80
                color: "white"
                border.color: "#dee2e6"
                border.width: 1
                radius: 4
                
                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 1
                    clip: true
                    
                    TableView {
                        id: dataTable
                        anchors.fill: parent
                        
                        property var tableHeaders: ["Index", "Type", "Size", "Channels", "Trials", "Time Points", "Sample Rate"]
                        
                        model: dataInfo.length
                        
                        delegate: Rectangle {
                            implicitWidth: 120
                            implicitHeight: 35
                            border.color: "#e9ecef"
                            border.width: 1
                            color: row % 2 === 0 ? "#f8f9fa" : "white"
                            
                            property int row: model.index
                            property int col: column
                            
                            Text {
                                anchors.centerIn: parent
                                text: {
                                    if (row === -1) {
                                        // Header row
                                        return dataTable.tableHeaders[col] || ""
                                    } else if (row < dataInfo.length) {
                                        // Data rows
                                        var item = dataInfo[row]
                                        switch(col) {
                                            case 0: return "data{" + (row + 1) + "}"
                                            case 1: return item.type || "FieldTrip Data"
                                            case 2: return item.size || "N/A"
                                            case 3: return item.channels || "N/A"
                                            case 4: return item.trials || "N/A"
                                            case 5: return item.timePoints || "N/A"
                                            case 6: return item.sampleRate || "N/A"
                                            default: return ""
                                        }
                                    }
                                    return ""
                                }
                                font.pixelSize: 11
                                color: row === -1 ? "#495057" : "#333"
                                font.bold: row === -1
                                wrapMode: Text.Wrap
                            }
                        }
                        
                        // Header
                        Rectangle {
                            z: 2
                            x: dataTable.contentX
                            y: dataTable.contentY
                            width: dataTable.width
                            height: 35
                            color: "#6c757d"
                            
                            Row {
                                anchors.fill: parent
                                
                                Repeater {
                                    model: dataTable.tableHeaders
                                    
                                    Rectangle {
                                        width: 120
                                        height: 35
                                        border.color: "#495057"
                                        border.width: 1
                                        color: "#6c757d"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: modelData
                                            color: "white"
                                            font.pixelSize: 11
                                            font.bold: true
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Empty state
                Column {
                    anchors.centerIn: parent
                    spacing: 10
                    visible: dataInfo.length === 0
                    
                    Text {
                        text: "🔍"
                        font.pixelSize: 48
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                    
                    Text {
                        text: "No data information available"
                        font.pixelSize: 14
                        color: "#6c757d"
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                    
                    Text {
                        text: "Click Refresh to load data details"
                        font.pixelSize: 12
                        color: "#adb5bd"
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }
            }
        }
    }
}
