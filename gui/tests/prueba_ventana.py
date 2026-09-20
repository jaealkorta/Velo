"""Prueba de humo de la ventana (necesita pantalla, p. ej. xvfb-run).

Uso (con HOME temporal para no tocar el real):
  HOME=<tmp/home> env -u WAYLAND_DISPLAY xvfb-run -a -s "-screen 0 1280x900x24" \
      python3 gui/tests/prueba_ventana.py <tema_tmp> <carpeta_fuentes> <video_original>
La carpeta temporal debe estar en el mismo disco que ~/.local/share/Trash (p. ej. ~/.cache)
La carpeta de fuentes debe tener al menos dos imágenes.
Nota: en xvfb las capturas hechas desde dentro del proceso salen negras; para ver el aspecto,
lanza velo_gui.py aparte y captura con `import -window root`.
"""
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
import velo_media

tema, fuentes = Path(sys.argv[1]), Path(sys.argv[2])
# argv[3]: ruta del vídeo original al que apunta el enlace Epona.mp4 del tema de prueba
conf = tema / 'configs' / 'default.conf'
imagenes = [p for p in velo_media.listar(fuentes) if velo_media.tipo(p) == 'imagen']
assert len(imagenes) >= 2, 'hacen falta 2 imágenes de prueba'
A, B = imagenes[:2]

v = velo_gui.Ventana(tema)
cerrada = {'si': False}
v.connect('destroy', lambda _w: (cerrada.update(si=True), Gtk.main_quit()))
v.show_all()
resultado = {'ok': False, 'detalle': ''}


def leer():
    return velo_gui.velo_conf.ConfFile(conf)


def paso0():   # con el .conf de siempre, los textos del tema aún no están en el idioma del sistema
    assert v.btn_aplicar.get_sensitive(), 'debería haber ajustes de idioma pendientes al abrir'
    pendientes = {(sec, clave): valor for sec, clave, valor, _q in v._idioma_cambios()}
    assert pendientes[('LoginScreen.LoginArea.Spinner', 'text')] == 'Iniciando sesión', pendientes
    assert pendientes[('Tooltips', 'power-text')] == 'Opciones de energía'
    assert v.sw_sistema.get_active() and not v.marco_idiomas.get_sensitive()
    v._guardar(cerrar=False)
    GLib.timeout_add(3500, envolver(paso1))


def paso1():   # estado inicial, validación de selección y "Los dos"
    assert (Path.home() / 'Pictures' / 'wallpaper').is_dir(), 'no se creó Pictures/wallpaper'
    c0 = leer()
    assert c0.get('LoginScreen.LoginArea.Spinner', 'text') == 'Iniciando sesión'
    assert c0.get('Tooltips', 'power-text') == 'Opciones de energía'
    assert c0.get('LockScreen.Date', 'locale') == 'es_ES'
    assert not v.btn_aplicar.get_sensitive(), 'Aplicar activo sin cambios'
    assert not v._param_cambiados(), 'los parámetros salen como cambiados nada más abrir'
    assert len(v.controles) == len(velo_gui.velo_params.todos_los_parametros())
    assert [v.pila.get_child_by_name(n) is not None for n in ('fondos', 'bloqueo_hora_fecha', 'idioma', 'inicio_recuadro')] == [True] * 4
    assert v.btn_aceptar.get_sensitive() and v.btn_cerrar.get_sensitive()
    assert v.cuaderno.get_n_pages() == 3 and v.cuaderno.get_current_page() == 0
    assert not v.caja_intervalo.get_sensitive(), 'el intervalo debería estar desactivado con 1 archivo'
    # elegir carpeta: imágenes por orden, vacía = error, demasiadas = error
    lista, error = velo_media.imagenes_de_carpeta(fuentes)
    assert error is None and len(lista) >= 2 and lista == sorted(lista, key=lambda p: p.name.lower())
    vacia = fuentes / 'vacia'
    vacia.mkdir(exist_ok=True)
    assert velo_media.imagenes_de_carpeta(vacia)[1] is not None
    muchas = fuentes / 'muchas'
    muchas.mkdir(exist_ok=True)
    for i in range(velo_media.MAX_IMAGENES_CARPETA + 1):
        (muchas / f'{i:03d}.png').write_bytes(b'x')
    assert 'máximo' in velo_media.imagenes_de_carpeta(muchas)[1]
    v._asignar('ambas', [A])
    assert v.btn_aplicar.get_sensitive()
    v._guardar(cerrar=False)
    GLib.timeout_add(3000, envolver(paso2))


