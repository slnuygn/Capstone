import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs
import MatlabExecutor 1.0
import FileBrowser 1.0

ApplicationWindow {
    id: window
    visible: true
    width: 600
    height: 500
    title: "Capstone"

    // Property to hold MATLAB output
    property string matlabOutput: "Click 'Run MATLAB' to execute script"
    property var folderContents: []
    property string currentFolder: ""
    property string saveMessage: ""
    property string fieldtripPath: ""
    // Properties for menu states
    property bool fileMenuOpen: false
    property bool matlabSubmenuOpen: false

    // Connect to the matlabExecutor signal
    Connections {
        target: matlabExecutor
        function onOutputChanged(output) {
            window.matlabOutput = output
        }
        function onConfigSaved(message) {
            window.saveMessage = message
            saveMessageTimer.start()
            // Refresh FieldTrip path display if updated
            if (message.includes("FieldTrip path updated")) {
                fieldtripPathRefreshTimer.start()
            }
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
            newSelection.splice(index, 1)
        } else {
            newSelection.push(channel)
        }
        channelPopup.selectedChannels = newSelection // Reassign to trigger property change
    }

    function getSelectedChannelsText() {
        if (channelPopup.selectedChannels.length === 0) {
            return "None"
        } else if (channelPopup.selectedChannels.length <= 3) {
            return channelPopup.selectedChannels.join(", ")
        } else {
            return channelPopup.selectedChannels.slice(0, 3).join(", ") + "... (" + channelPopup.selectedChannels.length + " total)"
        }
    }

    function getSelectedChannelsCount() {
        return channelPopup.selectedChannels.length.toString()
    }

    // Timer to clear save message after a few seconds
    Timer {
        id: saveMessageTimer
        interval: 3000
        onTriggered: window.saveMessage = ""
    }

    // Timer to refresh FieldTrip path display
    Timer {
        id: fieldtripPathRefreshTimer
        interval: 200
        onTriggered: {
            if (matlabExecutor) {
                window.fieldtripPath = matlabExecutor.getCurrentFieldtripPath()
            }
        }
    }

    // Connect to the fileBrowser signals
    Connections {
        target: fileBrowser
        function onFolderContentsChanged(contents) {
            window.folderContents = contents
        }
        function onCurrentFolderChanged(folder) {
            window.currentFolder = folder
        }
    }

    // Function to refresh folder contents
    function refreshFolderContents() {
        if (fileBrowser) {
            fileBrowser.refreshCurrentFolder()
        }
    }

    // File Dialog for folder selection
    FolderDialog {
        id: folderDialog
        title: "Select Folder"
        currentFolder: fileBrowser ? "file:///" + fileBrowser.getDesktopPath() : "file:///C:/Users"
        
        onAccepted: {
            if (fileBrowser) {
                fileBrowser.loadFolder(selectedFolder.toString())
                // Also update the MATLAB script with the selected folder
                if (matlabExecutor) {
                    matlabExecutor.updateDataDirectory(selectedFolder.toString())
                }
            }
        }
    }

    // FieldTrip Path Dialog
    FolderDialog {
        id: fieldtripDialog
        title: "Select FieldTrip Installation Folder"
        currentFolder: "file:///C:/Program Files/MATLAB"
        
        onAccepted: {
            if (matlabExecutor) {
                matlabExecutor.updateFieldtripPath(selectedFolder.toString())
            }
        }
    }

    // Top Menu Bar
    Rectangle {
        id: topMenuBar
        width: parent.width
        height: 30
        color: "#f8f9fa"
        
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
                color: fileMenuArea.containsMouse || window.fileMenuOpen ? "#d1d3d4" : "transparent"
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
                        window.fileMenuOpen = !window.fileMenuOpen
                    }
                }
            }

            // Edit Menu
            Rectangle {
                width: editMenuText.width + 20
                height: 25
                color: editMenuArea.containsMouse ? "#d1d3d4" : "transparent"
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
                        console.log("Edit menu clicked")
                        // TODO: Implement edit menu dropdown
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

    // Global MouseArea to close file menu when clicking outside
    MouseArea {
        anchors.fill: parent
        onClicked: {
            if (window.fileMenuOpen) {
                window.fileMenuOpen = false
                window.matlabSubmenuOpen = false
            }
        }
        z: -10
    }

    // Tab bar at the top
    Rectangle {
        id: tabBar
        anchors.top: topMenuBar.bottom
        width: parent.width
        height: 40
        color: "#e0e0e0"

        // Top border only
        Rectangle {
            width: parent.width
            height: 1
            color: "#e0e0e0"
            anchors.top: parent.top
        }

        Row {
            anchors.left: parent.left
            anchors.leftMargin: 5
            anchors.top: parent.top
            anchors.topMargin: 2  // Start below the top border
            height: parent.height - 2  // Adjust height to account for border

            // Tab 1 - Preprocessing
            Rectangle {
                id: preprocessingTab
                width: 120
                height: parent.height
                color: contentArea.currentIndex === 0 ? "white" : "#e0e0e0"

                Text {
                    text: "Preprocessing"
                    anchors.centerIn: parent
                    font.pixelSize: 14
                    color: "#333"
                    
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: contentArea.currentIndex = 0
                }
            }

            // Tab 2 - Processing
            Rectangle {
                id: processingTab
                width: 120
                height: parent.height
                color: contentArea.currentIndex === 1 ? "white" : "#e0e0e0"

                Text {
                    text: "Processing"
                    anchors.centerIn: parent
                    font.pixelSize: 14
                    color: "#333"
                    
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: contentArea.currentIndex = 1
                }
            }

            // Tab 3 - Classifier
            Rectangle {
                id: classifierTab
                width: 120
                height: parent.height
                color: contentArea.currentIndex === 2 ? "white" : "#e0e0e0"

                Text {
                    text: "Classifier"
                    anchors.centerIn: parent
                    font.pixelSize: 14
                    color: "#333"
                    
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: contentArea.currentIndex = 2
                }
            }
        }
    }

    // Content area (window underneath)
    Rectangle {
        id: contentArea
        anchors.top: tabBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        color: "white"
        

        property int currentIndex: 0

        // Tab 1 Content - Preprocessing
        Item {
            id: preprocessingPage
            anchors.fill: parent
            visible: contentArea.currentIndex === 0

            Loader {
                id: preprocessingPageLoader
                anchors.fill: parent
                source: "preprocessing_page.qml"
                
                onLoaded: {
                    item.currentFolder = Qt.binding(function() { return window.currentFolder })
                    item.folderContents = Qt.binding(function() { return window.folderContents })
                    item.fieldtripPath = Qt.binding(function() { return window.fieldtripPath })
                    item.saveMessage = Qt.binding(function() { return window.saveMessage })
                    item.contextMenu = contextMenu  // Pass context menu reference
                    
                    // Initialize eventvalue dropdown with current values from MATLAB file
                    if (matlabExecutor) {
                        var currentEventvalues = matlabExecutor.getCurrentEventvalue()
                        item.setInitialEventvalues(currentEventvalues)
                        
                        // Initialize channels with current values from CTL_preprocessing.m
                        var currentChannels = matlabExecutor.getCurrentChannels()
                        item.setInitialChannels(currentChannels)
                        
                        // Initialize demean settings from prep_data.m
                        var currentDemean = matlabExecutor.getCurrentDemean()
                        var currentBaseline = matlabExecutor.getCurrentBaselineWindow()
                        item.setInitialDemean(currentDemean, currentBaseline)
                        
                        // Initialize DFT filter settings from prep_data.m
                        var currentDftfilter = matlabExecutor.getCurrentDftfilter()
                        var currentDftfreq = matlabExecutor.getCurrentDftfreq()
                        item.setInitialDftfilter(currentDftfilter, currentDftfreq)
                    }
                    
                    item.openFolderDialog.connect(function() { folderDialog.open() })
                    item.openFieldtripDialog.connect(function() { fieldtripDialog.open() })
                    item.requestSaveConfiguration.connect(function(prestimValue, poststimValue, trialfunValue, eventtypeValue, selectedChannels, selectedEventvalues, demeanEnabled, baselineStart, baselineEnd, dftfilterEnabled, dftfreqStart, dftfreqEnd) {
                        matlabExecutor.saveConfiguration(prestimValue, poststimValue, trialfunValue, eventtypeValue, selectedChannels, selectedEventvalues, demeanEnabled, baselineStart, baselineEnd, dftfilterEnabled, dftfreqStart, dftfreqEnd)
                    })
                    item.refreshFileExplorer.connect(function() { 
                        refreshFolderContents()
                    })
                }
            }
        }

        // Tab 2 Content - Processing
        Item {
            id: processingPage
            anchors.fill: parent
            anchors.margins: 20
            visible: contentArea.currentIndex === 1

            Text {
                anchors.centerIn: parent
                text: "hello world 2"
                font.pixelSize: 24
                color: "#333"
            }
        }

        // Tab 3 Content - Classifier
        Item {
            id: classifierPage
            anchors.fill: parent
            anchors.margins: 20
            visible: contentArea.currentIndex === 2

            Text {
                anchors.centerIn: parent
                text: "hello world 3"
                font.pixelSize: 24
                color: "#333"
            }
        }
    }

    // File Menu Dropdown (positioned absolutely at window level)
    Rectangle {
        id: fileDropdownMenu
        x: 10  // Position relative to File menu button
        y: 25  // Position directly at the bottom of the File button (no gap)
        width: 220
        height: 110
        color: "white"
        border.color: "#ccc"
        border.width: 1
        radius: 4
        visible: window.fileMenuOpen
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

            // Add MATLAB function/script
            Rectangle {
                width: parent.width
                height: 35
                color: matlabFunctionMouseArea.containsMouse || window.matlabSubmenuOpen ? "#f8f9fa" : "white"

                Row {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 10
                    spacing: 10

                

                    Text {
                        text: "Add MATLAB function/script..."
                        font.pixelSize: 12
                        color: "#333"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                // Arrow indicator for submenu (positioned separately)
                Text {
                    text: "▶"
                    font.pixelSize: 12
                    color: "#666"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: 15
                }

                MouseArea {
                    id: matlabFunctionMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        window.matlabSubmenuOpen = !window.matlabSubmenuOpen
                    }
                }
            }

            // Change FieldTrip path
            Rectangle {
                width: parent.width
                height: 35
                color: changeFieldtripMainMouseArea.containsMouse ? "#f8f9fa" : "white"

                Row {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 10
                    spacing: 10

                
                    Text {
                        text: "Change FieldTrip path..."
                        font.pixelSize: 12
                        color: "#333"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                MouseArea {
                    id: changeFieldtripMainMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        window.fileMenuOpen = false
                        window.matlabSubmenuOpen = false
                        fieldtripDialog.open()
                    }
                }
            }

            // Change data path
            Rectangle {
                width: parent.width
                height: 35
                color: changeDataPathMainMouseArea.containsMouse ? "#f8f9fa" : "white"

                Row {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 10
                    spacing: 10

                

                    Text {
                        text: "Change data path..."
                        font.pixelSize: 12
                        color: "#333"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                MouseArea {
                    id: changeDataPathMainMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        window.fileMenuOpen = false
                        window.matlabSubmenuOpen = false
                        folderDialog.open()
                    }
                }
            }
        }
    }

    // MATLAB Submenu (appears next to the File dropdown)
    Rectangle {
        id: matlabSubmenu
        x: fileDropdownMenu.x + fileDropdownMenu.width
        y: fileDropdownMenu.y
        width: 180
        height: 80
        color: "white"
        border.color: "#ccc"
        border.width: 1
        radius: 4
        visible: window.matlabSubmenuOpen && window.fileMenuOpen
        z: 10001

        // Drop shadow effect
        Rectangle {
            anchors.fill: parent
            anchors.topMargin: 2
            anchors.leftMargin: 2
            color: "#00000020"
            radius: 4
            z: -1
        }

        MouseArea {
            anchors.fill: parent
            // Keep submenu open when hovering over it (no action needed)
        }

        Column {
            anchors.fill: parent
            anchors.margins: 2

            // Create function/script option
            Rectangle {
                width: parent.width
                height: 38
                color: createFunctionMouseArea.containsMouse ? "#f8f9fa" : "white"

                Row {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 10
                    spacing: 8

                    Text {
                        text: "+"
                        font.pixelSize: 16
                        font.bold: true
                        color: "#28a745"
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: "Create function/script"
                        font.pixelSize: 12
                        color: "#333"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                MouseArea {
                    id: createFunctionMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        window.fileMenuOpen = false
                        window.matlabSubmenuOpen = false
                        console.log("Create function/script clicked")
                        // TODO: Implement create function/script functionality
                    }
                }
            }

            // Open file explorer option
            Rectangle {
                width: parent.width
                height: 38
                color: openExplorerMouseArea.containsMouse ? "#f8f9fa" : "white"

                Row {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 10
                    spacing: 8

                    Text {
                        text: "📁"
                        font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: "Open file explorer"
                        font.pixelSize: 12
                        color: "#333"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                MouseArea {
                    id: openExplorerMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        window.fileMenuOpen = false
                        window.matlabSubmenuOpen = false
                        console.log("Open file explorer clicked")
                        // TODO: Implement open file explorer functionality
                    }
                }
            }
        }
    }

    // Custom context menu using Popup
    Popup {
        id: contextMenu
        
        property string fileName: ""
        property string filePath: ""
        property bool isMatFile: false
        
        width: 160  // Reduced width
        height: menuColumn.height + 12  // Reduced padding
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        
        // Method to open at specific coordinates
        function openAt(mouseX, mouseY) {
            x = mouseX
            y = mouseY
            open()
        }
        
        background: Rectangle {
            color: "white"
            border.color: "#cccccc"
            border.width: 1
            radius: 4
            
            Rectangle {
                anchors.fill: parent
                anchors.margins: 1
                color: "transparent"
                border.color: "#f0f0f0"
                border.width: 1
                radius: 3
            }
        }
        
        Column {
            id: menuColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 4
            anchors.topMargin: 0  // No top margin at all
            spacing: 1
            
            // Open Data Browser option (for any .mat file)
            Rectangle {
                id: openDataBrowserItem
                width: parent.width
                height: 24  // Reduced height
                visible: contextMenu.isMatFile
                color: openDataBrowserMouseArea.containsMouse ? "#e3f2fd" : "transparent"
                radius: 2
                
                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 8
                    
                    Text {
                        text: "Open Data Browser"
                        font.pixelSize: 12
                        color: "#333"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                
                MouseArea {
                    id: openDataBrowserMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        console.log("Opening Data Browser for:", contextMenu.fileName)
                        matlabExecutor.launchMatlabICABrowser(contextMenu.filePath)
                        contextMenu.close()
                    }
                }
            }
            
            // View File Info option
            Rectangle {
                id: viewFileInfoItem
                width: parent.width
                height: 24  // Reduced height
                visible: contextMenu.isMatFile
                color: viewFileInfoMouseArea.containsMouse ? "#e3f2fd" : "transparent"
                radius: 2
                
                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 8
                    
                    Text {
                        text: "View File Info"
                        font.pixelSize: 12
                        color: "#333"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                
                MouseArea {
                    id: viewFileInfoMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        console.log("Viewing file info for:", contextMenu.fileName)
                        contextMenu.close()
                    }
                }
            }
            
            // Copy File Path option
            Rectangle {
                id: copyPathItem
                width: parent.width
                height: 24  // Reduced height
                color: copyPathMouseArea.containsMouse ? "#e3f2fd" : "transparent"
                radius: 2
                
                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 8
                    
                    Text {
                        text: "Copy File Path"
                        font.pixelSize: 12
                        color: "#333"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                
                MouseArea {
                    id: copyPathMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        console.log("Copying path:", contextMenu.filePath)
                        contextMenu.close()
                    }
                }
            }
        }
    }

    // File properties dialog
    Dialog {
        id: filePropertiesDialog
        title: "File Properties"
        modal: true
        standardButtons: Dialog.Ok

        property string fileName: ""
        property string filePath: ""
        property bool isICAFile: false

        Column {
            spacing: 10
            padding: 10

            Text {
                text: "File Name:"
                font.bold: true
            }

            Text {
                text: filePropertiesDialog.fileName
            }

            Text {
                text: "File Path:"
                font.bold: true
            }

            Text {
                text: filePropertiesDialog.filePath
            }

            Text {
                text: "File Type:"
                font.bold: true
            }

            Text {
                text: filePropertiesDialog.isICAFile ? "ICA File" : "MATLAB Data File"
            }
        }
    }

}
