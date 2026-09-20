"""Parámetros del tema (hora, fecha, inicio de sesión): definición y controles GTK.

Todo está descrito en PAGINAS. Para añadir un parámetro basta con añadir una línea allí;
para añadir un tipo de control nuevo, una clase más en CONTROLES. Sin desplegables: en
Wayland los de GTK 3 salen cortados, así que las opciones son botones seguidos.
"""
import os

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402

# ---------- descripción de los parámetros ----------

FORMATOS_HORA = [('hh:mm', '24 horas'), ('hh:mm:ss', '24 h con segundos'), ('h:mm AP', '12 horas')]


def idioma_del_sistema():
    """Idioma aplicado en el sistema del usuario (p. ej. 'es_ES'), sacado de su entorno."""
    for variable in ('LC_ALL', 'LC_TIME', 'LANG'):
        valor = os.environ.get(variable, '')
        if valor and valor not in ('C', 'POSIX') and not valor.startswith('C.'):
            return valor.split('.')[0].split('@')[0]
    return 'en_US'


IDIOMA = idioma_del_sistema()
# Nombres del día y del mes: los pone Qt según el idioma. Solo cambian las palabras fijas ("de").
if IDIOMA.startswith('es'):
    FORMATOS_FECHA = [("dddd, d 'de' MMMM 'de' yyyy", 'lunes, 5 de enero de 2026'),
                      ("d 'de' MMMM 'de' yyyy", '5 de enero de 2026'),
                      ("dddd d 'de' MMMM", 'lunes 5 de enero'),
                      ('dd/MM/yyyy', '05/01/2026')]
else:
    FORMATOS_FECHA = [('dddd, MMMM d, yyyy', 'Monday, January 5, 2026'),
                      ('MMMM d, yyyy', 'January 5, 2026'),
                      ('dddd, d MMMM', 'Monday, 5 January'),
                      ('dd/MM/yyyy', '05/01/2026')]
POSICIONES = ['top-left', 'top-center', 'top-right',
              'center-left', 'center', 'center-right',
              'bottom-left', 'bottom-center', 'bottom-right']
FLECHAS = ['↖', '↑', '↗', '←', '●', '→', '↙', '↓', '↘']


def p(seccion, clave, tipo, etiqueta, ayuda='', **extra):
    return dict(seccion=seccion, clave=clave, tipo=tipo, etiqueta=etiqueta, ayuda=ayuda, **extra)


def _reloj(sec, tam=(20, 400, 5)):
    return [p(sec, 'display', 'bool', 'Mostrar la hora'),
            p(sec, 'format', 'formato', 'Formato de la hora', presets=FORMATOS_HORA,
              ayuda='Símbolos de Qt: hh horas, mm minutos, ss segundos, AP mañana/tarde.'),
            p(sec, 'font-size', 'numero', 'Tamaño de la hora', min=tam[0], max=tam[1], paso=tam[2]),
            p(sec, 'color', 'color', 'Color de la hora')]


def _fecha(sec, tam=(8, 120, 1)):
    return [p(sec, 'display', 'bool', 'Mostrar la fecha'),
            p(sec, 'format', 'formato', 'Formato de la fecha', presets=FORMATOS_FECHA,
              ayuda='Símbolos de Qt: d día, dddd nombre del día, MM mes en número, MMMM nombre del mes, '
                    'yyyy año. El texto fijo va entre comillas simples.'),
            p(sec, 'font-size', 'numero', 'Tamaño de la fecha', min=tam[0], max=tam[1], paso=tam[2]),
            p(sec, 'color', 'color', 'Color de la fecha')]

def _efectos(sec):
    return [p(sec, 'blur', 'numero', 'Desenfoque', '0 = nítido.', min=0, max=64, paso=1),
            p(sec, 'brightness', 'numero', 'Brillo', '0 = sin cambio · negativo oscurece · positivo aclara.',
              min=-1, max=1, paso=0.05, decimales=2),
            p(sec, 'saturation', 'numero', 'Saturación', '0 = sin cambio · -1 blanco y negro · positivo más vivo.',
              min=-1, max=1, paso=0.05, decimales=2)]