def paso2():   # las dos con A; ahora bloqueo con pase de diapositivas A+B, cada 2 minutos, modo fit
    c = leer()
    assert c.get('LockScreen', 'background') == c.get('LoginScreen', 'background') == A.name
    assert not v._hay_cambios() and not v.btn_aplicar.get_sensitive()
    v.radios_ajuste['fit'].set_active(True)
    v._asignar('LockScreen', [A, B])
    assert v.caja_intervalo.get_sensitive(), 'con varias imágenes el intervalo debe activarse'
    v.radio_minutos.set_active(True)
    v.spin_intervalo.set_value(2)
    v._guardar(cerrar=False)
    GLib.timeout_add(3500, envolver(paso3))


def paso3():
    c = leer()
    assert c.get('LockScreen', 'background') == f'{A.name}|{B.name}', c.get('LockScreen', 'background')
    assert c.get('LoginScreen', 'background') == A.name, 'se tocó el inicio de sesión sin querer'
    assert c.get('General', 'background-fill-mode') == 'fit'
    assert c.get('General', 'slideshow-interval') == '120'
    assert (tema / 'backgrounds' / A.name).exists() and (tema / 'backgrounds' / B.name).exists()
    assert not v._hay_cambios()
    # el vídeo viejo ya no se usa: a la papelera (y el original, intacto)
    assert not (tema / 'backgrounds' / 'Epona.mp4').exists(), 'no se quitó el fondo viejo'
    assert (tema / 'backgrounds' / 'default.jpg').exists(), 'se borró default.jpg'
    assert (Path.home() / '.local/share/Trash/files/Epona.mp4').exists() or \
        (Path.home() / '.local/share/Trash/files/Epona.mp4').is_symlink(), 'no está en la papelera'
    assert Path(sys.argv[3]).exists(), 'se borró el original del vídeo'
    # parámetros: hora, fecha e inicio de sesión
    c = v.controles
    c[('LockScreen.Clock', 'font-size')].spin.set_value(130)
    c[('LockScreen.Clock', 'format')].entrada.set_text('h:mm AP')
    c[('LockScreen.Clock', 'position')].radios['center'].set_active(True)
    c[('LockScreen.Clock', 'color')].boton.set_rgba(velo_gui.Gdk.RGBA(1, 0, 0, 1))
    c[('LockScreen.Date', 'display')].interruptor.set_active(False)
    c[('LoginScreen.Card', 'display')].interruptor.set_active(True)
    c[('LoginScreen.Card', 'opacity')].spin.set_value(0.45)
    assert len(v._param_cambiados()) == 7, v._param_cambiados()     # el idioma ya coincide con el del sistema
    assert v.btn_aplicar.get_sensitive()
    v._guardar(cerrar=False)
    GLib.timeout_add(3500, envolver(paso3b))


