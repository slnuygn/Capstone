import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Dialogs
import "."

Item {
    id: preprocessingPageRoot
    anchors.fill: parent
    anchors.margins: 10  // Reduced margins for better space usage
    
    // Properties to communicate with main.qml
    property string currentFolder: ""
    property var folderContents: []
    property string fieldtripPath: ""
    property string saveMessage: ""
    property bool isProcessing: false  // Track processing state
    property bool showICABrowser: false  // Track ICA browser visibility
    
    // Function to initialize eventvalues from main.qml
    function setInitialEventvalues(eventvalues) {
        if (eventvalues && eventvalues.length > 0) {
            eventvaluePopup.selectedEventvalues = eventvalues
        }
    }
    
    // Function to initialize channels from main.qml
    function setInitialChannels(channels) {
        if (channels && channels.length > 0) {
            channelPopup.selectedChannels = channels
        }
    }
    
    // Function to initialize demean settings from main.qml
    function setInitialDemean(demeanEnabled, baselineWindow) {
        demeanCheckBox.checked = demeanEnabled
        if (baselineWindow && baselineWindow.length >= 2) {
            baselineSlider.first.value = baselineWindow[0]
            baselineSlider.second.value = baselineWindow[1]
        }
    }
    
    // Function to initialize DFT filter settings from main.qml
    function setInitialDftfilter(dftfilterEnabled, dftfreq) {
        dftfilterCheckBox.checked = dftfilterEnabled
        if (dftfreq && dftfreq.length >= 2) {
            dftfreqSlider.first.value = dftfreq[0]
            dftfreqSlider.second.value = dftfreq[1]
        }
    }
    

    
    // Signals to communicate with main.qml
    signal openFolderDialog()
    signal openFieldtripDialog()
    signal requestSaveConfiguration(real prestimValue, real poststimValue, string trialfunValue, string eventtypeValue, var selectedChannels, var selectedEventvalues, bool demeanEnabled, real baselineStart, real baselineEnd, bool dftfilterEnabled, real dftfreqStart, real dftfreqEnd)
    signal refreshFileExplorer()
    
    // Connection to handle processing completion
    Connections {
        target: matlabExecutor
        function onProcessingFinished() {
            preprocessingPageRoot.isProcessing = false
        }
    }
    
    // JavaScript functions for channel selection
    function isChannelSelected(channel) {
        return channelPopup.selectedChannels.indexOf(channel) !== -1
    }

    function isAllSelected() {
        return channelPopup.selectedChannels.length === channelPopup.allChannels.length
    }

    function toggleChannel(channel) {
        var index = channelPopup.selectedChannels.indexOf(channel)
        var newSelection = channelPopup.selectedChannels.slice() // Create a copy
        
        if (index !== -1) {
            // Remove channel
            newSelection.splice(index, 1)
        } else {
            // Add channel
            newSelection.push(channel)
        }
        
        channelPopup.selectedChannels = newSelection
    }

    function getSelectedChannelsText() {
        if (channelPopup.selectedChannels.length === 0) {
            return "None"
        } else if (channelPopup.selectedChannels.length === channelPopup.allChannels.length) {
            return "All"
        } else {
            return channelPopup.selectedChannels.join(", ")
        }
    }

    function getSelectedChannelsCount() {
        return channelPopup.selectedChannels.length
    }

    // JavaScript functions for eventvalue selection
    function isEventvalueSelected(eventvalue) {
        return eventvaluePopup.selectedEventvalues.indexOf(eventvalue) !== -1
    }

    function toggleEventvalue(eventvalue) {
        var index = eventvaluePopup.selectedEventvalues.indexOf(eventvalue)
        var newSelection = eventvaluePopup.selectedEventvalues.slice() // Create a copy
        
        if (index !== -1) {
            // Remove eventvalue
            newSelection.splice(index, 1)
        } else {
            // Add eventvalue
            newSelection.push(eventvalue)
        }
        
        eventvaluePopup.selectedEventvalues = newSelection
    }

    function getSelectedEventvaluesText() {
        if (eventvaluePopup.selectedEventvalues.length === 0) {
            return ""
        } else {
            return "'" + eventvaluePopup.selectedEventvalues.join("' '") + "'"
        }
    }

    function getSelectedEventvaluesCount() {
        return eventvaluePopup.selectedEventvalues.length
    }

    // Background area to close dropdown when clicking outside (removed MouseArea to fix scrolling)

    // File Explorer Rectangle - Direct implementation
    Rectangle {
        id: fileExplorerRect
        anchors.left: parent.left
        anchors.top: parent.top
        width: parent.width * 0.2  // Slightly wider
        height: parent.height  // Use full height!
        color: "#f8f9fa"
        border.color: "#dee2e6"
        border.width: 2
        radius: 5

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5

            // Folder icon and current folder display in same row
            Row {
                width: parent.width
                height: 30
                spacing: 10

                // Current Folder Display
                Text {
                    text: preprocessingPageRoot.currentFolder ? "Folder: " + preprocessingPageRoot.currentFolder : "No folder selected"
                    font.pixelSize: 12
                    color: "#666"
                    width: parent.width - 70 // Account for both buttons width and spacing
                    wrapMode: Text.Wrap
                    anchors.verticalCenter: parent.verticalCenter
                }

                // Spacer to push buttons to the right
                Item {
                    width: parent.width - (parent.children[0].width + 70) // Account for both buttons
                    height: 1
                }

                // Button group with tighter spacing
                Row {
                    spacing: 2 // Very tight spacing between buttons
                    
                    // Refresh Button
                    Button {
                        width: 30
                        height: 30
                        
                        background: Rectangle {
                            color: parent.pressed ? "#dee2e6" : (parent.hovered ? "#f1f3f4" : "transparent")
                            radius: 4
                        }
                        
                        contentItem: Text {
                            text: "🔄"
                            font.pixelSize: 16
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }

                        onClicked: {
                            preprocessingPageRoot.refreshFileExplorer()
                        }
                    }

                    // Folder Icon Button (positioned at the right)
                    Button {
                        width: 30
                        height: 30
                        
                        background: Rectangle {
                            color: parent.pressed ? "#dee2e6" : (parent.hovered ? "#f1f3f4" : "transparent")
                            radius: 4
                        }
                        
                        contentItem: Text {
                            text: "📁"
                            font.pixelSize: 16
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }

                        onClicked: {
                            preprocessingPageRoot.openFolderDialog()
                        }
                    }
                }
            }

            // Drive Files (full height)
            Column {
                width: parent.width
                height: parent.height - 30  // Full height minus header row

                Text {
                    text: "File Explorer"
                    font.bold: true
                    color: "#495057"
                    font.pixelSize: 12
                }

                Rectangle {
                    width: parent.width
                    height: parent.height - 20  // Minus text height
                    color: "white"
                    border.color: "#ccc"
                    border.width: 1
                    radius: 3

                    ScrollView {
                        anchors.fill: parent
                        anchors.margins: 5
                        clip: true

                        ListView {
                            id: folderListView
                            anchors.fill: parent
                            model: preprocessingPageRoot.folderContents
                            
                            delegate: Item {
                                width: folderListView.width
                                height: 25

                                Rectangle {
                                    anchors.fill: parent
                                    color: fileMouseArea.containsMouse ? "#e3f2fd" : "transparent"
                                    radius: 3
                                    
                                    MouseArea {
                                        id: fileMouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                                        
                                        onClicked: function(mouse) {
                                            if (mouse.button === Qt.LeftButton) {
                                                // Left-click: original behavior (disabled as requested)
                                                // User wanted to cancel the automatic script execution on click
                                                console.log("File clicked (automatic execution disabled):", modelData)
                                            }
                                        }
                                    }
                                    
                                    Row {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 5
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 5
                                        
                                        Text {
                                            text: modelData
                                            font.pixelSize: 10
                                            color: modelData.endsWith('.mat') ? 
                                                (modelData.includes('ICA') || modelData.includes('ica') ? "#4caf50" : "#007bff") : "#333"
                                            font.underline: modelData.endsWith('.mat') && fileMouseArea.containsMouse
                                        }
                                        
                                        Text {
                                            text: modelData.endsWith('.mat') ? 
                                                (modelData.includes('ICA') || modelData.includes('ica') ? "🧠" : "📊") : ""
                                            font.pixelSize: 8
                                            visible: modelData.endsWith('.mat') && fileMouseArea.containsMouse
                                        }
                                    }
                                }

                                Rectangle {
                                    anchors.bottom: parent.bottom
                                    width: parent.width
                                    height: 1
                                    color: "#eee"
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Right side - Configuration Area with Scrolling (maximized space usage)
    Rectangle {
        anchors.left: fileExplorerRect.right
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 10  // Reduced from 20
        anchors.topMargin: 10   // Reduced from 20
        anchors.rightMargin: 5  // Reduced from 20 to push scrollbar right
        anchors.bottomMargin: 10 // Aligned with file browser bottom edge
        color: "transparent"
        
        Column {
            width: parent.width
            spacing: 10
            
            // Header text
            Text {
                text: "The .set files in this directory will be preprocessed."
                font.pixelSize: 14
                color: "#333"
            }
            
            // Scrollable content area
            ScrollView {
                width: parent.width  
                height: 660  // Adjusted to align with file browser bottom edge
                clip: true
                
                Column {
                    id: mainColumn
                    spacing: 20
                    width: parent.width
                    
                    Component.onCompleted: {
                        console.log("Fixed ScrollView - Column height:", height)
                        console.log("Fixed ScrollView - Available width:", width)
                    }

            // FieldTrip Path Selection
            Column {
                width: parent.width
                spacing: 5

                Text {
                    text: "addpath('" + preprocessingPageRoot.fieldtripPath + "')"
                    font.pixelSize: 12
                    color: "#666"
                }

                Row {
                width: parent.width
                spacing: 10

                // Current FieldTrip Path Display
                Rectangle {
                    width: 300
                    height: 30
                    color: "#f8f9fa"
                    border.color: "#dee2e6"
                    border.width: 1
                    radius: 3

                    Text {
                        id: fieldtripPathText
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        text: preprocessingPageRoot.fieldtripPath || "C:\\FIELDTRIP"
                        font.pixelSize: 11
                        color: "#666"
                        elide: Text.ElideLeft
                    }
                }

                // Folder Icon Button
                Button {
                    width: 30
                    height: 30
                    
                    background: Rectangle {
                        color: parent.pressed ? "#dee2e6" : (parent.hovered ? "#f1f3f4" : "transparent")
                        radius: 4
                    }
                    
                    contentItem: Text {
                        text: "📁"
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: {
                        preprocessingPageRoot.openFieldtripDialog()
                    }
                }
            }
        }

        // Trialfun dropdown
        Column {
            width: parent.width
            spacing: 5

            Text {
                text: "cfg.trialfun = '" + trialfunComboBox.currentText + "'"
                font.pixelSize: 12
                color: "#666"
            }

            Row {
                spacing: 10
                
                ComboBox {
                    id: trialfunComboBox
                    width: 200
                    height: 30

                    property var customModel: ["ft_trialfun_general", "alternative", "test1", "test2", "ddd"]
                    model: customModel
                    currentIndex: 0
                    
                    // Save selection when it changes
                    onCurrentTextChanged: {
                        if (currentText) {
                            matlabExecutor.saveTrialfunSelection(currentText, currentIndex)
                        }
                    }
                    
                    background: Rectangle {
                        color: "#f5f5f5"
                        border.color: "#ccc"
                        border.width: 1
                        radius: 3
                    }
                    
                    contentItem: Text {
                        text: trialfunComboBox.displayText
                        font.pixelSize: 12
                        color: "#333"
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                    }
                }
                
                // Add custom trialfun section
                Rectangle {
                    width: 120
                    height: 30
                    color: "#f8f9fa"
                    border.color: "#dee2e6"
                    border.width: 1
                    radius: 3
                    
                    TextInput {
                        id: customTrialfunInput
                        anchors.fill: parent
                        anchors.margins: 8
                        font.pixelSize: 11
                        color: "#333"
                        verticalAlignment: TextInput.AlignVCenter
                        
                        Text {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            text: "Enter custom..."
                            font.pixelSize: 11
                            color: "#999"
                            visible: customTrialfunInput.text === "" && !customTrialfunInput.activeFocus
                        }
                    }
                }
                
                Button {
                    width: 60
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
                        var newTrialfun = customTrialfunInput.text.trim()
                        if (newTrialfun !== "" && trialfunComboBox.customModel.indexOf(newTrialfun) === -1) {
                            var newModel = trialfunComboBox.customModel.slice() // Create copy
                            newModel.push(newTrialfun)
                            trialfunComboBox.customModel = newModel
                            trialfunComboBox.model = newModel
                            trialfunComboBox.currentIndex = newModel.length - 1 // Select the newly added item
                            customTrialfunInput.text = "" // Clear input
                            
                            // Save to QML file for persistence across restarts
                            matlabExecutor.addCustomTrialfunOption(newTrialfun)
                        }
                    }
                }
            }
        }

        // Eventtype dropdown
        Column {
            width: parent.width
            spacing: 5

            Text {
                text: "cfg.trialdef.eventtype = '" + eventtypeComboBox.currentText + "'"
                font.pixelSize: 12
                color: "#666"
            }

            Row {
                spacing: 10
                
                ComboBox {
                    id: eventtypeComboBox
                    width: 200
                    height: 30
                    
                    property var eventtypeCustomModel: ["Stimulus", "alternative", "alt2", "alt3"]
                    model: eventtypeCustomModel
                    currentIndex: 0
                    
                    // Save selection when it changes
                    onCurrentTextChanged: {
                        if (currentText) {
                            matlabExecutor.saveEventtypeSelection(currentText, currentIndex)
                        }
                    }
                    
                    background: Rectangle {
                        color: "#f5f5f5"
                        border.color: "#ccc"
                        border.width: 1
                        radius: 3
                    }
                    
                    contentItem: Text {
                        text: eventtypeComboBox.displayText
                        font.pixelSize: 12
                        color: "#333"
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                    }
                }
                
                // Add custom eventtype section
                Rectangle {
                    width: 120
                    height: 30
                    color: "#f8f9fa"
                    border.color: "#dee2e6"
                    border.width: 1
                    radius: 3
                    
                    TextInput {
                        id: customEventtypeInput
                        anchors.fill: parent
                        anchors.margins: 8
                        font.pixelSize: 11
                        color: "#333"
                        verticalAlignment: TextInput.AlignVCenter
                        
                        Text {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            text: "Enter custom..."
                            font.pixelSize: 11
                            color: "#999"
                            visible: customEventtypeInput.text === "" && !customEventtypeInput.activeFocus
                        }
                    }
                }
                
                Button {
                    width: 60
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
                        var newEventtype = customEventtypeInput.text.trim()
                        if (newEventtype !== "" && eventtypeComboBox.eventtypeCustomModel.indexOf(newEventtype) === -1) {
                            var newModel = eventtypeComboBox.eventtypeCustomModel.slice() // Create copy
                            newModel.push(newEventtype)
                            eventtypeComboBox.eventtypeCustomModel = newModel
                            eventtypeComboBox.model = newModel
                            eventtypeComboBox.currentIndex = newModel.length - 1 // Select the newly added item
                            customEventtypeInput.text = "" // Clear input
                            
                            // Save to QML file for persistence across restarts
                            matlabExecutor.addCustomEventtypeOption(newEventtype)
                        }
                    }
                }
            }
        }

        // Eventvalue multi-select dropdown
        Column {
            width: parent.width
            spacing: 5

            Text {
                text: "cfg.trialdef.eventvalue = {" + getSelectedEventvaluesText() + "}"
                font.pixelSize: 12
                color: "#666"
                wrapMode: Text.Wrap
                width: parent.width
            }

            Rectangle {
                width: 200
                height: 30
                color: "#f5f5f5"
                border.color: "#ccc"
                border.width: 1
                radius: 3

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    text: getSelectedEventvaluesCount() + " eventvalue(s) selected"
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
                        eventvaluePopup.visible = !eventvaluePopup.visible
                    }
                }
            }

            // Popup for eventvalue selection
            Rectangle {
                id: eventvaluePopup
                width: 200
                height: 120
                color: "white"
                border.color: "#ccc"
                border.width: 1
                radius: 3
                visible: false
                z: 1000

                property var allEventvalues: ["S200", "S201", "S202"]
                property var selectedEventvalues: ["S200", "S201", "S202"]

                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 5

                    Column {
                        width: parent.width
                        spacing: 2

                        // Individual eventvalue options
                        Repeater {
                            model: eventvaluePopup.allEventvalues

                            Rectangle {
                                width: parent.width
                                height: 25
                                color: isEventvalueSelected(modelData) ? "#e3f2fd" : "transparent"

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
                                        color: isEventvalueSelected(modelData) ? "#2196f3" : "white"

                                        Text {
                                            anchors.centerIn: parent
                                            text: "✓"
                                            color: "white"
                                            font.pixelSize: 10
                                            visible: isEventvalueSelected(modelData)
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
                                        toggleEventvalue(modelData)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Channel Selection
        Column {
            width: parent.width
            spacing: 5

            Text {
                text: "Choose Channels: " + getSelectedChannelsText()
                font.pixelSize: 12
                color: "#666"
                wrapMode: Text.Wrap
                width: parent.width
            }

            Rectangle {
                width: 200
                height: 30
                color: "#f5f5f5"
                border.color: "#ccc"
                border.width: 1
                radius: 3

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    text: getSelectedChannelsCount() + " channel(s) selected"
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
                        channelPopup.visible = !channelPopup.visible
                    }
                }
            }

            // Popup for channel selection
            Rectangle {
                id: channelPopup
                width: 250
                height: 300
                color: "white"
                border.color: "#ccc"
                border.width: 1
                radius: 3
                visible: false
                z: 1000

                property var allChannels: ["Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "C3", "Cz", "C4", "P3", "Pz", "P4", "T3", "T4", "T5", "T6", "O1", "O2", "Oz"]
                property var selectedChannels: ["F4", "Fz", "C3", "Pz", "P3", "O1", "Oz", "O2", "P4", "Cz", "C4"]

                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 5

                    Column {
                        width: parent.width
                        spacing: 2

                        // Include All option
                        Rectangle {
                            width: parent.width
                            height: 25
                            color: isAllSelected() ? "#e3f2fd" : "transparent"

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
                                    color: isAllSelected() ? "#2196f3" : "white"

                                    Text {
                                        anchors.centerIn: parent
                                        text: "✓"
                                        color: "white"
                                        font.pixelSize: 10
                                        visible: isAllSelected()
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
                                onClicked: {
                                    if (isAllSelected()) {
                                        channelPopup.selectedChannels = []
                                    } else {
                                        channelPopup.selectedChannels = channelPopup.allChannels.slice()
                                    }
                                }
                            }
                        }

                        // Individual channel options
                        Repeater {
                            model: channelPopup.allChannels

                            Rectangle {
                                width: parent.width
                                height: 25
                                color: isChannelSelected(modelData) ? "#e3f2fd" : "transparent"

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
                                        color: isChannelSelected(modelData) ? "#2196f3" : "white"

                                        Text {
                                            anchors.centerIn: parent
                                            text: "✓"
                                            color: "white"
                                            font.pixelSize: 10
                                            visible: isChannelSelected(modelData)
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
                                        toggleChannel(modelData)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Double Range Slider for prestim and poststim
        Column {
            width: parent.width
            spacing: 10

            Text {
                text: "cfg.trialdef.prestim = " + rangeSlider.first.value.toFixed(1) + " | cfg.trialdef.poststim = " + rangeSlider.second.value.toFixed(1)
                font.pixelSize: 12
                color: "#666"
            }

            RangeSlider {
                id: rangeSlider
                width: 150  // Much shorter bar
                from: 0.0   // Start from 0
                to: 1.0     // End at 1
                first.value: 0.5   // prestim default
                second.value: 1.0  // poststim default
                stepSize: 0.1

                background: Rectangle {
                    x: rangeSlider.leftPadding
                    y: rangeSlider.topPadding + rangeSlider.availableHeight / 2 - height / 2
                    implicitWidth: 200
                    implicitHeight: 6
                    width: rangeSlider.availableWidth
                    height: implicitHeight
                    radius: 3
                    color: "#e0e0e0"

                    // Active range
                    Rectangle {
                        x: rangeSlider.first.visualPosition * parent.width
                        width: (rangeSlider.second.visualPosition - rangeSlider.first.visualPosition) * parent.width
                        height: parent.height
                        color: "#2196f3"
                        radius: 3
                    }
                }

                first.handle: Rectangle {
                    x: rangeSlider.leftPadding + rangeSlider.first.visualPosition * (rangeSlider.availableWidth - width)
                    y: rangeSlider.topPadding + rangeSlider.availableHeight / 2 - height / 2
                    implicitWidth: 20
                    implicitHeight: 20
                    radius: 10
                    color: rangeSlider.first.pressed ? "#1976d2" : "#2196f3"
                    border.color: "#1976d2"
                    border.width: 2
                }

                second.handle: Rectangle {
                    x: rangeSlider.leftPadding + rangeSlider.second.visualPosition * (rangeSlider.availableWidth - width)
                    y: rangeSlider.topPadding + rangeSlider.availableHeight / 2 - height / 2
                    implicitWidth: 20
                    implicitHeight: 20
                    radius: 10
                    color: rangeSlider.second.pressed ? "#1976d2" : "#2196f3"
                    border.color: "#1976d2"
                    border.width: 2
                }
            }
        }

        // Demean configuration section
        Rectangle {
            width: parent.width
            height: demeanColumn.height + 20
            color: "#f8f9fa"
            border.color: "#e9ecef"
            border.width: 1
            radius: 4
            
            Column {
                id: demeanColumn
                width: parent.width - 20
                anchors.left: parent.left
                anchors.leftMargin: 10
                anchors.top: parent.top
                anchors.topMargin: 10
                spacing: 10

                // Demean checkbox
                CheckBox {
                    id: demeanCheckBox
                    checked: true  // Default to true (yes)
                    
                    indicator: Rectangle {
                        implicitWidth: 20
                        implicitHeight: 20
                        x: demeanCheckBox.leftPadding
                        y: parent.height / 2 - height / 2
                        radius: 3
                        border.color: demeanCheckBox.checked ? "#2196f3" : "#ccc"
                        border.width: 2
                        color: demeanCheckBox.checked ? "#2196f3" : "transparent"

                        Text {
                            anchors.centerIn: parent
                            text: "✓"
                            color: "white"
                            font.pixelSize: 12
                            visible: demeanCheckBox.checked
                        }
                    }

                    contentItem: Text {
                        text: "cfg.demean = '" + (demeanCheckBox.checked ? "yes" : "no") + "'"
                        font.pixelSize: 12
                        color: "#666"
                        leftPadding: demeanCheckBox.indicator.width + demeanCheckBox.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                // Baseline window range slider (only visible when demean is checked)
                Column {
                    width: parent.width
                    spacing: 5
                    visible: demeanCheckBox.checked

                    Text {
                        text: "cfg.baselinewindow = [" + baselineSlider.first.value.toFixed(1) + " " + baselineSlider.second.value.toFixed(1) + "]"
                        font.pixelSize: 12
                        color: "#666"
                    }

                    RangeSlider {
                        id: baselineSlider
                        width: 150
                        from: -0.5
                        to: 0.5
                        first.value: -0.2
                        second.value: 0.0
                        stepSize: 0.1

                        background: Rectangle {
                            x: baselineSlider.leftPadding
                            y: baselineSlider.topPadding + baselineSlider.availableHeight / 2 - height / 2
                            implicitWidth: 200
                            implicitHeight: 6
                            width: baselineSlider.availableWidth
                            height: implicitHeight
                            radius: 3
                            color: "#e0e0e0"

                            Rectangle {
                                x: baselineSlider.first.visualPosition * parent.width
                                width: (baselineSlider.second.visualPosition - baselineSlider.first.visualPosition) * parent.width
                                height: parent.height
                                color: "#2196f3"
                                radius: 3
                            }
                        }

                        first.handle: Rectangle {
                            x: baselineSlider.leftPadding + baselineSlider.first.visualPosition * (baselineSlider.availableWidth - width)
                            y: baselineSlider.topPadding + baselineSlider.availableHeight / 2 - height / 2
                            implicitWidth: 20
                            implicitHeight: 20
                            radius: 10
                            color: baselineSlider.first.pressed ? "#1976d2" : "#2196f3"
                            border.color: "#1976d2"
                            border.width: 2
                        }

                        second.handle: Rectangle {
                            x: baselineSlider.leftPadding + baselineSlider.second.visualPosition * (baselineSlider.availableWidth - width)
                            y: baselineSlider.topPadding + baselineSlider.availableHeight / 2 - height / 2
                            implicitWidth: 20
                            implicitHeight: 20
                            radius: 10
                            color: baselineSlider.second.pressed ? "#1976d2" : "#2196f3"
                            border.color: "#1976d2"
                            border.width: 2
                        }
                    }
                }
            }
        }

        // DFT Filter configuration section
        Rectangle {
            width: parent.width
            height: dftFilterColumn.height + 20
            color: "#f8f9fa"
            border.color: "#e9ecef"
            border.width: 1
            radius: 4
            
            Column {
                id: dftFilterColumn
                width: parent.width - 20
                anchors.left: parent.left
                anchors.leftMargin: 10
                anchors.top: parent.top
                anchors.topMargin: 10
                spacing: 10
                
                // DFT Filter checkbox
                CheckBox {
                    id: dftfilterCheckBox
                    checked: false  // Default to false (no)
                    
                    indicator: Rectangle {
                        implicitWidth: 20
                        implicitHeight: 20
                        x: dftfilterCheckBox.leftPadding
                        y: parent.height / 2 - height / 2
                        radius: 3
                        border.color: dftfilterCheckBox.checked ? "#2196f3" : "#ccc"
                        border.width: 2
                        color: dftfilterCheckBox.checked ? "#2196f3" : "transparent"

                        Text {
                            anchors.centerIn: parent
                            text: "✓"
                            color: "white"
                            font.pixelSize: 12
                            visible: dftfilterCheckBox.checked
                        }
                    }

                    contentItem: Text {
                        text: "cfg.dftfilter = '" + (dftfilterCheckBox.checked ? "yes" : "no") + "'"
                        font.pixelSize: 12
                        color: "#666"
                        leftPadding: dftfilterCheckBox.indicator.width + dftfilterCheckBox.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                
                // DFT Freq range slider (only visible when dftfilter is checked)
                Column {
                    width: parent.width
                    spacing: 5
                    visible: dftfilterCheckBox.checked

                    Text {
                        text: "cfg.dftfreq = [" + dftfreqSlider.first.value.toFixed(0) + " " + dftfreqSlider.second.value.toFixed(0) + "]"
                        font.pixelSize: 12
                        color: "#666"
                    }

                    RangeSlider {
                        id: dftfreqSlider
                        width: 150
                        from: 45
                        to: 65
                        first.value: 50
                        second.value: 60
                        stepSize: 1

                        background: Rectangle {
                            x: dftfreqSlider.leftPadding
                            y: dftfreqSlider.topPadding + dftfreqSlider.availableHeight / 2 - height / 2
                            implicitWidth: 200
                            implicitHeight: 6
                            width: dftfreqSlider.availableWidth
                            height: implicitHeight
                            radius: 3
                            color: "#e0e0e0"

                            Rectangle {
                                x: dftfreqSlider.first.visualPosition * parent.width
                                width: (dftfreqSlider.second.visualPosition - dftfreqSlider.first.visualPosition) * parent.width
                                height: parent.height
                                color: "#2196f3"
                                radius: 3
                            }
                        }

                        first.handle: Rectangle {
                            x: dftfreqSlider.leftPadding + dftfreqSlider.first.visualPosition * (dftfreqSlider.availableWidth - width)
                            y: dftfreqSlider.topPadding + dftfreqSlider.availableHeight / 2 - height / 2
                            implicitWidth: 20
                            implicitHeight: 20
                            radius: 10
                            color: dftfreqSlider.first.pressed ? "#1976d2" : "#2196f3"
                            border.color: "#1976d2"
                            border.width: 2
                        }

                        second.handle: Rectangle {
                            x: dftfreqSlider.leftPadding + dftfreqSlider.second.visualPosition * (dftfreqSlider.availableWidth - width)
                            y: dftfreqSlider.topPadding + dftfreqSlider.availableHeight / 2 - height / 2
                            implicitWidth: 20
                            implicitHeight: 20
                            radius: 10
                            color: dftfreqSlider.second.pressed ? "#1976d2" : "#2196f3"
                            border.color: "#1976d2"
                            border.width: 2
                        }
                    }
                }
            }
        }

        // Run & Save button - Center using Item wrapper
        Item {
            width: parent.width
            height: 35
            
            Button {
                text: preprocessingPageRoot.isProcessing ? "Processing..." : "Preprocess and Run ICA"
                width: 200
                height: 35
                anchors.centerIn: parent
                enabled: !preprocessingPageRoot.isProcessing  // Disable during processing

            background: Rectangle {
                color: parent.enabled ? 
                    (parent.pressed ? "#1976d2" : (parent.hovered ? "#2196f3" : "#2196f3")) :
                    "#888888"  // Gray when disabled
                radius: 5
                border.color: parent.enabled ? "#1976d2" : "#666666"
                border.width: 1
            }

            contentItem: Text {
                text: parent.text
                color: parent.enabled ? "white" : "#cccccc"
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            onClicked: {
                // Set processing state to true
                preprocessingPageRoot.isProcessing = true
                
                var prestimValue = rangeSlider.first.value
                var poststimValue = rangeSlider.second.value
                var trialfunValue = trialfunComboBox.currentText
                var eventtypeValue = eventtypeComboBox.currentText
                var selectedChannels = channelPopup.selectedChannels
                console.log("Running preprocessing and ICA:")
                console.log("cfg.trialdef.prestim =", prestimValue.toFixed(1))
                console.log("cfg.trialdef.poststim =", poststimValue.toFixed(1))
                console.log("cfg.trialfun =", trialfunValue)
                console.log("cfg.trialdef.eventtype =", eventtypeValue)
                console.log("selected channels =", selectedChannels)
                console.log("cfg.trialdef.eventvalue =", eventvaluePopup.selectedEventvalues)
                console.log("cfg.demean =", demeanCheckBox.checked)
                console.log("cfg.baselinewindow =", "[" + baselineSlider.first.value + " " + baselineSlider.second.value + "]")
                console.log("cfg.dftfilter =", dftfilterCheckBox.checked)
                console.log("cfg.dftfreq =", "[" + dftfreqSlider.first.value + " " + dftfreqSlider.second.value + "]")
                console.log("data path =", preprocessingPageRoot.currentFolder)
                
                // Call the new run and save method that includes MATLAB execution with ICA
                matlabExecutor.runAndSaveConfiguration(prestimValue, poststimValue, trialfunValue, eventtypeValue, selectedChannels, eventvaluePopup.selectedEventvalues, demeanCheckBox.checked, baselineSlider.first.value, baselineSlider.second.value, dftfilterCheckBox.checked, dftfreqSlider.first.value, dftfreqSlider.second.value, preprocessingPageRoot.currentFolder)
            }
            }
        }

        // Save confirmation message - Center using Item wrapper
        Item {
            width: parent.width
            height: saveConfirmationText.visible ? saveConfirmationText.height : 0
            
            Text {
                id: saveConfirmationText
                text: preprocessingPageRoot.saveMessage
                font.pixelSize: 12
                color: preprocessingPageRoot.saveMessage.includes("Error") ? "#d32f2f" : "#2e7d32"
                anchors.centerIn: parent
                visible: preprocessingPageRoot.saveMessage !== ""
            }
                }
                
                // Extra spacing at the bottom for better scrolling
                Item {
                    width: parent.width
                    height: 300  // Add 300px of extra space at the bottom
                }
            }  // End Column (mainColumn)
        }  // End ScrollView
        }  // End Column (wrapper)
    }  // End Rectangle
}  // End Item (preprocessingPageRoot)