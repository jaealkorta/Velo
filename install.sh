#!/usr/bin/env bash
# Instala Velo como pantalla de inicio de sesión (SDDM) en Debian, Ubuntu o derivadas con KDE Plasma.
#
#   ./install.sh             instala Velo y lo activa
#   ./install.sh --simular   enseña lo que haría, sin tocar nada
#   ./install.sh --quitar    quita Velo y vuelve al tema anterior
#
# Pide la contraseña (sudo) cuando hace falta. No lo ejecutes ya con sudo.
# Antes de reiniciar, prueba el tema sin instalar: ./test.sh
set -euo pipefail

AQUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DESTINO=/usr/share/sddm/themes/velo
AJUSTES=/etc/sddm.conf.d/velo.conf
# Lo que NO va a la carpeta del sistema: el editor gráfico, los scripts y las copias de seguridad.
EXCLUIR=(--exclude=./gui --exclude=./docs --exclude=./install.sh --exclude=./test.sh --exclude=./velo-gui
         --exclude=./.git --exclude=./.gitignore --exclude='*.bak*' --exclude='*.gui-bak-*'
         --exclude=__pycache__ --exclude='*.pyc' --exclude='.velo-*' --exclude='*~')
PAQUETES=(sddm qml6-module-qtquick-effects qml6-module-qtquick-controls qml6-module-qtquick-layouts
          qml6-module-qtquick-templates qml6-module-qtquick-window qml6-module-qtmultimedia
          qml6-module-qtquick-virtualkeyboard qt6-virtualkeyboard-plugin libqt6svg6 qt6-svg-plugins
          qt6-image-formats-plugins)

SIMULAR=0
case "${1:-}" in
    "" ) ;;
    --simular) SIMULAR=1 ;;
    --quitar) ;;
    *) echo "Opción desconocida: $1 (usa --simular o --quitar)" >&2; exit 1 ;;
esac

if [[ $EUID -eq 0 ]]; then
    echo "No lo ejecutes como administrador: pide la contraseña él solo cuando hace falta." >&2
    exit 1
fi

ejecutar() {   # enseña el comando y, si no es una simulación, lo ejecuta
    echo "  \$ $*"
    [[ $SIMULAR -eq 1 ]] || "$@"
}

if [[ "${1:-}" == "--quitar" ]]; then
    echo "Quitando Velo…"
    ejecutar sudo rm -f "$AJUSTES"
    ejecutar sudo rm -rf "$DESTINO" "$DESTINO.nuevo" "$DESTINO.anterior"
    echo "Hecho. SDDM vuelve al tema que tuvieras antes (en KDE, el de /etc/sddm.conf.d/kde_settings.conf)."
    exit 0
fi

[[ -f "$AQUI/metadata.desktop" && -f "$AQUI/Main.qml" ]] || { echo "Esto no parece la carpeta del tema Velo." >&2; exit 1; }
command -v apt-get >/dev/null || { echo "Este instalador es para Debian/Ubuntu (apt). En otra distribución, mira el README." >&2; exit 1; }

echo "1. Paquetes que necesita el tema"
FALTAN=()
for paquete in "${PAQUETES[@]}"; do
    dpkg -s "$paquete" >/dev/null 2>&1 || FALTAN+=("$paquete")
done
if ((${#FALTAN[@]})); then
    ejecutar sudo apt-get install -y "${FALTAN[@]}"
else
    echo "  ya están todos instalados"
fi

ENLACES=$(find "$AQUI" \( -path "$AQUI/gui" -o -path "$AQUI/.git" \) -prune -o -type l -print)
if [[ -n "$ENLACES" ]]; then
    echo "El tema tiene enlaces simbólicos y no se copian por seguridad; quítalos o cámbialos por archivos:" >&2
    echo "$ENLACES" >&2
    exit 1
fi

echo "2. Copiando el tema a $DESTINO"
# Se prepara al lado y se cambia de golpe: si algo falla antes, el tema instalado sigue intacto.
NUEVO=$DESTINO.nuevo
ejecutar sudo rm -rf "$NUEVO" "$DESTINO.anterior"
ejecutar sudo install -d -m 755 "$NUEVO"
if [[ $SIMULAR -eq 1 ]]; then
    echo "  \$ tar -C $AQUI ${EXCLUIR[*]} -cf - . | sudo tar -C $NUEVO --no-same-owner -xf -"
else
    tar -C "$AQUI" "${EXCLUIR[@]}" -cf - . | sudo tar -C "$NUEVO" --no-same-owner -xf -
fi
ejecutar sudo chmod -R a+rX "$NUEVO"
ejecutar sudo sh -c "if [ -e '$DESTINO' ]; then mv '$DESTINO' '$DESTINO.anterior'; fi; mv '$NUEVO' '$DESTINO'; rm -rf '$DESTINO.anterior'"

echo "3. Activándolo ($AJUSTES)"
# Un archivo aparte, que SDDM lee después de kde_settings.conf: no se toca la configuración de KDE.
IDIOMA=${LC_ALL:-${LANG:-}}
ENTORNO="QML2_IMPORT_PATH=$DESTINO/components/,QT_IM_MODULE=qtvirtualkeyboard"
if [[ -n "$IDIOMA" && "$IDIOMA" != C* && "$IDIOMA" != POSIX* ]]; then
    ENTORNO+=",LANG=$IDIOMA"     # los textos propios de SDDM (Contraseña, Apagar…) salen en tu idioma
fi
CONTENIDO=$(printf '[Theme]\nCurrent=velo\n\n[General]\nInputMethod=qtvirtualkeyboard\nGreeterEnvironment=%s\n' "$ENTORNO")
if [[ -f "$AJUSTES" ]]; then
    ejecutar sudo cp -a "$AJUSTES" "$AJUSTES.bak"
fi
if [[ $SIMULAR -eq 1 ]]; then
    echo "  escribiría en $AJUSTES:"; sed 's/^/    /' <<<"$CONTENIDO"
else
    sudo install -d -m 755 /etc/sddm.conf.d
    printf '%s\n' "$CONTENIDO" | sudo tee "$AJUSTES" >/dev/null
fi

echo
echo "Listo. Verás Velo la próxima vez que cierres sesión o reinicies."
echo "Si algo sale mal: ./install.sh --quitar  (o, desde otra consola con Ctrl+Alt+F3: sudo rm $AJUSTES)"