def paso3b():
    c = leer()
    assert c.get('LockScreen.Clock', 'font-size') == '130'
    assert c.get('LockScreen.Clock', 'format') == 'h:mm AP'
    assert c.get('LockScreen.Clock', 'position') == 'center'
    assert c.get('LockScreen.Clock', 'color') == '#FF0000'
    assert c.get('LockScreen.Date', 'display') == 'false'
    assert c.get('LockScreen.Date', 'locale') == velo_gui.velo_params.idioma_del_sistema()
    assert c.get('LoginScreen.Card', 'display') == 'true'
    assert c.get('LoginScreen.Card', 'opacity') == '0.45'
    texto = conf.read_text(encoding='utf-8')
    assert 'font-size = 130' in texto and 'display = false' in texto      # números y booleanos sin comillas
    assert 'format = "h:mm AP"' in texto and 'color = "#FF0000"' in texto  # textos con comillas
    assert 'font-weight = 600' in texto and 'font-size = 26' in texto     # lo que no se tocó, igual
    assert not v._param_cambiados() and not v._hay_cambios()
    # el idioma del sistema manda: si cambia, se ajusta al aplicar
    velo_gui.velo_params.idioma_del_sistema = lambda: 'en_GB'
    v._texto_info_idioma()
    pendientes = {(sec, clave): valor for sec, clave, valor, _q in v._idioma_cambios()}
    assert pendientes[('LockScreen.Date', 'locale')] == 'en_GB' and pendientes[('LoginScreen.Date', 'locale')] == 'en_GB'
    assert pendientes[('LockScreen.Message', 'text')] == 'Press any key', pendientes
    v._actualizar_botones()                  # en la vida real esto pasa al abrir la ventana
    assert v.btn_aplicar.get_sensitive()
    v._guardar(cerrar=False)
    GLib.timeout_add(3500, envolver(paso3c))


def paso3c():
    c = leer()
    assert c.get('LockScreen.Date', 'locale') == c.get('LoginScreen.Date', 'locale') == 'en_GB'
    assert c.get('LockScreen.Message', 'text') == 'Press any key'
    assert not v._param_cambiados() and not v._hay_cambios()
    # idioma a mano: euskera, con sus textos
    v.sw_sistema.set_active(False)
    assert v.marco_idiomas.get_sensitive()
    v.radios_idioma['eu'].set_active(True)
    assert 'Euskara' in v.lbl_idioma.get_text() and 'traducidos' not in v.lbl_idioma.get_text().replace('Fechas y textos', '')
    v.radios_idioma['ja'].set_active(True)
    assert 'inglés' in v.lbl_idioma.get_text(), v.lbl_idioma.get_text()      # sin traducción: avisa
    v.radios_idioma['eu'].set_active(True)
    pendientes = {(sec, clave): valor for sec, clave, valor, _q in v._idioma_cambios()}
    assert pendientes[('LockScreen.Message', 'text')] == 'Sakatu edozein tekla'
    assert pendientes[('LockScreen.Date', 'locale')] == 'eu'
    assert v.btn_aplicar.get_sensitive()
    v._guardar(cerrar=False)
    GLib.timeout_add(3500, envolver(paso3d))


def paso3d():
    c = leer()
    assert c.get('LockScreen.Message', 'text') == 'Sakatu edozein tekla'
    assert c.get('LockScreen.Date', 'locale') == 'eu'
    assert velo_gui.cargar_ajustes().get('idioma') == 'eu', 'no se recordó el idioma elegido'
    assert not v._hay_cambios()
    # vuelve a pantalla única: se puede cambiar solo el inicio de sesión
    v._asignar('LoginScreen', [B])
    v.btn_aceptar.emit('clicked')            # Aceptar = guardar y cerrar: el bucle termina solo


def comprobar_final():
    c = leer()
    assert c.get('LoginScreen', 'background') == B.name
    assert c.get('LockScreen', 'background') == f'{A.name}|{B.name}'
    assert cerrada['si'], 'Aceptar no cerró la ventana'
    assert list(conf.parent.glob('default.conf.gui-bak-*')), 'falta copia de seguridad'
    resultado['ok'] = True
    resultado['detalle'] = 'carpeta, los dos, pase de imágenes, intervalo, Aplicar, Aceptar y papelera'


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
GLib.timeout_add(40000, lambda: (fallo('tiempo agotado'), False)[1])
Gtk.main()
if cerrada['si'] and not resultado['detalle']:
    try:
        comprobar_final()
    except Exception as e:   # noqa: BLE001
        resultado['detalle'] = repr(e)
print('RESULTADO:', 'OK' if resultado['ok'] else 'FALLO', resultado['detalle'])
sys.exit(0 if resultado['ok'] else 1)
