import QtQuick.Controls 2.15
import QtQuick 2.15

Button {
    property string target
    property string iconFilled
    property string iconOutlined
    property var pastCurrentItem

    flat: stackView.currentItem.name == target ? false : true

    width: parent.parent.width
    height: width

    icon.source: flat ? iconOutlined : iconFilled
    icon.width: iconSize
    icon.height: iconSize
    icon.color: flat ? iconColor : accentColor

    onClicked: {
        if (stackView.currentItem.name != target) {
            stackView.pop()
        }
    }
}