def _boton(nombre, nombre_visible=False):
    sec = f'LoginScreen.MenuArea.{nombre}'
    lista = [p(sec, 'display', 'bool', 'Mostrar el botón'),
             p(sec, 'position', 'posicion', 'Posición', sin_centro=True),
             p(sec, 'content-color', 'color', 'Color del icono y el texto'),
             p(sec, 'background-opacity', 'numero', 'Opacidad del fondo del botón (0 = transparente)',
               min=0, max=1, paso=0.05, decimales=2)]
    if nombre_visible:
        clave = 'display-session-name' if nombre == 'Session' else 'display-layout-name'
        lista.insert(2, p(sec, clave, 'bool', 'Mostrar el nombre junto al icono'))
    return lista


NOTA_IDIOMA = f'Los nombres del día y del mes salen en el idioma de tu sistema ({IDIOMA}).'


# Cada página pertenece a un grupo del menú lateral: None = suelta (arriba), 'Bloqueo' o 'Inicio de sesión'.
# Lo que afecta a las dos pantallas (fondo con efectos, hora, fecha...) está en cada grupo con sus
# propios valores: cambiar uno no toca el otro.
GRUPO_BLOQUEO = 'Bloqueo'
GRUPO_INICIO = 'Inicio de sesión'

PAGINAS = [
    dict(id='general', grupo=None, titulo='General', secciones=[
        dict(titulo='Aspecto general', parametros=[
            p('General', 'scale', 'numero', 'Escala de toda la interfaz',
              'Agranda o reduce todo a la vez. Con valores extremos algo puede descolocarse.',
              min=0.6, max=2.5, paso=0.05, decimales=2),
            p('General', 'enable-animations', 'bool', 'Animaciones'),
            p('*', 'font-family', 'fuente', 'Fuente de todos los textos',
              'Se aplica a todo el tema. Tiene que estar instalada en el sistema: si no, se usa otra parecida.')]),
    ]),

    # ---------- pantalla de bloqueo ----------
    dict(id='bloqueo_hora_fecha', grupo=GRUPO_BLOQUEO, titulo='Hora y fecha', secciones=[
        dict(titulo='Hora de la pantalla de bloqueo', parametros=[
            p('LockScreen.Clock', 'position', 'posicion', 'Posición',
              'La fecha va siempre justo debajo de la hora.'),
            *_reloj('LockScreen.Clock'),
            p('LockScreen.Clock', 'font-weight', 'numero', 'Grosor de las letras',
              '100 muy fina · 400 normal · 700 negrita · 900 muy gruesa.', min=100, max=900, paso=100),
            p('LockScreen.Clock', 'outline', 'bool', 'Contorno gris suave')]),
        dict(titulo='Fecha de la pantalla de bloqueo', nota=NOTA_IDIOMA, parametros=[
            *_fecha('LockScreen.Date'),
            p('LockScreen.Date', 'font-weight', 'numero', 'Grosor de las letras',
              min=100, max=900, paso=100),
            p('LockScreen.Date', 'margin-top', 'numero', 'Espacio entre la hora y la fecha',
              min=0, max=100, paso=1),
            p('LockScreen.Date', 'outline', 'bool', 'Contorno gris suave')]),
    ]),
    dict(id='bloqueo_mensaje', grupo=GRUPO_BLOQUEO, titulo='Mensaje', secciones=[
        dict(titulo='Mensaje de la pantalla de bloqueo',
             nota='El texto («Pulse cualquier tecla») cambia solo con el idioma: se elige en la página Idioma.',
             parametros=[
                 p('LockScreen.Message', 'display', 'bool', 'Mostrar el mensaje'),
                 p('LockScreen.Message', 'position', 'posicion', 'Posición'),
                 p('LockScreen.Message', 'font-size', 'numero', 'Tamaño de la letra', min=8, max=60, paso=1),
                 p('LockScreen.Message', 'font-weight', 'numero', 'Grosor de las letras',
                   min=100, max=900, paso=100),
                 p('LockScreen.Message', 'color', 'color', 'Color'),
                 p('LockScreen.Message', 'display-icon', 'bool', 'Mostrar el icono'),
                 p('LockScreen.Message', 'icon-size', 'numero', 'Tamaño del icono', min=8, max=60, paso=1),
                 p('LockScreen.Message', 'spacing', 'numero', 'Espacio entre icono y texto',
                   min=0, max=40, paso=1)])]),
    dict(id='bloqueo_efectos', grupo=GRUPO_BLOQUEO, titulo='Efectos del fondo', secciones=[
        dict(titulo='Efectos sobre el fondo de la pantalla de bloqueo', parametros=_efectos('LockScreen'))]),
    dict(id='bloqueo_degradados', grupo=GRUPO_BLOQUEO, titulo='Degradados', secciones=[
        dict(titulo='Degradados de la pantalla de bloqueo',
             nota='Oscurecen el borde de arriba (la hora) y el de abajo (el mensaje) para que se lean sobre '
                  'cualquier fondo.',
             parametros=[
                 p('LockScreen.Scrim', 'display', 'bool', 'Mostrar los degradados'),
                 p('LockScreen.Scrim', 'color', 'color', 'Color'),
                 p('LockScreen.Scrim', 'top-opacity', 'numero', 'Intensidad de arriba',
                   min=0, max=1, paso=0.05, decimales=2),
                 p('LockScreen.Scrim', 'top-height', 'numero', 'Altura de arriba (fracción de la pantalla)',
                   min=0.05, max=1, paso=0.01, decimales=2),
                 p('LockScreen.Scrim', 'bottom-opacity', 'numero', 'Intensidad de abajo',
                   min=0, max=1, paso=0.05, decimales=2),
                 p('LockScreen.Scrim', 'bottom-height', 'numero', 'Altura de abajo (fracción de la pantalla)',
                   min=0.05, max=1, paso=0.01, decimales=2)])]),

    # ---------- pantalla de inicio de sesión ----------
    dict(id='inicio_recuadro', grupo=GRUPO_INICIO, titulo='Recuadro', secciones=[
        dict(titulo='Recuadro', nota='Un panel translúcido detrás de la foto, el nombre y la contraseña.',
             parametros=[
                 p('LoginScreen.Card', 'display', 'bool', 'Mostrar el recuadro'),
                 p('LoginScreen.Card', 'color', 'color', 'Color del recuadro'),
                 p('LoginScreen.Card', 'opacity', 'numero', 'Opacidad (0 invisible, 1 sólido)',
                   min=0, max=1, paso=0.05, decimales=2),
                 p('LoginScreen.Card', 'radius', 'numero', 'Esquinas redondeadas', min=0, max=60, paso=1)])]),
    dict(id='inicio_hora_fecha', grupo=GRUPO_INICIO, titulo='Hora y fecha', secciones=[
        dict(titulo='Hora en el inicio de sesión',
             parametros=[*_reloj('LoginScreen.Clock', tam=(10, 200, 2)),
                         p('LoginScreen.Clock', 'font-weight', 'numero', 'Grosor de las letras',
                           min=100, max=900, paso=100),
                         p('LoginScreen.Clock', 'outline', 'bool', 'Contorno gris suave')]),
        dict(titulo='Fecha en el inicio de sesión', nota=NOTA_IDIOMA,
             parametros=[*_fecha('LoginScreen.Date', tam=(8, 80, 1)),
                         p('LoginScreen.Date', 'font-weight', 'numero', 'Grosor de las letras',
                           min=100, max=900, paso=100),
                         p('LoginScreen.Date', 'outline', 'bool', 'Contorno gris suave')])]),
    dict(id='inicio_usuario', grupo=GRUPO_INICIO, titulo='Usuario y contraseña', secciones=[
        dict(titulo='Nombre de usuario', parametros=[
            p('LoginScreen.LoginArea.Username', 'font-size', 'numero', 'Tamaño', min=10, max=80, paso=1),
            p('LoginScreen.LoginArea.Username', 'font-weight', 'numero', 'Grosor de las letras',
              min=100, max=900, paso=100),
            p('LoginScreen.LoginArea.Username', 'color', 'color', 'Color'),
            p('LoginScreen.LoginArea.Username', 'outline', 'bool', 'Contorno gris suave')]),
        dict(titulo='Foto de usuario', parametros=[
            p('LoginScreen.LoginArea.Avatar', 'active-size', 'numero', 'Tamaño', min=40, max=300, paso=5),
            p('LoginScreen.LoginArea.Avatar', 'shape', 'opciones', 'Forma',
              opciones=[('circle', 'Círculo'), ('square', 'Cuadrado')])]),
        dict(titulo='Campo de contraseña', parametros=[
            p('LoginScreen.LoginArea.PasswordInput', 'width', 'numero', 'Ancho', min=100, max=600, paso=10),
            p('LoginScreen.LoginArea.PasswordInput', 'height', 'numero', 'Alto', min=20, max=80, paso=1),
            p('LoginScreen.LoginArea.PasswordInput', 'font-size', 'numero', 'Tamaño de la letra',
              min=8, max=30, paso=1)])]),
    dict(id='inicio_efectos', grupo=GRUPO_INICIO, titulo='Efectos del fondo', secciones=[
        dict(titulo='Efectos sobre el fondo de la pantalla de inicio de sesión',
             parametros=_efectos('LoginScreen'))]),
    dict(id='inicio_degradado', grupo=GRUPO_INICIO, titulo='Degradado inferior', secciones=[
        dict(titulo='Degradado inferior',
             nota='Oscurece el borde de abajo para que se lean los botones de sesión, idioma y apagado.',
             parametros=[
                 p('LoginScreen.Scrim', 'display', 'bool', 'Mostrar el degradado'),
                 p('LoginScreen.Scrim', 'color', 'color', 'Color'),
                 p('LoginScreen.Scrim', 'bottom-opacity', 'numero', 'Intensidad',
                   min=0, max=1, paso=0.05, decimales=2),
                 p('LoginScreen.Scrim', 'bottom-height', 'numero', 'Altura (fracción de la pantalla)',
                   min=0.05, max=0.6, paso=0.01, decimales=2)])]),
    dict(id='inicio_botones', grupo=GRUPO_INICIO, titulo='Botones', secciones=[
        dict(titulo='Todos los botones', nota='Los de sesión, teclado, idioma y apagado que salen en las esquinas.',
             parametros=[
                 p('LoginScreen.MenuArea.Buttons', 'size', 'numero', 'Tamaño', min=20, max=80, paso=1),
                 p('LoginScreen.MenuArea.Buttons', 'border-radius', 'numero', 'Esquinas redondeadas',
                   min=0, max=40, paso=1),
                 p('LoginScreen.MenuArea.Buttons', 'spacing', 'numero', 'Espacio entre botones',
                   min=0, max=60, paso=1),
                 p('LoginScreen.MenuArea.Buttons', 'margin-bottom', 'numero', 'Separación del borde de abajo',
                   min=0, max=200, paso=5)]),
        dict(titulo='Sesión (escritorio)', parametros=_boton('Session', nombre_visible=True)),
        dict(titulo='Distribución del teclado (idioma)', parametros=_boton('Layout', nombre_visible=True)),
        dict(titulo='Teclado en pantalla', parametros=_boton('Keyboard')),
        dict(titulo='Apagado y reinicio', parametros=_boton('Power')),
    ]),
]

