import QtQuick

// Degradado suave pegado al borde de arriba o de abajo de la pantalla: oscurece un poco el fondo
// para que el texto se lea sobre cualquier imagen o vídeo. Lo usan el bloqueo (arriba y abajo)
// y el inicio de sesión (abajo).
Rectangle {
    id: scrim

    property string edge: "bottom"   // "top" | "bottom"
    property color tint: "#000000"   // color del degradado
    property real strength: 0.4      // opacidad en el borde (0 = invisible, 1 = sólido)
    property real extent: 0.25       // altura, como fracción de la pantalla

    readonly property bool atTop: edge === "top"

    anchors.left: parent.left
    anchors.right: parent.right
    anchors.top: atTop ? parent.top : undefined
    anchors.bottom: atTop ? undefined : parent.bottom
    height: parent.height * extent

    gradient: Gradient {
        GradientStop { position: 0.0; color: Qt.rgba(scrim.tint.r, scrim.tint.g, scrim.tint.b, scrim.atTop ? scrim.strength : 0.0) }
        GradientStop { position: 1.0; color: Qt.rgba(scrim.tint.r, scrim.tint.g, scrim.tint.b, scrim.atTop ? 0.0 : scrim.strength) }
    }
}
