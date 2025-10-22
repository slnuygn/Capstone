import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
	id: classificationPageRoot
	anchors.fill: parent
	anchors.margins: 20
	property var connectedLayers: []

	function handleLayerUpdate(layerIdx, inCh, outCh, kSize, pad) {
		if (!classificationConfig) {
			return
		}
		classificationConfig.updateConvLayer(layerIdx, inCh, outCh, kSize, pad)
	}

	function initializeLayers() {
		var nextIndex = 0
		for (var i = 0; i < layerColumn.children.length; ++i) {
			var child = layerColumn.children[i]
			if (!child || typeof child.layerIndex === "undefined") {
				continue
			}
			child.layerIndex = nextIndex
			nextIndex += 1

			if (child.layerValuesChanged && connectedLayers.indexOf(child) === -1) {
				connectedLayers.push(child)
				child.layerValuesChanged.connect(function() {
					handleLayerUpdate(child.layerIndex, child.inChannels, child.outChannels, child.kernelSize, child.padding)
				})
			}
		}
	}

	Rectangle {
		width: parent.width / 3
		height: parent.height
		anchors.left: parent.left
		anchors.top: parent.top
		anchors.bottom: parent.bottom
		color: "#fdfdfdff"
		border.color: "#8d8d8dff"
		border.width: 1
		radius: 5

		ScrollView {
			anchors.fill: parent
			anchors.margins: 10
			clip: true

			Item {
				width: parent.width
				height: layerColumn.implicitHeight

				Column {
					id: layerColumn
					anchors.horizontalCenter: parent.horizontalCenter
					spacing: 0
					width: parent.width

					ConvolutionalLayer2D {
					inChannels: 3
					outChannels: 32
					kernelSize: 3
					padding: 0
				}

				Line {
					
				}

				ConvolutionalLayer2D {
					
					inChannels: 32
					outChannels: 64
					kernelSize: 3
					padding: 1
				}

				Line {
					
				}

				ConvolutionalLayer2D {
					
					inChannels: 64
					outChannels: 128
					kernelSize: 5
					padding: 2
				}
				}
			}
		}
	}

	Component.onCompleted: {
		initializeLayers()
	}
}