# Orden del menú lateral: General, Fondo, grupo Bloqueo, grupo Inicio de sesión, Idioma.
# (El editor de fondos y el de idioma son páginas propias de velo_gui.py.)


def todos_los_parametros():
    return [q for pag in PAGINAS for sec in pag['secciones'] for q in sec['parametros']]


# ---------- controles ----------

class Control:
    """Un parámetro con su widget. `valor()` devuelve el texto tal como va en el .conf."""
    entre_comillas = True

    def __init__(self, spec, al_cambiar):
        self.spec = spec
        self.al_cambiar = al_cambiar
        self.widget = None

    def valor(self):
        raise NotImplementedError

    def poner(self, texto):
        raise NotImplementedError

    def _avisar(self, *_):
        self.al_cambiar()


class ControlBool(Control):
    entre_comillas = False

    def __init__(self, spec, al_cambiar):
        super().__init__(spec, al_cambiar)
        self.interruptor = Gtk.Switch(halign=Gtk.Align.START, valign=Gtk.Align.CENTER)
        self.interruptor.connect('notify::active', self._avisar)
        self.widget = self.interruptor

    def valor(self):
        return 'true' if self.interruptor.get_active() else 'false'

    def poner(self, texto):
        self.interruptor.set_active(str(texto).strip().lower() == 'true')


