import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Window 2.15

// Custom Menu bar
Rectangle {
	id: menubar
	z: 99

	width: parent.width
	height: 44

	color: titleBarColor

	Row {
		anchors.right: parent.right
		anchors.verticalCenter: parent.verticalCenter

		spacing: 5
		layoutDirection: Qt.RightToLeft

		height: 48

		// Exit button
		Button {
			anchors.bottom: parent.bottom
			height: parent.height
			width: height * 1.25

			icon.source: "../../resources/window-close.svg"
			icon.width: width
			icon.height: height
			icon.color: iconColor
			flat: true

			onClicked: close()

			DragHandler {
				grabPermissions: PointerHandler.ApprovesCancellation
			}
		}
		// Restore/Maximize Button
		Button {
			anchors.bottom: parent.bottom
			height: parent.height
			width: height * 1.25

			icon.source: visibility == 4 ? "../../resources/window-restore.svg" : "../../resources/window-maximize.svg"
			icon.width: width
			icon.height: height
			icon.color: iconColor
			flat: true

			onClicked: {
				if (visibility == 2) {
					showMaximized()
				}
				else {
					showNormal()
				}
			}

			DragHandler {
				grabPermissions: PointerHandler.ApprovesCancellation
			}
		}

		// Minimize button
		Button {

			anchors.bottom: parent.bottom
			height: parent.height
			width: height * 1.25

			icon.source: "../../resources/window-minimize.svg"
			icon.width: width
			icon.height: height
			icon.color: iconColor
			flat: true

			onClicked: showMinimized()

			DragHandler {
				grabPermissions: PointerHandler.ApprovesCancellation
			}
		}
	}

	// Title text
	Label {
		anchors.centerIn: parent
		
		text: "Nunnix Manga"
		color: textColor

		font.pixelSize: normalTextFontSize
		font.bold: true
	}

	DragHandler {
		target: null
		grabPermissions: PointerHandler.TakeOverForbidden
		onActiveChanged: if (active) { mainWindow.startSystemMove()}
	}

	TapHandler {
		onDoubleTapped: visibility == 2 ? showMaximized() : showNormal()
	}

	MouseArea {
		anchors.fill: parent
		hoverEnabled: true
		acceptedButtons: Qt.NoButton 
	}
}