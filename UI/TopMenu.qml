import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: topMenuComponent
    width: parent.width
    height: 30
    color: "#f8f9fa"
    
    // Properties for menu states
    property bool fileMenuOpen: false
    property bool matlabSubmenuOpen: false
    property bool editMenuOpen: false
    property bool editModeChecked: false
    
    // Signals for communication with parent
    signal fieldtripDialogRequested()
    signal folderDialogRequested()
    signal createFunctionRequested()
    signal createScriptRequested()
    signal editModeToggled(bool checked)
    signal menuStateChanged(bool fileMenuOpen, bool matlabSubmenuOpen, bool editMenuOpen)
    
    // Function to close menus (can be called from parent)
    function closeMenus() {
        fileMenuOpen = false
        matlabSubmenuOpen = false
        editMenuOpen = false
        menuStateChanged(fileMenuOpen, matlabSubmenuOpen, editMenuOpen)
    }
    
    // Function to emit menu state changes
    function updateMenuState() {
        menuStateChanged(fileMenuOpen, matlabSubmenuOpen, editMenuOpen)
    }
    
    // Bottom border
    Rectangle {
        width: parent.width
        height: 1
        color: "#dee2e6"
        anchors.bottom: parent.bottom
    }

    Row {
        anchors.left: parent.left
        anchors.leftMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        spacing: 20

        // File Menu
        Rectangle {
            width: fileMenuText.width + 20
            height: 25
            color: fileMenuArea.containsMouse || topMenuComponent.fileMenuOpen ? "#d1d3d4" : "transparent"
            radius: 3

            Text {
                id: fileMenuText
                text: "File"
                anchors.centerIn: parent
                font.pixelSize: 12
                color: "#333"
            }

            MouseArea {
                id: fileMenuArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    console.log("File menu clicked, current state:", topMenuComponent.fileMenuOpen)
                    topMenuComponent.fileMenuOpen = !topMenuComponent.fileMenuOpen
                    if (topMenuComponent.fileMenuOpen) {
                        topMenuComponent.matlabSubmenuOpen = false
                        topMenuComponent.editMenuOpen = false
                    }
                    console.log("File menu new state:", topMenuComponent.fileMenuOpen)
                    topMenuComponent.menuStateChanged(topMenuComponent.fileMenuOpen, topMenuComponent.matlabSubmenuOpen, topMenuComponent.editMenuOpen)
                }
            }
        }

        // Edit Menu
        Rectangle {
            width: editMenuText.width + 20
            height: 25
            color: editMenuArea.containsMouse || topMenuComponent.editMenuOpen ? "#d1d3d4" : "transparent"
            radius: 3

            Text {
                id: editMenuText
                text: "Edit"
                anchors.centerIn: parent
                font.pixelSize: 12
                color: "#333"
            }

            MouseArea {
                id: editMenuArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    console.log("Edit menu clicked, current state:", topMenuComponent.editMenuOpen)
                    topMenuComponent.editMenuOpen = !topMenuComponent.editMenuOpen
                    if (topMenuComponent.editMenuOpen) {
                        topMenuComponent.fileMenuOpen = false
                        topMenuComponent.matlabSubmenuOpen = false
                    }
                    console.log("Edit menu new state:", topMenuComponent.editMenuOpen)
                    topMenuComponent.menuStateChanged(topMenuComponent.fileMenuOpen, topMenuComponent.matlabSubmenuOpen, topMenuComponent.editMenuOpen)
                }
            }

            // Edit Menu Dropdown
            Rectangle {
                id: editMenuDropdown
                x: 0
                y: parent.height + 2
                width: 180
                height: 50
                color: "white"
                border.color: "#d0d0d0"
                border.width: 1
                radius: 6
                visible: topMenuComponent.editMenuOpen
                z: 10000

                // Simple shadow effect
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -2
                    color: "transparent"
                    border.color: "#00000015"
                    border.width: 2
                    radius: 7
                    z: -1
                }

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -4
                    color: "transparent"
                    border.color: "#00000010"
                    border.width: 2
                    radius: 8
                    z: -2
                }

                // Edit Mode Checkbox Item
                Rectangle {
                    width: parent.width
                    height: 40
                    color: editModeArea.containsMouse ? "#e8e8e8" : "transparent"
                    radius: 4

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 8

                        // Checkbox
                        Rectangle {
                            width: 16
                            height: 16
                            anchors.verticalCenter: parent.verticalCenter
                            color: topMenuComponent.editModeChecked ? "#2196f3" : "white"
                            border.color: "#666"
                            border.width: 1
                            radius: 2

                            Text {
                                text: topMenuComponent.editModeChecked ? "✓" : ""
                                anchors.centerIn: parent
                                font.pixelSize: 10
                                color: "white"
                                font.bold: true
                            }
                        }

                        Text {
                            text: "Edit Mode"
                            anchors.verticalCenter: parent.verticalCenter
                            font.pixelSize: 13
                            color: editModeArea.containsMouse ? "#1a1a1a" : "#333"
                            font.weight: editModeArea.containsMouse ? Font.Medium : Font.Normal
                        }
                    }

                    MouseArea {
                        id: editModeArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            topMenuComponent.editModeChecked = !topMenuComponent.editModeChecked
                            console.log("Edit mode toggled:", topMenuComponent.editModeChecked)
                            topMenuComponent.editModeToggled(topMenuComponent.editModeChecked)
                            topMenuComponent.editMenuOpen = false
                            topMenuComponent.menuStateChanged(topMenuComponent.fileMenuOpen, topMenuComponent.matlabSubmenuOpen, topMenuComponent.editMenuOpen)
                        }
                    }
                }
            }
        }

        // View Menu
        Rectangle {
            width: viewMenuText.width + 20
            height: 25
            color: viewMenuArea.containsMouse ? "#d1d3d4" : "transparent"
            radius: 3

            Text {
                id: viewMenuText
                text: "View"
                anchors.centerIn: parent
                font.pixelSize: 12
                color: "#333"
            }

            MouseArea {
                id: viewMenuArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    console.log("View menu clicked")
                    // TODO: Implement view menu dropdown
                }
            }
        }

        // Tools Menu
        Rectangle {
            width: toolsMenuText.width + 20
            height: 25
            color: toolsMenuArea.containsMouse ? "#d1d3d4" : "transparent"
            radius: 3

            Text {
                id: toolsMenuText
                text: "Tools"
                anchors.centerIn: parent
                font.pixelSize: 12
                color: "#333"
            }

            MouseArea {
                id: toolsMenuArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    console.log("Tools menu clicked")
                    // TODO: Implement tools menu dropdown
                }
            }
        }

        // Help Menu
        Rectangle {
            width: helpMenuText.width + 20
            height: 25
            color: helpMenuArea.containsMouse ? "#d1d3d4" : "transparent"
            radius: 3

            Text {
                id: helpMenuText
                text: "Help"
                anchors.centerIn: parent
                font.pixelSize: 12
                color: "#333"
            }

            MouseArea {
                id: helpMenuArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    console.log("Help menu clicked")
                    // TODO: Implement help menu dropdown
                }
            }
        }
    }




}