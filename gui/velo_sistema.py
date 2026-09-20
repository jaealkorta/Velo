"""Puente entre la copia de trabajo de Velo y la que lee SDDM (/usr/share/sddm/themes/velo).

Cambiar esa carpeta exige permisos de administrador. La GUI empaqueta el tema (como usuario),
abre una terminal y allí ejecuta `sudo`; el usuario solo escribe la contraseña. Lo que corre como
root son herramientas del sistema (tar, mv...) que leen el paquete: nunca un script de tu carpeta.
"""
import fnmatch
import os
import shlex
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

DESTINO = Path('/usr/share/sddm/themes/velo')
# Lo que NO va al sistema: el editor gráfico, las capturas de la documentación, los scripts y las copias.
EXCLUIR_RAIZ = {'gui', 'docs', 'install.sh', 'instalar_app.sh', 'test.sh', 'velo-gui', '.git', '.gitignore'}
EXCLUIR_PATRONES = ('*.bak*', '*.gui-bak-*', '__pycache__', '*.pyc', '.velo-*', '*~')
MAX_BYTES = 500 * 1024 * 1024
LIMITE_LECTURA = 1_048_576      # por encima de esto, al comparar se mira solo tamaño y fecha
TITULO_TERMINAL = 'Velo — permiso de administrador'


class ErrorVelo(Exception):
    pass


def excluido(rel):
    partes = Path(rel).parts
    return partes[0] in EXCLUIR_RAIZ or any(fnmatch.fnmatch(p, pat) for p in partes for pat in EXCLUIR_PATRONES)


def archivos(origen):
    """Rutas relativas de los archivos del tema que van al sistema (sin enlaces simbólicos)."""
    origen = Path(origen)
    for raiz, dirs, nombres in os.walk(origen):
        rel_raiz = Path(raiz).relative_to(origen)
        dirs[:] = sorted(d for d in dirs if not excluido(rel_raiz / d) and not (Path(raiz) / d).is_symlink())
        for nombre in sorted(nombres):
            rel = rel_raiz / nombre
            ruta = origen / rel
            if not excluido(rel) and not ruta.is_symlink() and ruta.is_file():
                yield rel


def _clave(carpeta, clave, defecto=None):
    try:
        for linea in (Path(carpeta) / 'metadata.desktop').read_text(encoding='utf-8').splitlines():
            if linea.startswith(clave + '='):
                return linea.split('=', 1)[1].strip()
    except OSError:
        pass
    return defecto


def crear_paquete(origen, ruta_tar):
    """Empaqueta el tema en un .tar (solo archivos normales, dueño root, permisos 644).

    Devuelve (número de archivos, bytes). Lanza ErrorVelo si la carpeta no es un tema Velo completo.
    """
    origen = Path(origen).resolve()
    if _clave(origen, 'Theme-Id') != 'velo' or not (origen / 'Main.qml').is_file():
        raise ErrorVelo(f'No parece una carpeta del tema Velo: {origen}')
    lista = list(archivos(origen))
    if _clave(origen, 'ConfigFile', 'configs/default.conf') != 'configs/default.conf' \
            or Path('configs/default.conf') not in lista:
        raise ErrorVelo('Falta configs/default.conf: no se instala un tema sin configuración.')
    total = sum((origen / r).stat().st_size for r in lista)
    if total > MAX_BYTES:
        raise ErrorVelo(f'El tema pesa {total // 1048576} MB; el límite es {MAX_BYTES // 1048576} MB.')

    def normalizar(info):
        info.uid = info.gid = 0
        info.uname = info.gname = 'root'
        info.mode = 0o644
        return info

    with tarfile.open(ruta_tar, 'w') as paquete:
        for rel in lista:
            paquete.add(origen / rel, arcname=str(rel), recursive=False, filter=normalizar)
    return len(lista), total


def guion_root(destino=DESTINO):
    """Guion de shell que se ejecuta como root: lee el paquete por la entrada estándar.

    Deja la copia nueva al lado y la cambia de golpe; si algo falla antes, lo instalado no se toca.
    """
    d = shlex.quote(str(destino))
    return f'''set -e
D={d}
rm -rf "$D.nuevo" "$D.anterior"
mkdir -m 755 "$D.nuevo"
tar -xf - -C "$D.nuevo" --no-same-owner --no-same-permissions
find "$D.nuevo" -type d -exec chmod 755 {{}} +
test -f "$D.nuevo/Main.qml" -a -f "$D.nuevo/configs/default.conf"
if [ -e "$D" ]; then mv "$D" "$D.anterior"; fi
mv "$D.nuevo" "$D" || {{ if [ -e "$D.anterior" ]; then mv "$D.anterior" "$D"; fi; exit 1; }}
rm -rf "$D.anterior"
'''


