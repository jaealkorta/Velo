# Velo

**Tema de inicio de sesión (SDDM) para KDE Plasma con una pantalla de bloqueo al estilo Windows 11: reloj grande, degradados suaves y un vídeo, una imagen o un pase de imágenes como fondo. Incluye una aplicación gráfica para configurarlo sin editar archivos de texto.**

![Pantalla de bloqueo](docs/img/lock.jpg)

| Inicio de sesión | Inicio de sesión, plantilla «Tarjeta» |
|---|---|
| ![Inicio de sesión](docs/img/login.jpg) | ![Inicio de sesión con tarjeta](docs/img/login-card.jpg) |

*Capturas realizadas con el modo de prueba del propio tema (`sddm-greeter-qt6 --test-mode`) sobre un fondo generado.*

## Descripción

El nombre alude a un velo: una cortina fina que cubre algo hasta que se aparta. Es lo que hace esta pantalla con el escritorio.

Velo parte de [SilentSDDM](https://github.com/uiriansan/SilentSDDM) 1.5.0, de uiriansan, y lo adapta a un uso concreto: una pantalla de bloqueo limpia, inspirada en la de Windows 11, que se lea bien sobre cualquier fondo y que se pueda configurar cómodamente.

Consta de dos pantallas:

- **Bloqueo:** fondo, hora y fecha en grande y el mensaje «Pulse cualquier tecla».
- **Inicio de sesión:** foto, nombre de usuario y contraseña, con los botones de sesión, teclado, idioma y apagado.

## Características

- **Legibilidad sobre cualquier fondo:** en lugar de sombras, degradados oscuros muy suaves en los bordes superior e inferior.
- **Fondos:** imagen, vídeo (mp4, webm, mkv…) o una carpeta de imágenes que rotan automáticamente. Desenfoque, brillo y saturación independientes para cada pantalla.
- **Aplicación de configuración** («Configuraciones de VELO»): páginas General, Fondo e Idioma, y un grupo de páginas para cada pantalla (Bloqueo e Inicio de sesión). Escribe la configuración y conserva siempre una copia de seguridad.
- **Plantillas:** Windows 11, Tarjeta y Minimalista.
- **43 idiomas** para los textos propios del tema. Los nombres de días y meses los aporta Qt.
- **Estructura modular:** `Scrim`, `LoginCard`, `LoginHeader` y el resto de piezas son archivos QML independientes, de modo que modificar uno no afecta a los demás.

## Requisitos

- SDDM 0.21 o superior con Qt 6, y KDE Plasma.
- Para el instalador: Debian, Ubuntu o derivadas (`apt`). En otras distribuciones, la instalación es manual (véase [Estructura](#estructura-del-proyecto)).
- Para la aplicación: Python 3 con GTK 3 (`python3-gi` y `gir1.2-gtk-3.0`) y `ffmpeg` (miniaturas de vídeo).

## Instalación

```bash
git clone https://github.com/jaealkorta/Velo.git
cd Velo
./test.sh                # previsualiza el tema sin instalar nada
./install.sh --simular   # muestra lo que haría el instalador, sin ejecutar nada
./install.sh             # instala y activa el tema
./instalar_app.sh        # opcional: añade la aplicación al menú de aplicaciones
```

El instalador añade los paquetes que falten, copia el tema a `/usr/share/sddm/themes/velo` y lo activa mediante un archivo independiente, `/etc/sddm.conf.d/velo.conf`, sin modificar la configuración propia de KDE.

Conviene dejar la carpeta en un sitio fijo (por ejemplo, `~/Programas/Velo`) y no en Descargas: el icono del menú y la aplicación apuntan a ella. Si la mueves, vuelve a ejecutar `./instalar_app.sh` para que apunte al sitio nuevo.

**Desinstalación:** `./install.sh --quitar`. Si la pantalla de inicio no llegara a mostrarse, desde otra consola (`Ctrl+Alt+F3`): `sudo rm /etc/sddm.conf.d/velo.conf`.

> Se recomienda ejecutar siempre `./test.sh` antes de reiniciar: un tema defectuoso puede dejar la pantalla de inicio inutilizable.

## Aplicación de configuración

Se abre desde el menú de aplicaciones o con `./velo-gui`.

![Aplicación de configuración: General](docs/img/gui-general.png)

- **Probar** abre una vista previa de la pantalla de bloqueo y de inicio de sesión con los ajustes guardados (los pendientes se guardan antes). No permite iniciar sesión. Se cierra con `Alt+F4` o la tecla Meta (Windows), y sola a los 5 minutos.
- **Aplicar** guarda los cambios en la carpeta del tema y crea una copia de seguridad de la configuración.
- **Aplicar al sistema** copia el tema a la carpeta que lee SDDM. Esa operación requiere permisos de administrador: la aplicación lo indica, abre una terminal donde se introduce la contraseña y la cierra al terminar. Con permisos de administrador solo se ejecutan herramientas del sistema (`tar`, `mv`, etc.) que leen un paquete preparado por la aplicación.
- Los fondos se copian a la carpeta `backgrounds/` del tema, porque la pantalla de inicio no puede acceder al directorio personal del usuario.

Todo lo que hace la aplicación queda en un único archivo de texto, `configs/default.conf`, que también puede editarse a mano. Las plantillas están en `configs/presets/` como archivos de configuración parciales.

## Fondos

Se admiten imágenes (jpg, png) y vídeos (mp4, webm, mkv, mov, avi). Para una pantalla de inicio se recomienda un vídeo ligero: 1080p, 30 fps y pocos megabytes.

**Este repositorio no incluye vídeos ni fondos de pantalla**, salvo una imagen de reserva (`backgrounds/default.jpg`).

## Estructura del proyecto

- `Main.qml` monta las dos pantallas y el fondo; `components/` contiene las piezas.
- `configs/default.conf` es la configuración. Solo tienen efecto las claves que lee `components/Config.qml`.
- `gui/` contiene la aplicación (Python y GTK 3) y sus pruebas (`gui/tests/`). Las pruebas de ventana requieren un servidor gráfico virtual; las instrucciones figuran en la cabecera de cada archivo.
- Instalación manual: copiar la carpeta (sin `gui/`, `docs/` ni los scripts) a `/usr/share/sddm/themes/velo`, establecer `Current=velo` en un archivo de `/etc/sddm.conf.d/` y definir en `GreeterEnvironment` las variables `QML2_IMPORT_PATH=/usr/share/sddm/themes/velo/components/` y `QT_IM_MODULE=qtvirtualkeyboard`.

## Desarrollo y pruebas

Toda la modificación realizada sobre SilentSDDM (cambios en QML, aplicación de configuración, instalador, plantillas, traducciones, pruebas y documentación) ha sido realizada **al 100 % por Claude Code** (Anthropic).

El tema está probado: cuenta con pruebas automáticas, con verificación del renderizado del tema mediante el modo de prueba de SDDM y con comprobación en un equipo real (Debian 13, KDE Plasma 6.3, Wayland). No se ha probado en otras distribuciones ni entornos.

Las traducciones de los textos del tema son de generación automática y no han sido revisadas por hablantes nativos, por lo que pueden contener errores.

## Créditos y licencia

Velo es una versión modificada de SilentSDDM 1.5.0, obra de uiriansan y sus colaboradores, y se distribuye bajo la misma licencia: **GPL-3.0-or-later**. Se puede usar, modificar y compartir siempre que se mantenga esa licencia y el reconocimiento al autor original. Los detalles figuran en `NOTICE` y `LICENSE`.

Las fuentes de `fonts/` (Red Hat) se distribuyen con su propia licencia, SIL Open Font License (`fonts/OFL.txt`).
