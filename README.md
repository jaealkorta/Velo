# Velo

*A personal SDDM login theme for KDE Plasma (Windows 11-style lock screen with video background). Derived from SilentSDDM. English summary at the end.*

## De dónde surge

Un velo es una cortina fina que cubre algo hasta que decides apartarla. Eso es esta pantalla: lo primero que ves al encender el ordenador, antes de entrar a tu escritorio.

Nació de una idea sencilla: la pantalla de inicio de Debian con KDE Plasma es funcional pero sosa, y quería algo parecido a la de Windows 11, pero mejor: con un vídeo de fondo, con la hora grande y limpia, y que se lea bien con cualquier fondo.

No empecé de cero. Velo parte de [SilentSDDM](https://github.com/uiriansan/SilentSDDM), un tema de código abierto de uiriansan. Yo lo he personalizado a mi gusto, y todo el mérito de la base es suyo.

## Para qué sirve

Es la pantalla que aparece antes de iniciar sesión. Tiene dos partes:

- **Pantalla de bloqueo:** el fondo (imagen, vídeo o pase de imágenes), la hora y la fecha en grande, y el mensaje «Pulse cualquier tecla».
- **Pantalla de inicio de sesión:** tu foto, tu nombre y el campo de contraseña, con los botones de sesión, teclado, idioma y apagado.

Es de uso personal. No busca vender nada ni ganar dinero.

## Cómo se cambia, en simple

Con una aplicación con ventanas y botones: **Configuraciones de VELO**. No hace falta editar ningún texto.

El menú de la izquierda va de lo general a lo concreto:

- **General:** tamaño de todo, animaciones, fuente y **plantillas** (puntos de partida: Windows 11, Tarjeta, Minimalista).
- **Fondo:** elegir un archivo (imagen o vídeo) o una carpeta de imágenes que cambian solas.
- **Bloqueo:** hora, fecha, mensaje, efectos del fondo (desenfoque, brillo, saturación) y degradados.
- **Inicio de sesión:** recuadro, hora y fecha, usuario y contraseña, efectos del fondo, degradado y botones.
- **Idioma:** por defecto el de tu sistema; se puede elegir otro.

Cada pantalla tiene sus propios valores: cambiar el desenfoque del bloqueo no toca el del inicio de sesión.

Al pulsar **Aplicar** se guarda en la carpeta del tema (siempre con copia de seguridad). Para que lo vea la pantalla de inicio de verdad, **Aplicar al sistema**: abre una terminal, pide tu contraseña de administrador (sin ella no se puede cambiar) y se cierra sola.

Por debajo, todo lo que se ve se decide en un archivo de texto: `configs/default.conf`. La aplicación solo lo edita por ti.

Para que la hora se lea sobre cualquier fondo, no uso sombras: pongo un degradado oscuro muy suave arriba y abajo.

## Instalarlo (Debian, Ubuntu y derivadas con KDE Plasma)

1. **Ver cómo queda sin instalar nada:** `./test.sh`
2. **Instalarlo:** `./install.sh` (con `./install.sh --simular` enseña lo que haría sin tocar nada). Instala los paquetes que falten, copia el tema a `/usr/share/sddm/themes/velo` y lo activa con un archivo aparte, `/etc/sddm.conf.d/velo.conf`, sin tocar la configuración de KDE.
3. **La aplicación en el menú:** `./gui/instalar_app.sh` (solo para tu usuario, sin permisos de administrador). Si no, se abre con `./velo-gui`.

Necesita Python 3 con GTK 3 (`python3-gi` y `gir1.2-gtk-3.0`) para la aplicación, y `ffmpeg` para las miniaturas de vídeo.

**Volver atrás:** `./install.sh --quitar`. Si la pantalla de inicio no llegara a verse, desde otra consola (`Ctrl+Alt+F3`): `sudo rm /etc/sddm.conf.d/velo.conf`.

Antes de reiniciar, prueba siempre con `./test.sh`. Si no, podrías quedarte con una pantalla de inicio rota.

## Los fondos

Se admiten imágenes (jpg, png) y vídeos (mp4, webm, mkv, mov, avi). El tema solo puede leer los que están en su carpeta `backgrounds/`, así que la aplicación los copia allí al aplicar (el sistema de inicio de sesión no puede leer tu carpeta personal).

Para una pantalla de inicio conviene un vídeo ligero: 1080p, 30 fps y pocos megas. Con uno pesado tarda en arrancar.

**Este repositorio no incluye ningún vídeo ni imagen de fondo** salvo una de reserva (`backgrounds/default.jpg`): cada uno pone los suyos.

## Cómo está hecho

Para que cambiar una parte no rompa otra:

- `Main.qml` monta las dos pantallas y el fondo; `components/` tiene las piezas (`LockScreen`, `LoginScreen`, `LoginCard`, `LoginHeader`, `Scrim`, botones…).
- `configs/default.conf` es la configuración; `configs/presets/` guarda las plantillas.
- `gui/` es la aplicación (Python + GTK 3). Tiene pruebas en `gui/tests/`.

## A dónde voy

Hecho: pantalla de bloqueo estilo Windows 11 con vídeo, inicio de sesión limpio, aplicación de configuración completa con plantillas, idiomas y «Aplicar al sistema».

Ideas para más adelante: aligerar el vídeo de ejemplo y revisar las traducciones (las hizo una máquina, sin revisión de personas nativas; las de euskera, francés, alemán, etc. pueden tener errores).

## English summary

Velo is a personal SDDM theme for KDE Plasma 6 on Debian/Ubuntu: a Windows 11-style lock screen (big clock, date, "Press any key") over an image, a video or an image slideshow, with soft dark gradients so the text stays readable, and a clean login screen. It comes with a GTK 3 configuration app ("Configuraciones de VELO", Spanish UI) that edits everything without touching text files, ships three presets, and translates the theme's texts into the 43 languages SDDM supports (machine-written, unreviewed).

Install: `./test.sh` to preview, `./install.sh` (Debian/Ubuntu; `--simular` for a dry run, `--quitar` to remove it). The repository contains no videos and no wallpapers apart from a fallback image.

## Créditos y licencia

Velo es una versión modificada de SilentSDDM 1.5.0, de uiriansan, y usa la misma licencia: GPL-3.0-or-later. Puedes usarlo, cambiarlo y compartirlo con quien quieras, siempre que mantengas esa licencia y el crédito al autor original. Los detalles están en `NOTICE` y `LICENSE`.

Las fuentes de `fonts/` (Red Hat) van con su licencia SIL Open Font License (`fonts/OFL.txt`).
