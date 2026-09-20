"""Prueba de las páginas de parámetros nuevas y del marcador de vídeo (necesita pantalla: xvfb-run).

Uso:  env -u WAYLAND_DISPLAY HOME=<tmp/home> xvfb-run -a python3 gui/tests/prueba_paginas.py <carpeta_tmp>
Trabaja en una copia del tema dentro de <carpeta_tmp>; no toca el tema real. El tema resultante
queda en <carpeta_tmp>/tema por si se quiere abrir con sddm-greeter-qt6 --test-mode.
"""
import shutil
import subprocess
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# En pantalla virtual: sin esto GTK podría abrir la ventana en tu sesión Wayland real.
os.environ['GDK_BACKEND'] = 'x11'
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
import velo_gui

base = Path(sys.argv[1])
real = Path(__file__).resolve().parents[2]
tema = base / 'tema'
shutil.copytree(real, tema, ignore=shutil.ignore_patterns('gui', '*.bak*', '*.gui-bak-*', 'Epona.*', '.git*'))
# un vídeo pequeño de verdad como fondo
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc=size=640x360:rate=10:duration=3',
                '-pix_fmt', 'yuv420p', str(tema / 'backgrounds' / 'prueba.mp4')], check=True)
conf0 = velo_gui.velo_conf.ConfFile(tema / 'configs' / 'default.conf')
for seccion in ('LockScreen', 'LoginScreen'):
    conf0.set(seccion, 'background', 'prueba.mp4')
conf0.guardar()
conf_ruta = tema / 'configs' / 'default.conf'

v = velo_gui.Ventana(tema)
v.show_all()
resultado = {'ok': False, 'detalle': ''}


def leer():
    return velo_gui.velo_conf.ConfFile(conf_ruta)


def paso0():
    ids = ['general', 'fondos', 'idioma', 'bloqueo_hora_fecha', 'bloqueo_mensaje', 'bloqueo_efectos',
           'bloqueo_degradados', 'inicio_recuadro', 'inicio_hora_fecha', 'inicio_usuario', 'inicio_efectos',
           'inicio_degradado', 'inicio_botones']
    for pagina in ids:
        assert v.pila.get_child_by_name(pagina) is not None, pagina
    # el menú lateral: General, Fondo, Idioma, grupo Bloqueo (con sus páginas), grupo Inicio de sesión
    textos = [f.get_child().get_text() for f in v.menu.lista.get_children()]
    assert textos == ['General', 'Fondo', 'Idioma', 'BLOQUEO', 'Hora y fecha', 'Mensaje', 'Efectos del fondo',
                      'Degradados', 'INICIO DE SESIÓN', 'Recuadro', 'Hora y fecha', 'Usuario y contraseña',
                      'Efectos del fondo', 'Degradado inferior', 'Botones'], textos
    assert v.pila.get_visible_child_name() == 'fondos', 'al abrir debe verse el Fondo'
    assert v.menu.lista.get_selected_row() is v.menu.filas['fondos']
    v.menu.lista.select_row(v.menu.filas['inicio_efectos'])          # elegir en el menú cambia la página
    assert v.pila.get_visible_child_name() == 'inicio_efectos'
    v.pila.set_visible_child_name('general')                         # y al revés
    assert v.menu.lista.get_selected_row() is v.menu.filas['general']
    # los efectos del fondo están duplicados: cada pantalla con sus propios valores
    assert ('LockScreen', 'blur') in v.controles and ('LoginScreen', 'blur') in v.controles
    assert {pl['id'] for pl in v.plantillas} == {'minimalista', 'tarjeta', 'windows11'}
    assert leer().get('General', 'animated-background-placeholder', '') == ''
    assert v.btn_aplicar.get_sensitive(), 'con un vídeo y sin marcador debería haber algo que aplicar'
    c = v.controles
    fuente = c[('*', 'font-family')]
    assert fuente.valor() == 'Noto Sans', fuente.valor()
    fuente.poner('DejaVu Sans')
    fuente._avisar()
    c[('General', 'scale')].spin.set_value(1.1)
    c[('LockScreen.Message', 'position')].radios['top-center'].set_active(True)
    c[('LockScreen.Message', 'font-size')].spin.set_value(22)
    c[('LoginScreen.MenuArea.Power', 'display')].interruptor.set_active(False)
    c[('LoginScreen.MenuArea.Session', 'position')].radios['bottom-center'].set_active(True)
    assert not c[('LoginScreen.MenuArea.Session', 'position')].radios['center'].get_sensitive()
    c[('LockScreen', 'blur')].spin.set_value(12)
    c[('LockScreen', 'brightness')].spin.set_value(-0.25)
    c[('LockScreen.Scrim', 'top-opacity')].spin.set_value(0.8)
    c[('LoginScreen.MenuArea.Buttons', 'size')].spin.set_value(40)
    v.btn_aplicar.emit('clicked')
    GLib.timeout_add(6000, envolver(paso1))


