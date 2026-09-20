#!/usr/bin/env bash
# Convierte "Configuraciones de VELO" en una aplicación más del sistema.
#
#   ./instalar_app.sh            pone "Configuraciones de VELO" (con su icono) en el menú de aplicaciones
#   ./instalar_app.sh --quitar   lo quita
#
# No necesita permisos de administrador: solo toca tu usuario (~/.local/share).
# "Aplicar al sistema" no necesita nada instalado: pide la contraseña en una terminal cuando se usa.
# Si mueves la carpeta de Velo, vuelve a ejecutarlo para que el icono apunte al sitio nuevo.
set -euo pipefail

AQUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TEMA=$AQUI
DATOS=${XDG_DATA_HOME:-$HOME/.local/share}
LANZADOR="$DATOS/applications/velo.desktop"
ICONO="$DATOS/icons/hicolor/scalable/apps/velo.svg"

if [[ $EUID -eq 0 ]]; then
    echo "No lo ejecutes como administrador: se instalaría el icono en la cuenta de root." >&2
    exit 1
fi

refrescar_menu() {
    command -v update-desktop-database >/dev/null && update-desktop-database "$DATOS/applications" 2>/dev/null || true
    command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 >/dev/null 2>&1 || true
}

if [[ "${1:-}" == "--quitar" ]]; then
    rm -f "$LANZADOR" "$ICONO"
    refrescar_menu
    echo "Quitado el icono del menú. La pantalla de inicio instalada no se ha tocado."
    exit 0
fi

mkdir -p "$DATOS/applications" "$(dirname "$ICONO")"
install -m 644 "$AQUI/gui/velo.svg" "$ICONO"
cat > "$LANZADOR" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Configuraciones de VELO
GenericName=Pantalla de inicio de sesión
Comment=Personaliza la pantalla de bloqueo y de inicio de sesión (Velo)
Exec="$TEMA/velo-gui"
Icon=velo
Terminal=false
Categories=Settings;DesktopSettings;
Keywords=velo;sddm;login;inicio;bloqueo;fondo;pantalla;
StartupWMClass=velo-gui
DESKTOP
chmod 644 "$LANZADOR"
refrescar_menu
echo "Listo: 'Configuraciones de VELO' ya está en el menú de aplicaciones."