class ControlNumero(Control):
    entre_comillas = False

    def __init__(self, spec, al_cambiar):
        super().__init__(spec, al_cambiar)
        self.decimales = spec.get('decimales', 0)
        self.spin = Gtk.SpinButton.new_with_range(spec['min'], spec['max'], spec['paso'])
        self.spin.set_digits(self.decimales)
        self.spin.set_halign(Gtk.Align.START)
        self.spin.connect('value-changed', self._avisar)
        self.widget = self.spin

    def valor(self):
        if self.decimales:
            return f'{self.spin.get_value():g}'
        return str(self.spin.get_value_as_int())

    def poner(self, texto):
        try:
            self.spin.set_value(float(texto))
        except ValueError:
            pass


class ControlColor(Control):
    def __init__(self, spec, al_cambiar):
        super().__init__(spec, al_cambiar)
        self.boton = Gtk.ColorButton(halign=Gtk.Align.START)
        self.boton.connect('color-set', self._avisar)
        self.widget = self.boton

    def valor(self):
        c = self.boton.get_rgba()
        return '#%02X%02X%02X' % tuple(round(x * 255) for x in (c.red, c.green, c.blue))

    def poner(self, texto):
        rgba = Gdk.RGBA()
        if not rgba.parse(str(texto)):
            rgba.parse('#FFFFFF')
        self.boton.set_rgba(rgba)


