import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: dropdownTemplate
    width: parent ? parent.width : 200
    height: 60
    z: 1000  // Base z-index

    // Properties for customization
    property string label: "Dropdown Label"
    property string matlabProperty: "cfg.property"
    property var model: ["Option 1", "Option 2", "Option 3"]
    property int currentIndex: 0
    property bool hasAddFeature: false
    property bool isMultiSelect: false
    property int maxSelections: -1  // -1 = unlimited, 1 = single select in multi-style
    property string addPlaceholder: "Enter custom..."
    property var selectedItems: [] // For multi-select
    property var allItems: [] // For multi-select

    // Dynamic z-index management
    property int baseZ: 1000
    property int activeZ: 2000

    onActiveFocusChanged: {
        z = activeFocus ? activeZ : baseZ
    }

    // Exposed properties
    property string currentText: isMultiSelect ? getMultiSelectFormattedText() : (model[currentIndex] || "")

    // Signals
    signal selectionChanged(string value, int index)
    signal addItem(string newItem)
    signal multiSelectionChanged(var selected)

    // Function to get display text for multi-select
    function getMultiSelectText() {
        if (selectedItems.length === 0) {
            return "None"
        } else if (selectedItems.length === allItems.length) {
            return "All"
        } else {
            return selectedItems.length + " selected"
        }
    }

    // Function to get formatted text for multi-select
    function getMultiSelectFormattedText() {
        if (selectedItems.length === 0) {
            return ""
        } else {
            return selectedItems.join(", ")
        }
    }

    Column {
        width: parent.width
        spacing: 5

        Text {
            text: matlabProperty + " = '" + (isMultiSelect ? "{" + getMultiSelectFormattedText() + "}" : (comboBox.currentText || "none")) + "'"
            font.pixelSize: 12
            color: "#666"
            wrapMode: Text.Wrap
            width: parent.width
        }

        // Single-select interface
        Row {
            width: parent.width
            spacing: 8
            visible: !isMultiSelect

            // Custom display rectangle (consistent with multi-select)
            Rectangle {
                width: hasAddFeature ? parent.width * 0.4 : parent.width
                height: 30
                color: "#f5f5f5"
                border.color: "#ccc"
                border.width: 1
                radius: 3

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    text: comboBox.currentText || "Select option..."
                    font.pixelSize: 12
                    color: "#333"
                }

                Text {
                    anchors.right: parent.right
                    anchors.rightMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    text: "▼"
                    font.pixelSize: 10
                    color: "#666"
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        comboBox.popup.open()
                    }
                }
            }

            ComboBox {
                id: comboBox
                visible: false  // Hidden ComboBox for functionality
                width: hasAddFeature ? parent.width * 0.4 : parent.width
                height: 30
                model: dropdownTemplate.model
                currentIndex: dropdownTemplate.currentIndex

                onCurrentTextChanged: {
                    if (currentText) {
                        selectionChanged(currentText, currentIndex)
                    }
                }

                popup.onOpened: {
                    dropdownTemplate.z = dropdownTemplate.activeZ
                }

                popup.onClosed: {
                    dropdownTemplate.z = dropdownTemplate.baseZ
                }
            }

            // Add custom item section
            Rectangle {
                visible: hasAddFeature
                width: parent.width * 0.35
                height: 30
                color: "#f8f9fa"
                border.color: "#dee2e6"
                border.width: 1
                radius: 3

                TextInput {
                    id: customInput
                    anchors.fill: parent
                    anchors.margins: 8
                    font.pixelSize: 11
                    color: "#333"
                    verticalAlignment: TextInput.AlignVCenter

                    Text {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        text: addPlaceholder
                        font.pixelSize: 11
                        color: "#999"
                        visible: customInput.text === "" && !customInput.activeFocus
                    }
                }
            }

            Button {
                visible: hasAddFeature
                width: parent.width * 0.2
                height: 30
                text: "+ Add"

                background: Rectangle {
                    color: parent.pressed ? "#28a745" : (parent.hovered ? "#34ce57" : "#28a745")
                    radius: 3
                    border.color: "#1e7e34"
                    border.width: 1
                }

                contentItem: Text {
                    text: parent.text
                    color: "white"
                    font.pixelSize: 10
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: {
                    var newItem = customInput.text.trim()
                    if (newItem !== "" && model.indexOf(newItem) === -1) {
                        var newModel = model.slice()
                        newModel.push(newItem)
                        model = newModel
                        comboBox.currentIndex = newModel.length - 1
                        customInput.text = ""
                        addItem(newItem)
                    }
                }
            }
        }

        // Multi-select interface
        Rectangle {
            visible: isMultiSelect
            width: parent.width
            height: 30
            color: "#f5f5f5"
            border.color: "#ccc"
            border.width: 1
            radius: 3

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                text: getMultiSelectText()
                font.pixelSize: 12
                color: "#333"
            }

            Text {
                anchors.right: parent.right
                anchors.rightMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                text: "▼"
                font.pixelSize: 10
                color: "#666"
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    multiSelectPopup.visible = !multiSelectPopup.visible
                }
            }
        }

        // Multi-select popup
        Rectangle {
            id: multiSelectPopup
            visible: false
            width: parent.width
            height: 200
            color: "white"
            border.color: "#ccc"
            border.width: 1
            radius: 3
            z: 1000

            onVisibleChanged: {
                dropdownTemplate.z = visible ? dropdownTemplate.activeZ : dropdownTemplate.baseZ
            }

            ScrollView {
                anchors.fill: parent
                anchors.margins: 5

                Column {
                    width: parent.width
                    spacing: 2

                    // Include All option (only for multi-select with unlimited selections)
                    Rectangle {
                        width: parent.width
                        height: maxSelections === 1 ? 0 : 25
                        visible: maxSelections !== 1
                        color: selectedItems.length === allItems.length ? "#e3f2fd" : "transparent"

                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 5
                            spacing: 5

                            Rectangle {
                                width: 15
                                height: 15
                                anchors.verticalCenter: parent.verticalCenter
                                border.color: "#666"
                                border.width: 1
                                color: selectedItems.length === allItems.length ? "#2196f3" : "white"

                                Text {
                                    anchors.centerIn: parent
                                    text: "✓"
                                    color: "white"
                                    font.pixelSize: 10
                                    visible: selectedItems.length === allItems.length
                                }
                            }

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: "Include All"
                                font.pixelSize: 12
                                font.bold: true
                                color: "#333"
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            enabled: maxSelections !== 1
                            onClicked: {
                                if (maxSelections !== 1) {
                                    if (selectedItems.length === allItems.length) {
                                        selectedItems = []
                                    } else {
                                        selectedItems = allItems.slice()
                                    }
                                    multiSelectionChanged(selectedItems)
                                }
                            }
                        }
                    }

                    // Individual options
                    Repeater {
                        model: allItems

                        Rectangle {
                            width: parent.width
                            height: 25
                            color: selectedItems.indexOf(modelData) !== -1 ? "#e3f2fd" : "transparent"

                            Row {
                                anchors.fill: parent
                                anchors.leftMargin: 5
                                spacing: 5

                                Rectangle {
                                    width: 15
                                    height: 15
                                    anchors.verticalCenter: parent.verticalCenter
                                    border.color: "#666"
                                    border.width: 1
                                    color: selectedItems.indexOf(modelData) !== -1 ? "#2196f3" : "white"

                                    Text {
                                        anchors.centerIn: parent
                                        text: "✓"
                                        color: "white"
                                        font.pixelSize: 10
                                        visible: selectedItems.indexOf(modelData) !== -1
                                    }
                                }

                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: modelData
                                    font.pixelSize: 12
                                    color: "#333"
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    var index = selectedItems.indexOf(modelData)
                                    var newSelection = selectedItems.slice()

                                    if (index !== -1) {
                                        // If already selected and maxSelections allows, remove it
                                        if (maxSelections !== 1) {
                                            newSelection.splice(index, 1)
                                        }
                                    } else {
                                        // If not selected, add it
                                        if (maxSelections === 1) {
                                            // Single select mode - replace selection
                                            newSelection = [modelData]
                                        } else {
                                            // Multi select mode - add to selection
                                            newSelection.push(modelData)
                                        }
                                    }

                                    selectedItems = newSelection
                                    multiSelectionChanged(selectedItems)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}