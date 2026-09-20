#!/usr/bin/env python3
"""Deja el repositorio git de Velo listo para subir a GitHub. No hace commit ni sube nada.

Qué hace:
  1. Crea el repositorio (rama main) si todavía no existe.
  2. Añade al índice de git una configuración NEUTRA (fondo de reserva, textos en inglés, nada
     personal) en lugar de tu configs/default.conf. Tu archivo no se toca: en `git status` seguirá
     saliendo como modificado, y eso es lo correcto (lo tuyo se queda solo en tu equipo).
  3. Añade el resto de archivos respetando .gitignore (sin vídeos, ni copias de seguridad).
  4. Revisa que no se cuele nada pesado ni con rutas o nombres personales.

Se puede ejecutar las veces que haga falta, antes de cada commit:  python3 gui/preparar_github.py
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import velo_conf      # noqa: E402
import velo_idiomas   # noqa: E402

CONF = 'configs/default.conf'
FORMATO_FECHA_EN = 'dddd, MMMM d, yyyy'
LIMITE_ARCHIVO = 1_500_000        # bytes; las fuentes (OFL) son lo único que se acerca
PROHIBIDO_EN_EL_CONTENIDO = ('/home/', 'jalkorta', 'jaealkorta', 'Alkorta')   # salvo en los README: allí van la autoría y la URL del repositorio
EXTENSIONES_PROHIBIDAS = ('.mp4', '.webm', '.mkv', '.avi', '.mov')


def git(*args, entrada=None, comprobar=True):
    r = subprocess.run(['git', '-C', str(RAIZ), *args], input=entrada, capture_output=True, text=True)
    if comprobar and r.returncode != 0:
        raise SystemExit(f'git {" ".join(args)} falló:\n{r.stderr.strip()}')
    return r.stdout


def configuracion_neutra():
    """Texto de configs/default.conf sin nada personal: fondo de reserva, textos y fechas en inglés."""
    c = velo_conf.ConfFile(RAIZ / CONF)
    for seccion in ('LockScreen', 'LoginScreen'):
        c.set(seccion, 'background', 'default.jpg')
    c.set('General', 'animated-background-placeholder', '')
    c.set('General', 'slideshow-interval', '60', texto=False)
    for seccion, clave, valor in velo_idiomas.claves('en_US', 'en'):
        c.set(seccion, clave, valor)
    for seccion in ('LockScreen.Date', 'LoginScreen.Date'):
        c.set(seccion, 'format', FORMATO_FECHA_EN)
    return '\n'.join(c.lineas) + '\n'


def main():
    if not (RAIZ / 'metadata.desktop').exists():
        raise SystemExit(f'{RAIZ} no parece la carpeta del tema Velo.')
    if not (RAIZ / '.git').exists():
        git('init', '-b', 'main')
        print('Repositorio creado (rama main).')

    git('add', '--all')
    blob = git('hash-object', '-w', '--stdin', entrada=configuracion_neutra()).strip()
    git('update-index', '--add', '--cacheinfo', f'100644,{blob},{CONF}')
    print(f'{CONF}: en el índice va la versión neutra; tu configuración personal no se ha tocado.')

    ficheros = [linea.split('\t', 1) for linea in git('ls-files', '-s').splitlines()]
    problemas = []
    for info, ruta in ficheros:
        objeto = info.split()[1]
        tamano = int(git('cat-file', '-s', objeto).strip())
        if tamano > LIMITE_ARCHIVO:
            problemas.append(f'{ruta}: pesa {tamano / 1e6:.1f} MB')
        if ruta.lower().endswith(EXTENSIONES_PROHIBIDAS):
            problemas.append(f'{ruta}: es un vídeo (no debe subirse)')
        if '.bak' in ruta or 'gui-bak' in ruta:
            problemas.append(f'{ruta}: es una copia de seguridad')
        contenido = subprocess.run(['git', '-C', str(RAIZ), 'cat-file', 'blob', objeto], capture_output=True).stdout
        for texto in PROHIBIDO_EN_EL_CONTENIDO:
            if texto.encode() in contenido and not ruta.startswith(('LICENSE', 'fonts/', 'README', 'gui/preparar_github.py')):
                problemas.append(f'{ruta}: contiene «{texto}»')
                break
    total = sum(int(git('cat-file', '-s', i.split()[1]).strip()) for i, _r in ficheros)
    print(f'{len(ficheros)} archivos preparados, {total / 1e6:.1f} MB en total.')
    if problemas:
        print('\nRevisa esto antes de subir:')
        print('\n'.join(f'  - {p}' for p in problemas))
        return 1
    print('Sin vídeos, copias ni datos personales.')
    identidad = git('config', 'user.email', comprobar=False).strip()
    print('\nSiguiente paso (lo haces tú, con tu nombre y correo):')
    if not identidad:
        print('  git config user.name  "Tu nombre"')
        print('  git config user.email "tu-correo@ejemplo.com"   # o el correo «noreply» que te da GitHub')
    print('  git commit -m "Velo: primera versión"')
    print('  git remote add origin https://github.com/TU-USUARIO/velo.git')
    print('  git push -u origin main')
    return 0


if __name__ == '__main__':
    sys.exit(main())