def paso1():
    conf = leer()
    familias = [(s, conf.get(s, 'font-family')) for s in conf.secciones_con('font-family')]
    assert len(familias) > 10 and all(f == 'DejaVu Sans' for _s, f in familias), familias
    assert conf.get('General', 'scale') == '1.1'
    assert conf.get('LockScreen.Message', 'position') == 'top-center'
    assert conf.get('LockScreen.Message', 'font-size') == '22'
    assert conf.get('LoginScreen.MenuArea.Power', 'display') == 'false'
    assert conf.get('LoginScreen.MenuArea.Session', 'position') == 'bottom-center'
    assert conf.get('LockScreen', 'blur') == '12' and conf.get('LockScreen', 'brightness') == '-0.25'
    assert conf.get('LockScreen.Scrim', 'top-opacity') == '0.8'
    assert conf.get('LoginScreen.MenuArea.Buttons', 'size') == '40'
    marcador = conf.get('General', 'animated-background-placeholder')
    assert marcador == 'prueba-fotograma.jpg' and (tema / 'backgrounds' / marcador).stat().st_size > 1000, marcador
    assert not v._hay_cambios() and not v._param_cambiados(), v._param_cambiados()
    assert (tema / 'backgrounds' / marcador).exists() and (tema / 'backgrounds' / 'prueba.mp4').exists()
    # dejar de usar vídeo: el marcador sobra y se va a la papelera
    imagen = tema / 'backgrounds' / 'default.jpg'
    v._asignar('LockScreen', [imagen])
    v._asignar('LoginScreen', [imagen])
    assert v.btn_aplicar.get_sensitive()
    v.btn_aplicar.emit('clicked')
    GLib.timeout_add(6000, envolver(paso2))


def paso2():
    conf = leer()
    assert conf.get('General', 'animated-background-placeholder', 'x') == '', 'el marcador debía quedar vacío'
    assert not (tema / 'backgrounds' / 'prueba-fotograma.jpg').exists(), 'el marcador viejo debía irse a la papelera'
    assert not v._hay_cambios()
    # una plantilla rellena los ajustes de aspecto, pero no toca fondo, idioma ni fuente
    v._usar_plantilla(next(pl for pl in v.plantillas if pl['id'] == 'minimalista'))
    assert v.btn_aplicar.get_sensitive() and 'Minimalista' in v.estado.get_text()
    v.btn_aplicar.emit('clicked')
    GLib.timeout_add(3500, envolver(paso3))


def paso3():
    conf = leer()
    assert conf.get('LockScreen.Clock', 'position') == 'bottom-left'
    assert conf.get('LockScreen.Clock', 'font-weight') == '300'
    assert conf.get('LockScreen.Message', 'display') == 'false' and conf.get('LockScreen.Scrim', 'display') == 'false'
    assert conf.get('LoginScreen.Scrim', 'display') == 'false'
    assert conf.get('LockScreen.Clock', 'font-family') == 'DejaVu Sans', 'la plantilla no debe tocar la fuente'
    assert conf.get('LockScreen', 'background') == 'default.jpg', 'la plantilla no debe tocar el fondo'
    assert conf.get('General', 'scale') == '1.1', 'la plantilla no debe tocar la escala'
    assert not v._hay_cambios()
    resultado.update(ok=True, detalle='menú por grupos, páginas, fuente global, ajustes, marcador y plantilla')
    Gtk.main_quit()


def fallo(exc):
    resultado['detalle'] = repr(exc) + ' | estado: ' + v.estado.get_text()
    Gtk.main_quit()


def envolver(f):
    def g():
        try:
            f()
        except Exception:   # noqa: BLE001
            import traceback
            fallo(traceback.format_exc().strip().splitlines()[-3:])
        return False
    return g


GLib.timeout_add(3000, envolver(paso0))
GLib.timeout_add(60000, lambda: (fallo('tiempo agotado'), False)[1])
Gtk.main()
print('RESULTADO:', 'OK' if resultado['ok'] else 'FALLO', resultado['detalle'])
sys.exit(0 if resultado['ok'] else 1)
