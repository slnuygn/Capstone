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
				child.layerValuesChanged.connect(handleLayerUpdate)
				connectedLayers.push(child)
			}
		}
	}

	function applySavedLayers(layers) {
		if (!layers || !layers.length) {
			return
		}

		for (var i = 0; i < layerColumn.children.length; ++i) {
			var child = layerColumn.children[i]
			if (!child || typeof child.layerIndex === "undefined") {
				continue
			}

			var layerData = layers[child.layerIndex]
			if (!layerData) {
				continue
			}

			if (layerData.hasOwnProperty("inChannels")) {
				child.inChannels = layerData.inChannels
			}
			if (layerData.hasOwnProperty("outChannels")) {
				child.outChannels = layerData.outChannels
			}
			if (layerData.hasOwnProperty("kernelSize")) {
				child.kernelSize = layerData.kernelSize
			}
			if (layerData.hasOwnProperty("padding")) {
				child.padding = layerData.padding
			}
		}
	}

	function syncAllLayersToBackend() {
		if (!classificationConfig) {
			return
		}

		for (var i = 0; i < layerColumn.children.length; ++i) {
			var child = layerColumn.children[i]
			if (!child || typeof child.layerIndex === "undefined") {
				continue
			}

			classificationConfig.updateConvLayer(
						child.layerIndex,
						child.inChannels,
						child.outChannels,
						child.kernelSize,
						child.padding)
		}
	}

	Component.onCompleted: {
		initializeLayers()

		if (classificationConfig) {
			var savedLayers = classificationConfig.getConvLayers()
			if (savedLayers && savedLayers.length) {
				applySavedLayers(savedLayers)
			}
			syncAllLayersToBackend()
		}
	}

	Rectangle {
		width: parent.width / 3
		height: parent.height
		anchors.left: parent.left
		anchors.verticalCenter: parent.verticalCenter
		color: "#f8f9fa"
		border.color: "#dee2e6"
		border.width: 2
		radius: 6

		ScrollView {
			anchors.top: parent.top
			anchors.left: parent.left
			anchors.right: parent.right
			anchors.bottom: parent.bottom
			clip: true

			contentItem: Flickable {
				contentWidth: width
				contentHeight: layerColumn.implicitHeight + 20

				Column {
					id: layerColumn
					x: 10
					y: 10
					width: parent.width - 20
					spacing: 0
					

					ConvolutionalLayer2D {
						inChannels: 3232
						outChannels: 232
						kernelSize: 33434
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
					Line {
					}

					ConvolutionalLayer2D {
						inChannels: 64
						outChannels: 128
						kernelSize: 5
						padding: 2
						
					}
					Line {
					}

					ConvolutionalLayer2D {
						inChannels: 64
						outChannels: 128
						kernelSize: 5
						padding: 2
						
					}
					Line {
					}

					ConvolutionalLayer2D {
						inChannels: 64
						outChannels: 128
						kernelSize: 5
						padding: 2
						
					}
					Line {
					}

					ConvolutionalLayer2D {
						inChannels: 64
						outChannels: 128
						kernelSize: 5
						padding: 2
						
					}
					Line {
					}

					ConvolutionalLayer2D {
						inChannels: 64
						outChannels: 128
						kernelSize: 5
						padding: 2
						
					}

					Line {
					}

					ConvolutionalLayer2D {
						inChannels: 64
						outChannels: 128
						kernelSize: 5
						padding: 2
						
					}
					Line {
					}

					ConvolutionalLayer2D {
						inChannels: 64
						outChannels: 128
						kernelSize: 5
						padding: 2
						
					}
					Line {
					}

					ConvolutionalLayer2D {
						inChannels: 64
						outChannels: 128
						kernelSize: 5
						padding: 2
						
					}
					Line {
					}

					ConvolutionalLayer2D {
						inChannels: 64
						outChannels: 128
						kernelSize: 5
						padding: 2
						
					}

					Line {
					}

					ConvolutionalLayer2D {
						inChannels: 64
						outChannels: 128
						kernelSize: 5
						padding: 2
						
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
}
