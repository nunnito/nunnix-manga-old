import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Controls 2.15

Button {
    property alias chapterButton: chapterButton

    property string chapterName
    property string chapterDate
    property string chapterLink
    Material.background: surfaceColor

    id: chapterButton
    width: parent.width
    height: normalSpacing * 4 - normalSpacing / 2

    text: chapterName
    opacity: 0

    contentItem: Label {
        text: chapterButton.text
        color: textColor

        font.pixelSize: normalTextFontSize
        elide: Text.ElideRight

        // Date
        Label {
            text: chapterButton.chapterDate
            color: textColor
            font.pixelSize: smallTextFontSize

            anchors.bottom: parent.bottom
            anchors.left: parent.left
        }
    }
}