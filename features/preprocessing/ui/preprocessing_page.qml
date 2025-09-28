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
            eventvalueDropdown.selectedItems = eventvalues
        }
    }
    
    // Function to initialize channels from main.qml
    function setInitialChannels(channels) {
        if (channels && channels.length > 0) {
            selectedChannels = channels
            channelDropdown.selectedItems = channels
        }
    }
    
    // Function to initialize demean settings from main.qml
    function setInitialDemean(baselineWindow) {
        if (baselineWindow && baselineWindow.length >= 2) {
            baselineSlider.firstValue = baselineWindow[0]
            baselineSlider.secondValue = baselineWindow[1]
        }
    }
    
    // Function to initialize DFT filter settings from main.qml
    function setInitialDftfilter(dftfreq) {
        if (dftfreq && dftfreq.length >= 2) {
            dftfreqSlider.firstValue = dftfreq[0]
            dftfreqSlider.secondValue = dftfreq[1]
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
    
    // Property for backward compatibility with selectedChannels
    property var selectedChannels: ["F4", "Fz", "C3", "Pz", "P3", "O1", "Oz", "O2", "P4", "Cz", "C4"]
    property bool editModeEnabled: false  // Track edit mode state
    
    // JavaScript functions for channel selection
    function isChannelSelected(channel) {
        return selectedChannels.indexOf(channel) !== -1
    }

    function isAllSelected() {
        return selectedChannels.length === channelDropdown.allItems.length
    }

    function toggleChannel(channel) {
        var index = selectedChannels.indexOf(channel)
        var newSelection = selectedChannels.slice() // Create a copy
        
        if (index !== -1) {
            // Remove channel
            newSelection.splice(index, 1)
        } else {
            // Add channel
            newSelection.push(channel)
        }
        
        selectedChannels = newSelection
    }

    function getSelectedChannelsText() {
        if (selectedChannels.length === 0) {
            return "None"
        } else if (selectedChannels.length === channelDropdown.allItems.length) {
            return "All"
        } else {
            return selectedChannels.join(", ")
        }
    }

    function getSelectedChannelsCount() {
        return selectedChannels.length
    }

    // JavaScript functions for eventvalue selection
    function isEventvalueSelected(eventvalue) {
        return eventvalueDropdown.selectedItems.indexOf(eventvalue) !== -1
    }

    function toggleEventvalue(eventvalue) {
        var index = eventvalueDropdown.selectedItems.indexOf(eventvalue)
        var newSelection = eventvalueDropdown.selectedItems.slice() // Create a copy
        
        if (index !== -1) {
            // Remove eventvalue
            newSelection.splice(index, 1)
        } else {
            // Add eventvalue
            newSelection.push(eventvalue)
        }
        
        eventvalueDropdown.selectedItems = newSelection
    }

    function getSelectedEventvaluesText() {
        if (eventvalueDropdown.selectedItems.length === 0) {
            return ""
        } else {
            return "'" + eventvalueDropdown.selectedItems.join("' '") + "'"
        }
    }

    function getSelectedEventvaluesCount() {
        return eventvalueDropdown.selectedItems.length
    }

    // Function to handle edit mode toggle from TopMenu
    function setEditMode(editModeEnabled) {
        preprocessingPageRoot.editModeEnabled = editModeEnabled
        var newState = editModeEnabled ? "edit" : "default"
        
        // Update all dropdown states
        trialfunDropdown.dropdownState = newState
        eventtypeDropdown.dropdownState = newState
        eventvalueDropdown.dropdownState = newState
        channelDropdown.dropdownState = newState
        
        // Update all slider states
        prestimPoststimSlider.sliderState = newState
        baselineSlider.sliderState = newState
        dftfreqSlider.sliderState = newState
        
        console.log("Edit mode set to:", newState)
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
                                                // Left-click: Check if it's a .mat file and handle accordingly
                                                var cleanFilename = modelData.replace(/^[^\w]+/, '')  // Remove leading emojis/symbols
                                                
                                                if (cleanFilename.toLowerCase().endsWith('.mat')) {
                                                    // Check if it's an ICA file by looking for ICA indicators in filename
                                                    var isICAFile = cleanFilename.toLowerCase().includes('ica') || 
                                                                   cleanFilename.toLowerCase().includes('comp') ||
                                                                   cleanFilename.toLowerCase().includes('component')
                                                    
                                                    if (isICAFile) {
                                                        console.log("ICA file detected:", cleanFilename)
                                                        var fullPath = preprocessingPageRoot.currentFolder + "/" + cleanFilename
                                                        
                                                        // Call browse_ICA function through MATLAB executor
                                                        if (matlabExecutor) {
                                                            matlabExecutor.launchMatlabICABrowser(fullPath)
                                                        }
                                                    } else {
                                                        console.log("Not an ICA file:", cleanFilename)
                                                    }
                                                } else {
                                                    console.log("Not a .mat file:", cleanFilename)
                                                }
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
            
            // Header row with text and buttons
            Row {
                width: parent.width
                height: 35
                spacing: 10  // Add spacing between elements
                
                // Header text
                Text {
                    id: headerText
                    text: "The .set files in this directory will be preprocessed."
                    font.pixelSize: 14
                    color: "#333"
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                // Spacer to push buttons to the right
                Item {
                    width: addButton.visible ? 
                        (parent.width - headerText.width - addButton.width - runButton.width - 100 - parent.spacing * 3) :
                        (parent.width - headerText.width - runButton.width - 100 - parent.spacing * 2)
                    height: 1
                }
                
                // Add button with dropdown menu
                Rectangle {
                    id: addButton
                    width: 80
                    height: 35
                    visible: preprocessingPageRoot.editModeEnabled
                    property bool menuOpen: false
                    
                    color: mouseArea.containsMouse ? "#f5f5f5" : "transparent"
                    radius: 5
                    border.color: "#2196f3"
                    border.width: 1
                    
                    Text {
                        text: "Add ▼"
                        color: "#2196f3"
                        font.pixelSize: 12
                        anchors.centerIn: parent
                    }
                    
                    MouseArea {
                        id: mouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            addButton.menuOpen = !addButton.menuOpen
                        }
                    }
                    
                    // Add dropdown menu (styled like main.qml dropdowns)
                    Rectangle {
                        id: addMenuPopup
                        x: 0
                        y: addButton.height
                        width: 150
                        height: 80
                        color: "white"
                        border.color: "#ccc"
                        border.width: 1
                        radius: 4
                        visible: addButton.menuOpen
                        z: 10000
                        
                        // Drop shadow effect
                        Rectangle {
                            anchors.fill: parent
                            anchors.topMargin: 2
                            anchors.leftMargin: 2
                            color: "#00000020"
                            radius: 4
                            z: -1
                        }
                        
                        Column {
                            anchors.fill: parent
                            anchors.margins: 2
                            
                            // Range Slider menu item
                            Rectangle {
                                width: parent.width
                                height: 35
                                color: rangeSliderArea.containsMouse ? "#f8f9fa" : "white"
                                
                                Text {
                                    text: "Range Slider"
                                    anchors.left: parent.left
                                    anchors.leftMargin: 10
                                    anchors.verticalCenter: parent.verticalCenter
                                    font.pixelSize: 12
                                    color: "#333"
                                }
                                
                                MouseArea {
                                    id: rangeSliderArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        console.log("Range Slider selected")
                                        addButton.menuOpen = false
                                    }
                                }
                            }
                            
                            // Dropdown Menu item
                            Rectangle {
                                width: parent.width
                                height: 35
                                color: dropdownMenuArea.containsMouse ? "#f8f9fa" : "white"
                                
                                Text {
                                    text: "Dropdown Menu"
                                    anchors.left: parent.left
                                    anchors.leftMargin: 10
                                    anchors.verticalCenter: parent.verticalCenter
                                    font.pixelSize: 12
                                    color: "#333"
                                }
                                
                                MouseArea {
                                    id: dropdownMenuArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        console.log("Dropdown Menu selected")
                                        addButton.menuOpen = false
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Run & Save button
                Button {
                    id: runButton
                    text: preprocessingPageRoot.isProcessing ? "Processing..." : "Preprocess and Run ICA"
                    width: 200
                    height: 35
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
                        
                        var prestimValue = prestimPoststimSlider.firstValue
                        var poststimValue = prestimPoststimSlider.secondValue
                        var trialfunValue = trialfunDropdown.selectedItems.length > 0 ? trialfunDropdown.selectedItems[0] : ""
                        var eventtypeValue = eventtypeDropdown.selectedItems.length > 0 ? eventtypeDropdown.selectedItems[0] : ""
                        var selectedChannels = selectedChannels
                        console.log("Running preprocessing and ICA:")
                        console.log("cfg.trialdef.prestim =", prestimValue.toFixed(1))
                        console.log("cfg.trialdef.poststim =", poststimValue.toFixed(1))
                        console.log("cfg.trialfun =", trialfunValue)
                        console.log("cfg.trialdef.eventtype =", eventtypeValue)
                        console.log("selected channels =", selectedChannels)
                        console.log("cfg.trialdef.eventvalue =", eventvalueDropdown.selectedItems)
                        console.log("cfg.demean =", "yes")
                        console.log("cfg.baselinewindow =", "[" + baselineSlider.firstValue + " " + baselineSlider.secondValue + "]")
                        console.log("cfg.dftfilter =", "yes")
                        console.log("cfg.dftfreq =", "[" + dftfreqSlider.firstValue + " " + dftfreqSlider.secondValue + "]")
                        console.log("data path =", preprocessingPageRoot.currentFolder)
                        
                        // Call the new run and save method that includes MATLAB execution with ICA
                        matlabExecutor.runAndSaveConfiguration(prestimValue, poststimValue, trialfunValue, eventtypeValue, selectedChannels, eventvalueDropdown.selectedItems, true, baselineSlider.firstValue, baselineSlider.secondValue, true, dftfreqSlider.firstValue, dftfreqSlider.secondValue, preprocessingPageRoot.currentFolder)
                    }
                }
            }
            
            // Scrollable content area
            ScrollView {
                width: parent.width  
                height: 700  // Fixed height that's reasonable for the content
                clip: true
                
                Column {
                    id: mainColumn
                    spacing: 15  // Reduced spacing for better space usage
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
                    width: parent.width - 40  // Fill available width minus button width and spacing
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
        DropdownTemplate {
            id: trialfunDropdown
            label: "Trialfun"
            matlabProperty: "cfg.trialfun"
            isMultiSelect: true
            maxSelections: 1
            allItems: ["ft_trialfun_general", "alternative"]
            selectedItems: ["ft_trialfun_general"]
            hasAddFeature: true
            addPlaceholder: "Add custom trialfun..."
            dropdownState: "default"

            onMultiSelectionChanged: function(selected) {
                if (selected.length > 0) {
                    matlabExecutor.saveTrialfunSelection(selected[0], 0)
                }
            }

            onAddItem: function(newItem) {
                // Save the custom option to the QML file
                matlabExecutor.addCustomTrialfunOptionToAllItems(newItem)
            }

            onDeleteItem: function(itemToDelete) {
                // Remove the custom option from the QML file
                matlabExecutor.deleteCustomTrialfunOptionFromAllItems(itemToDelete)
            }

            onDeleteRequested: {
                // Handle deletion of this dropdown
                trialfunDropdown.visible = false
            }
        }

        // Eventtype dropdown
        DropdownTemplate {
            id: eventtypeDropdown
            label: "Eventtype"
            matlabProperty: "cfg.trialdef.eventtype"
            isMultiSelect: true
            maxSelections: 1
            allItems: ["Stimulus", "alternatives"]
            selectedItems: ["Stimulus"]
            hasAddFeature: true
            addPlaceholder: "Add custom eventtype..."
            dropdownState: "default"

            onMultiSelectionChanged: function(selected) {
                if (selected.length > 0) {
                    matlabExecutor.saveEventtypeSelection(selected[0], 0)
                }
            }

            onAddItem: function(newItem) {
                // Save the custom option to the QML file
                matlabExecutor.addCustomEventtypeOptionToAllItems(newItem)
            }

            onDeleteItem: function(itemToDelete) {
                // Remove the custom option from the QML file
                matlabExecutor.deleteCustomEventtypeOptionFromAllItems(itemToDelete)
            }

            onDeleteRequested: {
                // Handle deletion of this dropdown
                eventtypeDropdown.visible = false
            }
        }

        // Eventvalue multi-select dropdown
        DropdownTemplate {
            id: eventvalueDropdown
            label: "Eventvalue"
            matlabProperty: "cfg.trialdef.eventvalue"
            isMultiSelect: true
            allItems: ["S200", "S201", "S202"]
            selectedItems: ["S200", "S201", "S202"]
            hasAddFeature: true
            addPlaceholder: "Add custom eventvalue..."
            dropdownState: "default"

            onMultiSelectionChanged: function(selected) {
                // Handle multi-selection changes for eventvalues
                console.log("Eventvalues selected:", selected)
            }

            onAddItem: function(newItem) {
                // Save the custom option to the QML file
                matlabExecutor.addCustomEventvalueOptionToAllItems(newItem)
            }

            onDeleteItem: function(itemToDelete) {
                // Remove the custom option from the QML file
                matlabExecutor.deleteCustomEventvalueOptionFromAllItems(itemToDelete)
            }

            onDeleteRequested: {
                // Handle deletion of this dropdown
                eventvalueDropdown.visible = false
            }
        }

        // Channel Selection
        // Channel Selection using DropdownTemplate
        DropdownTemplate {
            id: channelDropdown
            label: "Choose Channels: " + getSelectedChannelsText()
            matlabProperty: "cfg.channel"
            isMultiSelect: true
            model: ["Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "C3", "Cz", "C4", "P3", "Pz", "P4", "T3", "T4", "T5", "T6", "O1", "O2", "Oz"]
            allItems: ["Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "C3", "Cz", "C4", "P3", "Pz", "P4", "T3", "T4", "T5", "T6", "O1", "O2", "Oz"]
            selectedItems: ["F4", "Fz", "C3", "Pz", "P3", "O1", "Oz", "O2", "P4", "Cz", "C4"]
            hasAddFeature: true
            addPlaceholder: "Add custom channel..."
            dropdownState: "default"

            onMultiSelectionChanged: {
                // Update the selectedChannels property for backward compatibility
                selectedChannels = selectedItems
            }

            onAddItem: function(newItem) {
                // Save the custom option to the QML file
                matlabExecutor.addCustomChannelOptionToAllItems(newItem)
            }

            onDeleteItem: function(itemToDelete) {
                // Remove the custom option from the QML file
                matlabExecutor.deleteCustomChannelOptionFromAllItems(itemToDelete)
            }

            onDeleteRequested: {
                // Handle deletion of this dropdown
                channelDropdown.visible = false
            }
        }

        // Prestim/Poststim Range Slider using RangeSliderTemplate
        RangeSliderTemplate {
            id: prestimPoststimSlider
            label: "Trial Time Window (seconds)"
            matlabProperty: "cfg.trialdef"
            from: 0.0
            to: 1.0
            firstValue: 0.5
            secondValue: 1.0
            stepSize: 0.1
            unit: ""
            sliderState: "default"
            sliderId: "prestimPoststimSlider"

            onRangeChanged: {
                // Range values updated, will be used when running preprocessing
            }

            onDeleteRequested: {
                // Handle deletion of this slider
                prestimPoststimSlider.visible = false
            }
        }

        // Baseline window range slider using RangeSliderTemplate
        RangeSliderTemplate {
            id: baselineSlider
            label: "Baseline Window (seconds)"
            matlabProperty: "cfg.baselinewindow"
            from: -0.5
            to: 0.6
            firstValue: -0.2
            secondValue: 0.0
            stepSize: 0.1
            unit: ""
            sliderState: "default"
            sliderId: "baselineSlider"

            onRangeChanged: {
                // Baseline values updated, will be used when running preprocessing
            }

            onDeleteRequested: {
                // Handle deletion of this slider
                baselineSlider.visible = false
            }
        }

        // DFT Freq range slider using RangeSliderTemplate
        RangeSliderTemplate {
            id: dftfreqSlider
            label: "DFT Frequency Range (Hz)"
            matlabProperty: "cfg.dftfreq"
            from: 45.0
            to: 70.0
            firstValue: 50.0
            secondValue: 60.0
            stepSize: 1
            unit: ""
            sliderState: "default"
            sliderId: "dftfreqSlider"

            onRangeChanged: {
                // DFT frequency values updated, will be used when running preprocessing
            }

            onDeleteRequested: {
                // Handle deletion of this slider
                dftfreqSlider.visible = false
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