def guion_terminal(ruta_tar, destino=DESTINO):
    """Lo que se ve y se ejecuta dentro de la terminal (bash)."""
    return f'''clear
echo "Velo · actualizar la pantalla de inicio de sesión"
echo
echo "Cambiar la pantalla de inicio necesita permiso de administrador."
echo "Escribe tu contraseña (no se ve mientras escribes) y pulsa Intro."
echo "Esta ventana se cerrará sola cuando termine."
echo
if sudo sh -c {shlex.quote(guion_root(destino))} < {shlex.quote(str(ruta_tar))}; then
    echo
    echo "Listo."
    sleep 1
else
    echo
    echo "No se ha podido actualizar la pantalla de inicio. Pulsa Intro para cerrar."
    read -r _
    exit 1
fi
'''


def _terminal_preferida():
    try:
        r = subprocess.run(['kreadconfig6', '--file', 'kdeglobals', '--group', 'General',
                            '--key', 'TerminalApplication'], capture_output=True, text=True, timeout=5)
        return r.stdout.strip().split()[0] if r.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def comando_terminal(guion):
    """argv para abrir la terminal por defecto del equipo y ejecutar `guion` con bash.

    Orden: la de KDE (Configuración > Aplicaciones predeterminadas), la del sistema
    (x-terminal-emulator en Debian) y, si no, la primera conocida que haya instalada.
    """
    preferida = _terminal_preferida()
    for nombre in ([preferida] if preferida else []) + ['x-terminal-emulator', 'kitty', 'konsole', 'xterm']:
        ruta = shutil.which(nombre)
        if not ruta:
            continue
        base = os.path.basename(os.path.realpath(ruta))
        if base == 'kitty':
            return [ruta, '--title', TITULO_TERMINAL, '-o', 'initial_window_width=84c',
                    '-o', 'initial_window_height=16c', 'bash', '-c', guion]
        if base == 'xterm':
            return [ruta, '-T', TITULO_TERMINAL, '-e', 'bash', '-c', guion]
        if base in ('gnome-terminal', 'kgx', 'gnome-console'):
            return [ruta, '--', 'bash', '-c', guion]
        if base == 'xfce4-terminal':
            return [ruta, '-T', TITULO_TERMINAL, '-x', 'bash', '-c', guion]
        return [ruta, '-e', 'bash', '-c', guion]
    return None


def _iguales(a, b):
    try:
        sa, sb = a.stat(), b.stat()
    except OSError:
        return False
    if sa.st_size != sb.st_size:
        return False
    if sa.st_size > LIMITE_LECTURA:
        return int(sa.st_mtime) == int(sb.st_mtime)
    return a.read_bytes() == b.read_bytes()


def diferencias(origen, destino=None):
    """Lista de (motivo, ruta) entre la copia de trabajo y la instalada.

    motivo: 'nuevo' (falta en el sistema), 'cambiado' o 'sobra' (está en el sistema y ya no en el tema).
    Devuelve None si el tema no está instalado.
    """
    origen = Path(origen)
    destino = Path(destino or DESTINO)
    if not destino.is_dir():
        return None
    propios = set(archivos(origen))
    salida = []
    for rel in sorted(propios):
        d = destino / rel
        if not d.exists():
            salida.append(('nuevo', str(rel)))
        elif not _iguales(origen / rel, d):
            salida.append(('cambiado', str(rel)))
    for archivo in sorted(p for p in destino.rglob('*') if p.is_file() or p.is_symlink()):
        rel = archivo.relative_to(destino)
        if rel not in propios:
            salida.append(('sobra', str(rel)))
    return salida


def texto_estado(diffs):
    if diffs is None:
        return 'Velo aún no está instalado en el sistema.'
    if not diffs:
        return 'La pantalla de inicio del sistema está al día.'
    return f'Hay {len(diffs)} cambio(s) que todavía no están en la pantalla de inicio: pulsa «Aplicar al sistema».'


def aplicar(origen):
    """Empaqueta el tema, abre la terminal con sudo y espera. Devuelve (ok, mensaje)."""
    trabajo = Path(tempfile.mkdtemp(prefix='velo-', dir=os.environ.get('XDG_RUNTIME_DIR') or None))
    try:
        try:
            n, _total = crear_paquete(origen, trabajo / 'tema.tar')
        except (ErrorVelo, OSError) as e:
            return False, str(e)
        argv = comando_terminal(guion_terminal(trabajo / 'tema.tar', DESTINO))
        if argv is None:
            return False, 'No encuentro ninguna terminal (la predeterminada de KDE, kitty, konsole, xterm) para pedir la contraseña.'
        try:
            subprocess.run(argv, check=False)
        except OSError as e:
            return False, f'No se pudo abrir la terminal: {e}'
        diffs = diferencias(origen)
        if diffs == []:
            return True, f'{n} archivos'
        return False, 'La pantalla de inicio no se actualizó (¿contraseña incorrecta o ventana cerrada?).'
    finally:
        shutil.rmtree(trabajo, ignore_errors=True)