class ControlOpciones(Control):
    """Botones seguidos, uno por opción. Si el .conf tiene un valor que no está, se añade."""

    def __init__(self, spec, al_cambiar):
        super().__init__(spec, al_cambiar)
        self.opciones = list(spec['opciones'])
        self.radios = {}
        self.caja = Gtk.Box(halign=Gtk.Align.START)
        self.caja.get_style_context().add_class('linked')
        self.widget = self.caja
        for valor, etiqueta in self.opciones:
            self._anadir(valor, etiqueta)

    def _anadir(self, valor, etiqueta):
        grupo = next(iter(self.radios.values()), None)
        r = Gtk.RadioButton.new_with_label_from_widget(grupo, etiqueta)
        r.set_mode(False)
        r.connect('toggled', lambda b: b.get_active() and self._avisar())
        self.radios[valor] = r
        self.caja.pack_start(r, False, False, 0)
        r.show()

    def valor(self):
        return next((v for v, r in self.radios.items() if r.get_active()), self.opciones[0][0])

    def poner(self, texto):
        texto = str(texto)
        if texto not in self.radios:
            self._anadir(texto, texto)
        self.radios[texto].set_active(True)


class ControlPosicion(Control):
    """Cuadrícula 3×3 de flechas para elegir dónde va un elemento."""

    def __init__(self, spec, al_cambiar):
        super().__init__(spec, al_cambiar)
        self.rejilla = Gtk.Grid(halign=Gtk.Align.START, row_spacing=2, column_spacing=2)
        self.radios = {}
        grupo = None
        for i, (pos, flecha) in enumerate(zip(POSICIONES, FLECHAS)):
            r = Gtk.RadioButton.new_with_label_from_widget(grupo, flecha)
            r.set_mode(False)
            r.set_size_request(44, 36)
            if pos == 'center' and spec.get('sin_centro'):
                r.set_sensitive(False)          # el tema no admite el centro para este elemento
            r.set_tooltip_text(pos.replace('-', ' '))
            r.connect('toggled', lambda b: b.get_active() and self._avisar())
            grupo = grupo or r
            self.radios[pos] = r
            self.rejilla.attach(r, i % 3, i // 3, 1, 1)
        self.widget = self.rejilla

    def valor(self):
        return next((v for v, r in self.radios.items() if r.get_active()), 'top-center')

    def poner(self, texto):
        if str(texto) in self.radios:
            self.radios[str(texto)].set_active(True)


class ControlFormato(Control):
    """Cuadro de texto con botones de formatos habituales que lo rellenan."""

    def __init__(self, spec, al_cambiar):
        super().__init__(spec, al_cambiar)
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, halign=Gtk.Align.START)
        fila = Gtk.Box()
        fila.get_style_context().add_class('linked')
        self.entrada = Gtk.Entry(width_chars=34)
        for valor, etiqueta in spec['presets']:
            b = Gtk.Button(label=etiqueta)
            b.connect('clicked', lambda _b, v=valor: self.entrada.set_text(v))
            fila.pack_start(b, False, False, 0)
        self.entrada.connect('changed', self._avisar)
        caja.pack_start(fila, False, False, 0)
        caja.pack_start(self.entrada, False, False, 0)
        self.widget = caja

    def valor(self):
        return self.entrada.get_text()

    def poner(self, texto):
        self.entrada.set_text(str(texto))


