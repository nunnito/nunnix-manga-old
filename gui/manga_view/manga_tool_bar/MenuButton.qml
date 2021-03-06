import QtQuick 2.15
import QtQuick.Controls 2.15

// Menu button.
RoundButton {
    property alias menuButton: menuButton
    property alias filters: filters
    property alias menu: menu
    property alias menuCopyLink: menuCopyLink
    property alias menuFilter: menuFilter

    id: menuButton
    flat: true

    height: mangaToolBar.height
    width: height

    icon.source: "../../../resources/more_vert.svg"
    icon.color: iconColor
    icon.width: iconSize
    icon.height: iconSize

    onClicked: menu.open()

    Menu {
        id: menu

        MenuItem {
            id: menuCopyLink
            text: qsTr("Copy manga link")

            onTriggered: copy(mangaLink)
        }

        MenuItem {
            id: menuFilter
            text: qsTr("Filters")

            onTriggered: filters.open()
        }

        MenuItem {
            id: reloadMenu
            text: qsTr("Reload")

            onTriggered: {
                forced = true
                MangaViewer.set_manga_data(mangaLink, mangaSource, title, forced)
                forced = false
            }
        }
    }

    FilterMenu {id: filters}
}