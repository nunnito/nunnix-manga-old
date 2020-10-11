import QtQuick 2.15
import QtQuick.Controls 2.15

Menu {
    id: menu

    // Download chapter
    MenuItem {
        id: download
        text: downloaded ? qsTr("Delete") : qsTr("Download")

        onTriggered: queued = true
    }
    // Bookmark/unbookmark chapter
    MenuItem {
        id: bookmark
        text: bookmarked ? qsTr("Unbookmark") : qsTr("Bookmark")

        onTriggered: bookmarked = !bookmarked
    }
    // Mark chapter as read/unread
    MenuItem {
        id: markAsRead
        text: read ? qsTr("Mark as unread") : qsTr("Mark as read")

        onTriggered: read = !read
    }

    MenuSeparator {}

    // Copy chapter link
    MenuItem {
        id: copyLink
        text: qsTr("Copy chapter link")

        onTriggered: copy(chapterLink)
    }
    // Mark all previous chapters as read
    MenuItem {
        id: previousAsRead
        text: qsTr("Mark previous as read")

        onTriggered: markPreviousAsRead(index)
    }

    onClosed: mouseArea.acceptedButtons = Qt.RightButton, parent.active = false

    Component.onCompleted: popup()
    Component.onDestruction: mouseArea.acceptedButtons = Qt.RightButton, parent.active = false
}