class ControlFuente(Control):
    """Nombre de la fuente y un botón que abre el selector de fuentes de GTK."""

    def __init__(self, spec, al_cambiar):
        super().__init__(spec, al_cambiar)
        self.familia = ''
        self.etiqueta = Gtk.Label(xalign=0)
        self.boton = Gtk.Button(label='Elegir…')
        self.boton.connect('clicked', self._elegir)
        caja = Gtk.Box(spacing=12, halign=Gtk.Align.START)
        caja.pack_start(self.etiqueta, False, False, 0)
        caja.pack_start(self.boton, False, False, 0)
        self.widget = caja

    def _elegir(self, boton):
        dlg = Gtk.FontChooserDialog(title='Fuente de todos los textos', transient_for=boton.get_toplevel())
        dlg.set_font(f'{self.familia} 12')
        dlg.set_preview_text('Pulse cualquier tecla · 12:34')
        if dlg.run() == Gtk.ResponseType.OK:
            familia = dlg.get_font_face().get_family().get_name() if dlg.get_font_face() else ''
            if not familia:
                familia = Pango.FontDescription.from_string(dlg.get_font()).get_family()
            self.poner(familia)
            self._avisar()
        dlg.destroy()

    def valor(self):
        return self.familia

    def poner(self, texto):
        self.familia = str(texto)
        self.etiqueta.set_markup(f'<span font_family="{GLib.markup_escape_text(self.familia)}" size="large">'
                                 f'{GLib.markup_escape_text(self.familia)}</span>')


CONTROLES = {'bool': ControlBool, 'numero': ControlNumero, 'color': ControlColor,
             'opciones': ControlOpciones, 'posicion': ControlPosicion, 'formato': ControlFormato,
             'fuente': ControlFuente}


# ---------- construcción de páginas ----------

def crear_pagina(pagina, conf, al_cambiar):
    """Devuelve (widget, {(seccion, clave): Control}) para una página de parámetros.

    Los controles ya llevan el valor del .conf; `valores_iniciales` no se guarda aquí:
    quien llama lo toma con `control.valor()` justo después de crearla.
    """
    controles = {}
    cont = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=22, margin=24)
    for seccion in pagina['secciones']:
        bloque = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        titulo = Gtk.Label(label=seccion['titulo'], xalign=0)
        titulo.get_style_context().add_class('titulo')
        bloque.pack_start(titulo, False, False, 0)
        if seccion.get('nota'):
            nota = Gtk.Label(label=seccion['nota'], xalign=0, wrap=True)
            nota.get_style_context().add_class('suave')
            bloque.pack_start(nota, False, False, 0)
        rejilla = Gtk.Grid(row_spacing=10, column_spacing=18)
        for fila, spec in enumerate(seccion['parametros']):
            control = CONTROLES[spec['tipo']](spec, al_cambiar)
            control.poner(valor_inicial(conf, spec))
            controles[(spec['seccion'], spec['clave'])] = control
            etiqueta = Gtk.Label(label=spec['etiqueta'], xalign=0, valign=Gtk.Align.START, wrap=True)
            etiqueta.set_size_request(230, -1)
            if spec['tipo'] in ('bool', 'numero', 'color', 'opciones'):
                etiqueta.set_valign(Gtk.Align.CENTER)
            rejilla.attach(etiqueta, 0, fila, 1, 1)
            columna = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            columna.pack_start(control.widget, False, False, 0)
            if spec.get('ayuda'):
                ayuda = Gtk.Label(label=spec['ayuda'], xalign=0, wrap=True)
                ayuda.get_style_context().add_class('suave')
                columna.pack_start(ayuda, False, False, 0)
            rejilla.attach(columna, 1, fila, 1, 1)
        bloque.pack_start(rejilla, False, False, 0)
        cont.pack_start(bloque, False, False, 0)
    return cont, controles


def valor_inicial(conf, spec):
    """Valor del .conf para ese parámetro ('*' = el de la primera sección que tenga la clave)."""
    if spec['seccion'] == '*':
        secciones = conf.secciones_con(spec['clave'])
        return conf.get(secciones[0], spec['clave'], _defecto(spec)) if secciones else _defecto(spec)
    return conf.get(spec['seccion'], spec['clave'], _defecto(spec))


def expandir(conf, seccion, clave, valor, entre_comillas):
    """[(sección, clave, valor, comillas)] que hay que escribir; '*' se reparte por todas las secciones."""
    if seccion != '*':
        return [(seccion, clave, valor, entre_comillas)]
    return [(s, clave, valor, entre_comillas) for s in conf.secciones_con(clave)]


def _defecto(spec):
    return {'bool': 'false', 'numero': str(spec.get('min', 0)), 'color': '#FFFFFF',
            'opciones': spec['opciones'][0][0] if spec.get('opciones') else '',
            'posicion': 'top-center', 'formato': '', 'fuente': 'Noto Sans'}[spec['tipo']]
