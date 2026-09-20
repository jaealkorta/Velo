import QtQuick
import QtQuick.Layouts

// Hora y fecha encima de la foto de usuario en el inicio de sesión. En Velo vienen apagadas
// ([LoginScreen.Clock] y [LoginScreen.Date] display = false); si las dos lo están, no ocupa sitio.
ColumnLayout {
    id: header

    property date currentTime: new Date()

    visible: Config.loginClockDisplay || Config.loginDateDisplay
    spacing: Config.loginDateMarginTop
    anchors.top: parent.top
    anchors.horizontalCenter: parent.horizontalCenter

    Timer {
        interval: 1000
        repeat: true
        running: header.visible
        onTriggered: header.currentTime = new Date()
    }

    Text {
        visible: Config.loginClockDisplay
        Layout.alignment: Qt.AlignHCenter
        font.family: Config.loginClockFontFamily
        font.weight: Config.loginClockFontWeight
        font.pixelSize: Config.loginClockFontSize * Config.generalScale
        color: Config.loginClockColor
        style: Config.loginClockOutline ? Text.Outline : Text.Normal
        styleColor: Config.loginClockOutlineColor
        text: header.currentTime.toLocaleString(Qt.locale(Config.loginDateLocale), Config.loginClockFormat)
    }

    Text {
        visible: Config.loginDateDisplay
        Layout.alignment: Qt.AlignHCenter
        font.family: Config.loginDateFontFamily
        font.weight: Config.loginDateFontWeight
        font.pixelSize: Config.loginDateFontSize * Config.generalScale
        color: Config.loginDateColor
        style: Config.loginDateOutline ? Text.Outline : Text.Normal
        styleColor: Config.loginDateOutlineColor
        text: header.currentTime.toLocaleString(Qt.locale(Config.loginDateLocale), Config.loginDateFormat)
    }
}
