"""Prueba del botón "Aplicar al sistema" (necesita pantalla, p. ej. xvfb-run).

Uso:  env -u WAYLAND_DISPLAY HOME=<tmp/home> xvfb-run -a python3 gui/tests/prueba_sistema.py <carpeta_tmp>
Trabaja en una copia del tema dentro de <carpeta_tmp> y con un "sistema" falso; 
la terminal y `sudo` se sustituyen por versiones de mentira que ejecutan el guion real.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# En pantalla virtual: sin esto GTK podría abrir la ventana en tu sesión Wayland real.
os.environ['GDK_BACKEND'] = 'x11'
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
import velo_gui
import velo_sistema

base = Path(sys.argv[1])
real = Path(__file__).resolve().parents[2]
tema = base / 'tema'
shutil.copytree(real, tema, ignore=shutil.ignore_patterns('gui', '*.bak*', '*.gui-bak-*', 'Epona.*', '.git*'))
conf = velo_gui.velo_conf.ConfFile(tema / 'configs' / 'default.conf')
for seccion in ('LockScreen', 'LoginScreen'):
    conf.set(seccion, 'background', 'default.jpg')
conf.guardar()
sistema = base / 'sistema' / 'velo'
sistema.parent.mkdir()
velo_sistema.DESTINO = sistema
n, _t = velo_sistema.crear_paquete(tema, base / 'previo.tar')      # instalación previa, como la de hoy
subprocess.run(['sh', '-c', velo_sistema.guion_root(sistema)], stdin=open(base / 'previo.tar', 'rb'), check=True)

# sudo de mentira: ejecuta el comando tal cual (o falla si existe el archivo "falla")
falso = base / 'bin'
falso.mkdir()
(falso / 'sudo').write_text(f'#!/bin/sh\n[ -e "{base}/falla" ] && exit 1\nexec "$@"\n')
(falso / 'sudo').chmod(0o755)
os.environ['PATH'] = f'{falso}:{os.environ["PATH"]}'
llamadas_terminal = []
# terminal de mentira: ejecuta el guion en el mismo proceso hijo, sin teclado
velo_sistema.comando_terminal = lambda guion: (llamadas_terminal.append(1), ['bash', '-c', 'exec 0</dev/null; ' + guion])[1]
registro = {'respuesta': Gtk.ResponseType.OK}
Gtk.MessageDialog.run = lambda self: registro['respuesta']    # el aviso previo se acepta o se cancela a mano

v = velo_gui.Ventana(tema)
v.show_all()
resultado = {'ok': False, 'detalle': ''}


_PRUEBAS = []


def pruebas_globales():
    return _PRUEBAS


def leer_tema():
    return velo_gui.velo_conf.ConfFile(tema / 'configs' / 'default.conf')


def leer_sistema():
    return velo_gui.velo_conf.ConfFile(sistema / 'configs' / 'default.conf')


def paso0():   # al abrir: todo al día
    assert 'al día' in v.estado.get_text(), v.estado.get_text()
    assert v.btn_sistema.get_sensitive()
    # el aviso previo se cancela: no se abre la terminal ni se guarda
    registro['respuesta'] = Gtk.ResponseType.CANCEL
    v.controles[('LockScreen.Clock', 'font-size')].spin.set_value(99)
    v.btn_sistema.emit('clicked')
    assert not llamadas_terminal and v._hay_cambios() and not v.ocupado
    # se acepta con un cambio sin guardar: guarda y luego lo lleva al sistema
    registro['respuesta'] = Gtk.ResponseType.OK
    v.btn_sistema.emit('clicked')
    GLib.timeout_add(6000, envolver(paso1))


def paso1():
    assert len(llamadas_terminal) == 1, llamadas_terminal
    assert leer_sistema().get('LockScreen.Clock', 'font-size') == '99', 'el cambio no llegó al sistema'
    assert 'Listo' in v.estado.get_text(), v.estado.get_text()
    assert not v._hay_cambios() and v.btn_sistema.get_sensitive() and not v.ocupado
    assert velo_sistema.diferencias(tema) == []
    # solo Aplicar (sin ir al sistema): avisa de que falta llevarlo
    v.controles[('LockScreen.Clock', 'font-size')].spin.set_value(88)
    v.btn_aplicar.emit('clicked')
    GLib.timeout_add(3000, envolver(paso2))


def paso2():
    assert leer_sistema().get('LockScreen.Clock', 'font-size') == '99', 'Aplicar no debe tocar el sistema'
    assert 'Aplicar al sistema' in v.estado.get_text(), v.estado.get_text()
    # contraseña mal puesta (sudo falla): lo dice y no cambia nada
    (base / 'falla').write_text('')
    v.btn_sistema.emit('clicked')
    GLib.timeout_add(6000, envolver(paso3))


def paso3():
    assert len(llamadas_terminal) == 2
    assert 'No se aplicó al sistema' in v.estado.get_text() and 'contraseña' in v.estado.get_text(), v.estado.get_text()
    assert leer_sistema().get('LockScreen.Clock', 'font-size') == '99'
    assert v.btn_sistema.get_sensitive() and v.btn_aceptar.get_sensitive() and not v.ocupado
    (base / 'falla').unlink()
    v.btn_sistema.emit('clicked')
    GLib.timeout_add(6000, envolver(paso4))


def paso4():
    assert leer_sistema().get('LockScreen.Clock', 'font-size') == '88'
    assert velo_sistema.diferencias(tema) == []
    assert not list(sistema.parent.glob('velo.*')), 'quedaron carpetas temporales'
    # Probar: el aviso se cancela, y con un cambio pendiente guarda y abre la prueba
    pruebas = _PRUEBAS
    velo_sistema.probar = lambda origen, segundos=300: (pruebas.append(str(origen)), (True, 'Prueba cerrada.'))[1]
    v.controles[('LockScreen.Clock', 'font-size')].spin.set_value(77)
    registro['respuesta'] = Gtk.ResponseType.CANCEL
    v.btn_probar.emit('clicked')
    assert not pruebas and v._hay_cambios(), 'cancelar no debe guardar ni probar'
    registro['respuesta'] = Gtk.ResponseType.OK
    v.btn_probar.emit('clicked')
    GLib.timeout_add(3500, envolver(paso5))


def paso5():
    assert len(pruebas_globales()) == 1
    assert leer_tema().get('LockScreen.Clock', 'font-size') == '77', 'Probar debe guardar antes lo pendiente'
    assert leer_sistema().get('LockScreen.Clock', 'font-size') == '88', 'Probar no debe tocar el sistema'
    assert 'Prueba cerrada' in v.estado.get_text(), v.estado.get_text()
    assert not v._hay_cambios() and v.btn_probar.get_sensitive() and not v.ocupado
    # sin cambios pendientes: va directo
    v.btn_probar.emit('clicked')
    GLib.timeout_add(2500, envolver(paso6))


def paso6():
    assert len(pruebas_globales()) == 2
    resultado.update(ok=True, detalle='aviso cancelado, guardar+enviar, solo Aplicar, contraseña fallida, reintento, probar')
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
