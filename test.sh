#!/usr/bin/env bash
green='\033[0;32m'
red='\033[0;31m'
bred='\033[1;31m'
cyan='\033[0;36m'
grey='\033[2;37m'
reset="\033[0m"

: ${THEMES_DIR:=/usr/share/sddm/themes}

# Test for debug param ( debug | -debug | -d | --debug )
debug=0
if [[ "$1" =~ ^(debug|-debug|--debug|-d)$ ]]; then debug=1; fi
if [[ $debug -eq 0 ]]; then
    config_file=$(awk -F '=' '/^ConfigFile=/ {print $2}' metadata.desktop)
    echo -e "${green}Testing Velo theme...${reset}\nLoading config: ${config_file}\nDon't worry about the infinite loading, SDDM won't let you log in while in 'test-mode'."
fi

# Cada pantalla es una ventana; al cerrar una (Alt+F4) el tema escribe VELO_CERRAR_PRUEBA y se cierra todo.
pid_file=$(mktemp)
QT_IM_MODULE=qtvirtualkeyboard QML2_IMPORT_PATH=./components/ sddm-greeter-qt6 --test-mode --theme . 2> >(
    while IFS= read -r linea; do
        [[ $linea == *VELO_CERRAR_PRUEBA* ]] && kill "$(<"$pid_file")" 2>/dev/null
        [[ $debug -eq 1 ]] && echo "$linea" >&2
    done
) > /dev/null &
greeter_pid=$!
echo "$greeter_pid" > "$pid_file"
wait "$greeter_pid" 2>/dev/null
rm -f "$pid_file"

if [ ! -d "${THEMES_DIR}/velo" ]; then
    echo -e "\n${bred}[AVISO]: ${red}Velo todavía no está instalado como pantalla de inicio.${reset}"
    echo -e "Para instalarlo en Debian/Ubuntu con KDE: ${cyan}./install.sh${reset}   (primero puedes ver qué haría con ${cyan}./install.sh --simular${reset})"
fi
