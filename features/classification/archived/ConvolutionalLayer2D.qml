import QtQuick 2.15

Rectangle {
    id: convRect
    width: convRow.implicitWidth + 40
    height: convRow.implicitHeight + 40
    color: "#ffffff"
    border.color: "#bbbbbbff"
    border.width: 1
    radius: 4
    anchors.horizontalCenter: parent.horizontalCenter

    property int inChannels
    property int outChannels
    property int kernelSize
    property int padding
    property int layerIndex: -1

    signal layerValuesChanged(int layerIndex, int inChannels, int outChannels, int kernelSize, int padding)

    function notifyLayerUpdate() {
        if (layerIndex >= 0) {
            layerValuesChanged(layerIndex, inChannels, outChannels, kernelSize, padding)
        }
    }

    onInChannelsChanged: notifyLayerUpdate()
    onOutChannelsChanged: notifyLayerUpdate()
    onKernelSizeChanged: notifyLayerUpdate()
    onPaddingChanged: notifyLayerUpdate()

    Row {
        id: convRow
        anchors.centerIn: parent
        spacing: 0

        Text {
            text: "Conv2d("
            font.pixelSize: 13
            color: "#333"
        }

        Item {
            width: number1Input.visible ? number1Input.implicitWidth : number1Text.implicitWidth
            height: number1Input.visible ? number1Input.implicitHeight : number1Text.implicitHeight

            Text {
                id: number1Text
                text: inChannels
                font.pixelSize: 13
                color: "#333"
                visible: true

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        number1Input.visible = true
                        number1Input.forceActiveFocus()
                        number1Input.selectAll()
                        number1Text.visible = false
                    }
                }
            }

            TextInput {
                id: number1Input
                text: number1Text.text
                font.pixelSize: 13
                color: "#333"
                visible: false
                onAccepted: {
                    cursorVisible = false
                }
                onActiveFocusChanged: {
                    if (!activeFocus) {
                        var parsedValue = parseInt(text)
                        if (isNaN(parsedValue)) {
                            parsedValue = inChannels
                        }
                        inChannels = parsedValue
                        visible = false
                        number1Text.visible = true
                        cursorVisible = false
                        text = String(inChannels)
                    } else {
                        cursorVisible = true
                    }
                }
            }
        }

        Text {
            text: ", "
            font.pixelSize: 13
            color: "#333"
        }

        Item {
            width: number2Input.visible ? number2Input.implicitWidth : number2Text.implicitWidth
            height: number2Input.visible ? number2Input.implicitHeight : number2Text.implicitHeight

            Text {
                id: number2Text
                text: outChannels
                font.pixelSize: 13
                color: "#333"
                visible: true

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        number2Input.visible = true
                        number2Input.forceActiveFocus()
                        number2Input.selectAll()
                        number2Text.visible = false
                    }
                }
            }

            TextInput {
                id: number2Input
                text: number2Text.text
                font.pixelSize: 13
                color: "#333"
                visible: false
                onAccepted: {
                    cursorVisible = false
                }
                onActiveFocusChanged: {
                    if (!activeFocus) {
                        var parsedValue = parseInt(text)
                        if (isNaN(parsedValue)) {
                            parsedValue = outChannels
                        }
                        outChannels = parsedValue
                        visible = false
                        number2Text.visible = true
                        cursorVisible = false
                        text = String(outChannels)
                    } else {
                        cursorVisible = true
                    }
                }
            }
        }

        Text {
            text: ", kernel_size="
            font.pixelSize: 13
            color: "#333"
        }

        Item {
            width: number3Input.visible ? number3Input.implicitWidth : number3Text.implicitWidth
            height: number3Input.visible ? number3Input.implicitHeight : number3Text.implicitHeight

            Text {
                id: number3Text
                text: kernelSize
                font.pixelSize: 13
                color: "#333"
                visible: true

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        number3Input.visible = true
                        number3Input.forceActiveFocus()
                        number3Input.selectAll()
                        number3Text.visible = false
                    }
                }
            }

            TextInput {
                id: number3Input
                text: number3Text.text
                font.pixelSize: 13
                color: "#333"
                visible: false
                onAccepted: {
                    cursorVisible = false
                }
                onActiveFocusChanged: {
                    if (!activeFocus) {
                        var parsedValue = parseInt(text)
                        if (isNaN(parsedValue)) {
                            parsedValue = kernelSize
                        }
                        kernelSize = parsedValue
                        visible = false
                        number3Text.visible = true
                        cursorVisible = false
                        text = String(kernelSize)
                    } else {
                        cursorVisible = true
                    }
                }
            }
        }

        Text {
            text: ", padding="
            font.pixelSize: 13
            color: "#333"
        }

        Item {
            width: number4Input.visible ? number4Input.implicitWidth : number4Text.implicitWidth
            height: number4Input.visible ? number4Input.implicitHeight : number4Text.implicitHeight

            Text {
                id: number4Text
                text: padding
                font.pixelSize: 13
                color: "#333"
                visible: true

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        number4Input.visible = true
                        number4Input.forceActiveFocus()
                        number4Input.selectAll()
                        number4Text.visible = false
                    }
                }
            }

            TextInput {
                id: number4Input
                text: number4Text.text
                font.pixelSize: 13
                color: "#333"
                visible: false
                onAccepted: {
                    cursorVisible = false
                }
                onActiveFocusChanged: {
                    if (!activeFocus) {
                        var parsedValue = parseInt(text)
                        if (isNaN(parsedValue)) {
                            parsedValue = padding
                        }
                        padding = parsedValue
                        visible = false
                        number4Text.visible = true
                        cursorVisible = false
                        text = String(padding)
                    } else {
                        cursorVisible = true
                    }
                }
            }
        }

        Text {
            text: ")"
            font.pixelSize: 13
            color: "#333"
        }
    }
}
