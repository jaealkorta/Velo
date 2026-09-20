import QtQuick

// Recuadro translúcido detrás de la zona de inicio de sesión (foto, nombre y contraseña).
// Se dibuja solo si [LoginScreen.Card] display = true. LoginScreen.qml le pasa las tres piezas
// sobre las que se dimensiona; no necesita saber nada más de la pantalla.
Rectangle {
    id: card

    required property Item container   // se centra sobre él y copia su escala (la animación de entrada)
    required property Item content     // bloque del nombre y la contraseña: fija el ancho mínimo
    required property Item header      // hora y fecha (pueden estar apagadas)

    visible: Config.cardDisplay
    anchors.horizontalCenter: container.horizontalCenter
    anchors.verticalCenter: container.verticalCenter
    width: Math.max(content.width, Config.avatarActiveSize * Config.generalScale, header.visible ? header.width : 0) + 2 * Config.cardPaddingX * Config.generalScale
    height: container.height + 2 * Config.cardPaddingY * Config.generalScale
    radius: Config.cardRadius * Config.generalScale
    color: Qt.rgba(Config.cardColor.r, Config.cardColor.g, Config.cardColor.b, Config.cardOpacity)
    border.width: Config.cardBorderSize * Config.generalScale
    border.color: Config.cardBorderColor
    scale: container.scale
}
