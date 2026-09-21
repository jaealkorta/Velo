#!/usr/bin/env python3
"""Configuraciones de VELO - editor gráfico de la configuración del tema.

Trabaja sobre la copia local del tema (la carpeta que contiene gui/), lee y escribe
configs/default.conf con copia de seguridad y no usa la red.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Con Wayland puro, GTK 3 dibuja su propia barra de título (pequeña y poco visible).
# Con X11/XWayland la dibuja KDE, con el tema de ventanas del usuario.
if os.environ.get('DISPLAY'):
    os.environ.setdefault('GDK_BACKEND', 'x11')

import gi  # noqa: E402
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GLib, GdkPixbuf, Gtk, Gdk  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import velo_conf   # noqa: E402
import velo_idiomas  # noqa: E402
import velo_media  # noqa: E402
import velo_params  # noqa: E402
import velo_presets  # noqa: E402
import velo_sistema  # noqa: E402

TITULO = 'Configuraciones de VELO'
TEMA_POR_DEFECTO = Path(__file__).resolve().parent.parent
AJUSTES = Path.home() / '.config' / 'velo-gui' / 'ajustes.json'
PANTALLAS = {'LockScreen': 'la pantalla de bloqueo', 'LoginScreen': 'la pantalla de inicio de sesión'}
SEPARADOR = '|'            # varias imágenes en `background = "a.jpg|b.jpg"`
INTERVALO_MINIMO = 5       # segundos (el tema no baja de esto)
INTERVALO_POR_DEFECTO = 60
# (id de la pestaña, texto de la pestaña, título de la tarjeta)
PESTANAS = [('ambas', 'Los dos', 'Fondo de las dos pantallas'),
            ('LockScreen', 'Bloqueo', 'Fondo de la pantalla de bloqueo'),
            ('LoginScreen', 'Inicio de sesión', 'Fondo de la pantalla de inicio de sesión')]
AJUSTES_IMAGEN = [('fill', 'Rellenar', 'Ocupa toda la pantalla y recorta lo que sobre.'),
                  ('fit', 'Ajustar', 'Se ve entera, con bordes si la proporción no coincide.'),
                  ('stretch', 'Estirar', 'Ocupa toda la pantalla, pero deforma la imagen.')]
CSS = b"""
.tarjeta { background: alpha(@theme_fg_color, 0.06); border-radius: 10px; padding: 14px; }
.titulo { font-weight: bold; font-size: 110%; }
.seccion { font-weight: bold; }
.aviso { color: #d99a2b; }
.suave { opacity: 0.7; }
.menu-grupo { font-weight: bold; font-size: 80%; opacity: 0.65; margin: 16px 12px 4px 12px; }
.menu-pagina { margin: 9px 12px; }
.menu-sangria { margin-left: 28px; }
"""


def cargar_ajustes():
    try:
        return json.loads(AJUSTES.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def guardar_ajustes(datos):
    try:
        AJUSTES.parent.mkdir(parents=True, exist_ok=True)
        AJUSTES.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')
    except OSError:
        pass


def cargar_pixbuf(ruta, ancho, alto):
    """Miniatura de una imagen o del primer fotograma de un vídeo (None si falla)."""
    try:
        if velo_media.tipo(ruta) == 'video':
            ruta = velo_media.miniatura_video(ruta, ancho * 2)
            if not ruta:
                return None
        return GdkPixbuf.Pixbuf.new_from_file_at_scale(str(ruta), ancho, alto, True)
    except GLib.Error:
        return None


class TarjetaFondo(Gtk.Box):
    """Vista previa y datos del fondo (uno o varios archivos) y su botón de elegir."""

    def __init__(self, titulo, al_elegir_archivo, al_elegir_carpeta):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.get_style_context().add_class('tarjeta')
        self.set_size_request(540, -1)
        self.set_halign(Gtk.Align.CENTER)
        cab = Gtk.Label(label=titulo, xalign=0)
        cab.get_style_context().add_class('titulo')
        self.imagen = Gtk.Image()
        self.imagen.set_size_request(256, 144)
        self.imagen.set_no_show_all(True)
        self.nombre = Gtk.Label(xalign=0, ellipsize=3)
        self.info = Gtk.Label(xalign=0, wrap=True)
        self.info.get_style_context().add_class('suave')
        self.aviso = Gtk.Label(xalign=0, wrap=True)
        self.aviso.get_style_context().add_class('aviso')
        botones = Gtk.Box(spacing=8, homogeneous=True)
        b_archivo = Gtk.Button(label='Elegir archivo…')
        b_archivo.set_tooltip_text('Una imagen o un vídeo')
        b_archivo.connect('clicked', lambda _b: al_elegir_archivo())
        b_carpeta = Gtk.Button(label='Elegir carpeta…')
        b_carpeta.set_tooltip_text('Las imágenes de la carpeta cambian solas')
        b_carpeta.connect('clicked', lambda _b: al_elegir_carpeta())
        botones.pack_start(b_archivo, True, True, 0)
        botones.pack_start(b_carpeta, True, True, 0)
        ayuda = Gtk.Label(label='Archivo: una imagen o un vídeo. '
                                'Carpeta: sus imágenes cambian solas.', xalign=0, wrap=True)
        ayuda.get_style_context().add_class('suave')
        for w in (cab, self.imagen, self.nombre, self.info, self.aviso, botones, ayuda):
            self.pack_start(w, False, False, 0)
        self._version = 0

    def mostrar_texto(self, nombre, info):
        """Para el caso en que no hay un único fondo que enseñar."""
        self._version += 1
        self.imagen.clear()
        self.imagen.hide()
        self.nombre.set_text(nombre)
        self.info.set_text(info)
        self.aviso.set_text('')

    def mostrar(self, rutas, ejecutor):
        """rutas: lista de 1 archivo, o de varias imágenes (pase de diapositivas)."""
        self._version += 1
        version = self._version
        rutas = [Path(r) for r in rutas]
        primera = rutas[0]
        if len(rutas) > 1:
            self.nombre.set_text(f'{len(rutas)} imágenes que cambian solas')
            self.info.set_text('Leyendo datos…')
        else:
            self.nombre.set_text(primera.name)
            self.info.set_text('Leyendo datos…')
        self.aviso.set_text('')
        self.imagen.clear()
        self.imagen.show()
        if not primera.exists():
            self.info.set_text('No se encuentra este archivo.')
            self.aviso.set_text('Elige otro fondo o se usará default.jpg.')
            return

        def trabajo():
            pb = cargar_pixbuf(primera, 256, 144)
            datos = velo_media.describir(primera) if len(rutas) == 1 else None
            total_mb = sum(r.stat().st_size for r in rutas if r.exists()) / 1_048_576
            GLib.idle_add(self._rellenar, version, pb, datos, len(rutas), total_mb)
        ejecutor.submit(trabajo)

    def _rellenar(self, version, pb, datos, cuantas, total_mb):
        if version != self._version:
            return False
        if pb:
            self.imagen.set_from_pixbuf(pb)
        if datos:
            self.info.set_text(velo_media.resumen(datos))
            self.aviso.set_text(datos['aviso'])
        elif cuantas > 1:
            self.info.set_text(f'{total_mb:.1f} MB en total')
            if total_mb > velo_media.AVISO_TOTAL_MB:
                self.aviso.set_text('Pesan mucho en total: la pantalla de inicio tardará más en cargar.')
        return False


class MenuLateral(Gtk.ScrolledWindow):
    """Menú de la izquierda: páginas sueltas y grupos con sus páginas debajo (un grupo no es una página)."""

    def __init__(self, pila):
        super().__init__(hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.pila = pila
        self.lista = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.ids = {}          # fila -> id de página
        self.filas = {}        # id de página -> fila
        self.add(self.lista)
        self.set_size_request(210, -1)
        self.lista.connect('row-selected', self._al_elegir)
        pila.connect('notify::visible-child-name', self._al_cambiar_pagina)

    def grupo(self, titulo):
        fila = Gtk.ListBoxRow(selectable=False, activatable=False)
        etiqueta = Gtk.Label(label=titulo.upper(), xalign=0)
        etiqueta.get_style_context().add_class('menu-grupo')
        fila.add(etiqueta)
        self.lista.add(fila)

    def pagina(self, id_, titulo, en_grupo=False):
        fila = Gtk.ListBoxRow()
        etiqueta = Gtk.Label(label=titulo, xalign=0)
        estilo = etiqueta.get_style_context()
        estilo.add_class('menu-pagina')
        if en_grupo:
            estilo.add_class('menu-sangria')
        fila.add(etiqueta)
        self.lista.add(fila)
        self.ids[fila] = id_
        self.filas[id_] = fila

    def _al_elegir(self, _lista, fila):
        if fila is not None and fila in self.ids:
            self.pila.set_visible_child_name(self.ids[fila])

    def _al_cambiar_pagina(self, *_):
        fila = self.filas.get(self.pila.get_visible_child_name())
        if fila is not None and self.lista.get_selected_row() is not fila:
            self.lista.select_row(fila)


class Ventana(Gtk.Window):
    def __init__(self, tema):
        super().__init__(title=TITULO)
        self.tema = Path(tema).resolve()
        self.fondos = self.tema / 'backgrounds'
        self.ejecutor = ThreadPoolExecutor(max_workers=2)
        self.ajustes = cargar_ajustes()
        self.ocupado = False
        self.cerrar_al_guardar = False
        self.marcador_fallido = False  # ffmpeg no pudo sacar el primer fotograma: no insistir
        self.luego_guardar = None    # qué hacer cuando termine de guardar (p. ej. enviar al sistema)
        self._listo = False          # hasta que la ventana está construida, los avisos de cambio no valen
        self.controles = {}          # parámetros de las páginas de ajustes: {(sección, clave): Control}
        self.iniciales_param = {}

        self.conf = velo_conf.ConfFile(self._ruta_conf())
        self.inicial = {s: self._rutas_actuales(s) for s in PANTALLAS}
        self.elegido = {s: list(r) for s, r in self.inicial.items()}
        self.modo_inicial = self.conf.get('General', 'background-fill-mode', 'fill')
        if self.modo_inicial not in {i for i, _t, _d in AJUSTES_IMAGEN}:
            self.modo_inicial = 'fill'
        self.intervalo_inicial = self._intervalo_conf()
        self.idiomas = velo_idiomas.disponibles()
        elegido = self.ajustes.get('idioma', 'sistema')
        self.idioma_inicial = elegido if elegido in dict(self.idiomas) else 'sistema'

        self._carpeta_selector()   # crea ~/Pictures/wallpaper si no existe
        self.set_default_size(1140, 800)
        self._construir()
        self.connect('delete-event', self._al_cerrar)
        self._refrescar_tarjetas()
        GLib.idle_add(self._comprobar_sistema)

    # ---------- datos ----------
    def _ruta_conf(self):
        relativa = 'configs/default.conf'
        try:
            for linea in (self.tema / 'metadata.desktop').read_text(encoding='utf-8').splitlines():
                if linea.startswith('ConfigFile='):
                    relativa = linea.split('=', 1)[1].strip()
        except OSError:
            pass
        return self.tema / relativa

    def _rutas_actuales(self, seccion):
        valor = self.conf.get(seccion, 'background', 'default.jpg')
        nombres = [n for n in valor.split(SEPARADOR) if n] or ['default.jpg']
        return [self.fondos / n for n in nombres]

    def _intervalo_conf(self):
        try:
            return max(INTERVALO_MINIMO, int(self.conf.get('General', 'slideshow-interval', '')))
        except ValueError:
            return INTERVALO_POR_DEFECTO

    def _carpeta_selector(self):
        """Carpeta donde se abre el selector de archivos: la última usada, o
        ~/Pictures/wallpaper (que se crea sola si no existe)."""
        ultima = self.ajustes.get('ultima_carpeta')
        if ultima and Path(ultima).is_dir():
            return Path(ultima)
        por_defecto = Path.home() / 'Pictures' / 'wallpaper'
        try:
            por_defecto.mkdir(parents=True, exist_ok=True)
            return por_defecto
        except OSError:
            return Path.home()

    def _modo_actual(self):
        return next(i for i, r in self.radios_ajuste.items() if r.get_active())

    def _intervalo_actual(self):
        factor = 60 if self.radio_minutos.get_active() else 1
        return max(INTERVALO_MINIMO, self.spin_intervalo.get_value_as_int() * factor)

    def _hay_slideshow(self):
        return any(len(r) > 1 for r in self.elegido.values())

    def _param_cambiados(self):
        return [t for (sec, clave), c in self.controles.items()
                if c.valor() != self.iniciales_param[(sec, clave)]
                for t in velo_params.expandir(self.conf, sec, clave, c.valor(), c.entre_comillas)]

    def _idioma_estado(self):
        """'sistema' o el código del idioma elegido a mano."""
        return 'sistema' if self.sw_sistema.get_active() else self._idioma_elegido()

    def _idioma_elegido(self):
        return next((c for c, r in self.radios_idioma.items() if r.get_active()), 'en')

    def _idioma_efectivo(self):
        """Código del idioma que se aplica: el del sistema o el elegido."""
        if self.sw_sistema.get_active():
            return velo_params.idioma_del_sistema()
        return self._idioma_elegido()

    def _idioma_cambios(self):
        """Claves del .conf que no coinciden con el idioma que toca (fechas y textos del tema)."""
        codigo = self._idioma_efectivo()
        return [(sec, clave, valor, True) for sec, clave, valor in velo_idiomas.claves(codigo, codigo)
                if self.conf.get(sec, clave, '') != valor]

    def _marcador_desfasado(self):
        """El marcador (primer fotograma) debe existir si y solo si algún fondo es un vídeo."""
        if self.marcador_fallido:
            return False
        hay_video = any(velo_media.tipo(r) == 'video' for rutas in self.elegido.values() for r in rutas)
        return hay_video != bool(self.conf.get('General', 'animated-background-placeholder', ''))

    def _hay_cambios(self):
        return (self.elegido != self.inicial
                or self._marcador_desfasado()
                or self._modo_actual() != self.modo_inicial
                or (self._hay_slideshow() and self._intervalo_actual() != self.intervalo_inicial)
                or bool(self._param_cambiados())
                or self._idioma_estado() != self.idioma_inicial
                or bool(self._idioma_cambios()))

    # ---------- interfaz ----------
    def _construir(self):
        css = Gtk.CssProvider()
        css.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        raiz = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(raiz)

        # Menú lateral + páginas. Orden: General, Fondo, Idioma, grupo Bloqueo, grupo Inicio de sesión.
        self.pila = Gtk.Stack()
        lateral = self.menu = MenuLateral(self.pila)
        cuerpo = Gtk.Box()
        cuerpo.pack_start(lateral, False, False, 0)
        cuerpo.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)
        cuerpo.pack_start(self.pila, True, True, 0)
        raiz.pack_start(cuerpo, True, True, 0)

        def anadir(id_, titulo, widget, en_grupo=False):
            self.pila.add_named(widget, id_)
            lateral.pagina(id_, titulo, en_grupo)

        def pagina_de_ajustes(pagina):
            widget, controles = velo_params.crear_pagina(pagina, self.conf, self._param_cambio)
            self.controles.update(controles)
            if pagina['id'] == 'general':
                widget.pack_start(self._seccion_plantillas(), False, False, 0)
            desplazable = Gtk.ScrolledWindow()
            desplazable.add(widget)
            return desplazable

        sueltas = [p for p in velo_params.PAGINAS if p['grupo'] is None]
        for pagina in sueltas:
            anadir(pagina['id'], pagina['titulo'], pagina_de_ajustes(pagina))
        anadir('fondos', 'Fondo', self._pagina_fondos())
        anadir('idioma', 'Idioma', self._pagina_idioma())
        for grupo in (velo_params.GRUPO_BLOQUEO, velo_params.GRUPO_INICIO):
            lateral.grupo(grupo)
            for pagina in (p for p in velo_params.PAGINAS if p['grupo'] == grupo):
                anadir(pagina['id'], pagina['titulo'], pagina_de_ajustes(pagina), en_grupo=True)
        self.iniciales_param = {k: c.valor() for k, c in self.controles.items()}
        self.pila.show_all()                                # GTK solo cambia a páginas ya visibles
        self.pila.set_visible_child_name('fondos')          # al abrir se ve el Fondo

        # Botones, al final
        raiz.pack_start(Gtk.Separator(), False, False, 0)
        raiz.pack_start(self._barra_inferior(), False, False, 0)
        self._listo = True
        self._actualizar_botones()

    def _seccion_plantillas(self):
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        titulo = Gtk.Label(label='Plantillas', xalign=0)
        titulo.get_style_context().add_class('titulo')
        nota = Gtk.Label(xalign=0, wrap=True, label=(
            'Un punto de partida para el aspecto. Al elegir una se rellenan los ajustes de Bloqueo e '
            'Inicio de sesión (no el fondo, el idioma ni la fuente); revísalos y pulsa Aplicar, o cierra '
            'sin aplicar para descartarlos.'))
        nota.get_style_context().add_class('suave')
        caja.pack_start(titulo, False, False, 0)
        caja.pack_start(nota, False, False, 0)
        self.plantillas = velo_presets.listar(self.tema / 'configs' / 'presets')
        for plantilla in self.plantillas:
            fila = Gtk.Box(spacing=12)
            boton = Gtk.Button(label=plantilla['nombre'])
            boton.set_size_request(150, -1)
            boton.connect('clicked', lambda _b, pl=plantilla: self._usar_plantilla(pl))
            descripcion = Gtk.Label(label=plantilla['descripcion'], xalign=0, wrap=True)
            descripcion.get_style_context().add_class('suave')
            fila.pack_start(boton, False, False, 0)
            fila.pack_start(descripcion, True, True, 0)
            caja.pack_start(fila, False, False, 0)
        caja.set_no_show_all(not self.plantillas)
        return caja

    def _usar_plantilla(self, plantilla):
        puestos = 0
        for seccion, clave, valor in plantilla['valores']:
            control = self.controles.get((seccion, clave))
            if control is not None:
                control.poner(valor)
                puestos += 1
        self._actualizar_botones()
        self._estado(f'Plantilla «{plantilla["nombre"]}» cargada ({puestos} ajustes). '
                     'Revísalos y pulsa Aplicar.')

    def _pagina_fondos(self):
        cont = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16, margin=20)

        # 1. Pestañas: a qué pantalla se aplica el fondo
        self.cuaderno = Gtk.Notebook()
        self.tarjetas = {}
        for id_, texto, titulo in PESTANAS:
            tarjeta = TarjetaFondo(titulo, lambda t=id_: self._elegir_archivo(t),
                                   lambda t=id_: self._elegir_carpeta(t))
            self.tarjetas[id_] = tarjeta
            pagina = Gtk.Box(margin=16)
            pagina.pack_start(tarjeta, True, False, 0)
            self.cuaderno.append_page(pagina, Gtk.Label(label=texto))
        cont.pack_start(self.cuaderno, False, False, 0)

        # 2. Cómo se coloca la imagen y 3. cambio automático
        cont.pack_start(self._seccion_ajuste(), False, False, 0)
        cont.pack_start(self._seccion_intervalo(), False, False, 0)
        desplazable = Gtk.ScrolledWindow()
        desplazable.add(cont)
        return desplazable

    def _pagina_idioma(self):
        cont = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, margin=24)
        titulo = Gtk.Label(label='Idioma', xalign=0)
        titulo.get_style_context().add_class('titulo')
        nota = Gtk.Label(xalign=0, wrap=True, label=(
            'Cambia el idioma de los nombres de día y mes y de los textos del tema (globos de ayuda, '
            '«Iniciando sesión», el mensaje de bloqueo). Es opcional: por defecto se usa el de tu sistema.'))
        nota.get_style_context().add_class('suave')
        fila = Gtk.Box(spacing=12)
        sistema = velo_params.idioma_del_sistema()
        nombre = velo_idiomas.NOMBRES.get(velo_idiomas.base(sistema), sistema)
        fila.pack_start(Gtk.Label(label=f'Usar el idioma de mi sistema: {nombre} ({sistema})'),
                        False, False, 0)
        self.sw_sistema = Gtk.Switch(valign=Gtk.Align.CENTER)
        fila.pack_start(self.sw_sistema, False, False, 0)

        self.radios_idioma = {}
        lista = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, margin=8)
        grupo = None
        for codigo, nombre_idioma in self.idiomas:
            r = Gtk.RadioButton.new_with_label_from_widget(grupo, f'{nombre_idioma}   ({codigo})')
            grupo = grupo or r
            self.radios_idioma[codigo] = r
            lista.pack_start(r, False, False, 0)
        self.marco_idiomas = Gtk.ScrolledWindow(min_content_height=300, vexpand=True)
        self.marco_idiomas.set_shadow_type(Gtk.ShadowType.IN)
        self.marco_idiomas.add(lista)

        manual = self.idioma_inicial != 'sistema'
        self.sw_sistema.set_active(not manual)
        self.radios_idioma[self.idioma_inicial if manual else
                           velo_idiomas.elegir_en_lista(sistema, self.idiomas)].set_active(True)
        self.marco_idiomas.set_sensitive(manual)
        self.lbl_idioma = Gtk.Label(xalign=0, wrap=True)
        self.lbl_idioma.get_style_context().add_class('suave')
        aviso = Gtk.Label(xalign=0, wrap=True, label=(
            'Los textos propios de SDDM (Contraseña, Apagar…) dependen del idioma del sistema y se '
            'ajustan al instalar el tema, no aquí.'))
        aviso.get_style_context().add_class('suave')
        self.sw_sistema.connect('notify::active', self._al_cambiar_idioma)
        for r in self.radios_idioma.values():
            r.connect('toggled', self._al_cambiar_idioma)
        for w in (titulo, nota, fila, self.marco_idiomas, self.lbl_idioma, aviso):
            cont.pack_start(w, w is self.marco_idiomas, w is self.marco_idiomas, 0)
        self._texto_info_idioma()
        return cont

    def _al_cambiar_idioma(self, *_):
        self.marco_idiomas.set_sensitive(not self.sw_sistema.get_active())
        self._texto_info_idioma()
        self._actualizar_botones()

    def _texto_info_idioma(self):
        codigo = self._idioma_efectivo()
        nombre = velo_idiomas.NOMBRES.get(velo_idiomas.base(codigo), codigo)
        if velo_idiomas.tiene_textos(codigo):
            texto = f'Fechas y textos del tema en {nombre}.'
        else:
            texto = (f'Fechas en {nombre}. Los textos del tema aún no están traducidos a este idioma: '
                     'se verán en inglés.')
        self.lbl_idioma.set_text(texto)

    def _param_cambio(self):
        self._actualizar_botones()

    def _seccion_ajuste(self):
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        titulo = Gtk.Label(label='Cómo se coloca la imagen', xalign=0)
        titulo.get_style_context().add_class('seccion')
        fila = Gtk.Box()
        fila.get_style_context().add_class('linked')
        self.radios_ajuste = {}
        grupo = None
        self._descripciones = {}
        for id_, texto, descripcion in AJUSTES_IMAGEN:
            r = Gtk.RadioButton.new_with_label_from_widget(grupo, texto)
            r.set_mode(False)
            grupo = grupo or r
            self.radios_ajuste[id_] = r
            self._descripciones[id_] = descripcion
            fila.pack_start(r, False, False, 0)
        self.lbl_ajuste = Gtk.Label(xalign=0)
        self.lbl_ajuste.get_style_context().add_class('suave')
        self.radios_ajuste[self.modo_inicial].set_active(True)
        self.lbl_ajuste.set_text(self._descripciones[self.modo_inicial])
        for r in self.radios_ajuste.values():
            r.connect('toggled', self._al_cambiar_ajuste)
        for w in (titulo, fila, self.lbl_ajuste):
            caja.pack_start(w, False, False, 0)
        return caja

    def _seccion_intervalo(self):
        self.caja_intervalo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        titulo = Gtk.Label(label='Cambio automático de imágenes', xalign=0)
        titulo.get_style_context().add_class('seccion')
        fila = Gtk.Box(spacing=10)
        fila.pack_start(Gtk.Label(label='Cambiar cada'), False, False, 0)
        segundos = self.intervalo_inicial
        en_minutos = segundos % 60 == 0
        self.spin_intervalo = Gtk.SpinButton.new_with_range(1, 999, 1)
        self.spin_intervalo.set_value(segundos // 60 if en_minutos else segundos)
        unidades = Gtk.Box()
        unidades.get_style_context().add_class('linked')
        self.radio_segundos = Gtk.RadioButton.new_with_label_from_widget(None, 'Segundos')
        self.radio_minutos = Gtk.RadioButton.new_with_label_from_widget(self.radio_segundos, 'Minutos')
        for r in (self.radio_segundos, self.radio_minutos):
            r.set_mode(False)
            unidades.pack_start(r, False, False, 0)
        (self.radio_minutos if en_minutos else self.radio_segundos).set_active(True)
        self.spin_intervalo.connect('value-changed', lambda _w: self._actualizar_botones())
        self.radio_minutos.connect('toggled', lambda _w: self._actualizar_botones())
        fila.pack_start(self.spin_intervalo, False, False, 0)
        fila.pack_start(unidades, False, False, 0)
        self.lbl_intervalo = Gtk.Label(xalign=0, wrap=True)
        self.lbl_intervalo.get_style_context().add_class('suave')
        for w in (titulo, fila, self.lbl_intervalo):
            self.caja_intervalo.pack_start(w, False, False, 0)
        return self.caja_intervalo

    def _barra_inferior(self):
        barra = Gtk.Box(spacing=8, margin=12)
        self.estado = Gtk.Label(xalign=0, wrap=True)
        self.estado.get_style_context().add_class('suave')
        self.btn_aplicar = Gtk.Button(label='Aplicar')
        self.btn_aplicar.connect('clicked', lambda _b: self._guardar(cerrar=False))
        self.btn_aceptar = Gtk.Button(label='Aceptar')
        self.btn_aceptar.get_style_context().add_class('suggested-action')
        self.btn_aceptar.connect('clicked', self._al_aceptar)
        self.btn_cerrar = Gtk.Button(label='Cerrar')
        self.btn_cerrar.connect('clicked', lambda _b: self.close())
        self.btn_sistema = Gtk.Button(label='Aplicar al sistema')
        self.btn_sistema.set_tooltip_text('Lleva la configuración a la pantalla de inicio de sesión real (abre una terminal para pedir la contraseña).')
        self.btn_sistema.connect('clicked', self._al_aplicar_sistema)
        self.btn_probar = Gtk.Button(label='Probar')
        self.btn_probar.set_tooltip_text('Abre una vista previa de la pantalla de inicio con los ajustes guardados.')
        self.btn_probar.connect('clicked', self._al_probar)
        barra.pack_start(self.btn_probar, False, False, 0)
        barra.pack_start(self.btn_sistema, False, False, 0)
        barra.pack_start(self.estado, True, True, 0)
        for b in (self.btn_aceptar, self.btn_aplicar, self.btn_cerrar):   # orden habitual de KDE
            barra.pack_start(b, False, False, 0)
        return barra

    # ---------- acciones ----------
    def _al_cambiar_ajuste(self, boton):
        if boton.get_active():
            self.lbl_ajuste.set_text(self._descripciones[self._modo_actual()])
            self._actualizar_botones()

    def _asignar(self, destino, rutas):
        """destino: 'ambas', 'LockScreen' o 'LoginScreen'. rutas: lista de archivos."""
        for seccion in (PANTALLAS if destino == 'ambas' else [destino]):
            self.elegido[seccion] = [Path(r) for r in rutas]
        self._refrescar_tarjetas()

    def _refrescar_tarjetas(self):
        bloqueo, inicio = self.elegido['LockScreen'], self.elegido['LoginScreen']
        if bloqueo == inicio:
            self.tarjetas['ambas'].mostrar(bloqueo, self.ejecutor)
        else:
            self.tarjetas['ambas'].mostrar_texto(
                'Cada pantalla tiene un fondo distinto',
                f'Bloqueo: {self._texto_lista(bloqueo)}\nInicio de sesión: {self._texto_lista(inicio)}\n'
                'Si eliges un archivo aquí, se aplicará a las dos.')
        self.tarjetas['LockScreen'].mostrar(bloqueo, self.ejecutor)
        self.tarjetas['LoginScreen'].mostrar(inicio, self.ejecutor)
        self._actualizar_botones()

    @staticmethod
    def _texto_lista(rutas):
        return rutas[0].name if len(rutas) == 1 else f'{len(rutas)} imágenes que cambian solas'

    def _elegir_archivo(self, destino):
        que = 'las dos pantallas' if destino == 'ambas' else PANTALLAS[destino]
        dlg = Gtk.FileChooserNative.new(f'Fondo para {que}', self, Gtk.FileChooserAction.OPEN,
                                        'Elegir', 'Cancelar')
        filtro = Gtk.FileFilter()
        filtro.set_name('Imágenes y vídeos')
        for ext in sorted(velo_media.IMAGENES | velo_media.VIDEOS):
            filtro.add_pattern(f'*{ext}')
            filtro.add_pattern(f'*{ext.upper()}')
        dlg.add_filter(filtro)
        dlg.set_current_folder(str(self._carpeta_selector()))
        if dlg.run() != Gtk.ResponseType.ACCEPT or not dlg.get_filename():
            return
        ruta = Path(dlg.get_filename())
        if not velo_media.tipo(ruta):
            self._estado('Ese tipo de archivo no vale como fondo (los .gif pueden colgar SDDM).')
            return
        self._recordar_carpeta(ruta.parent)
        self._asignar(destino, [ruta])

    def _elegir_carpeta(self, destino):
        que = 'las dos pantallas' if destino == 'ambas' else PANTALLAS[destino]
        dlg = Gtk.FileChooserNative.new(f'Carpeta de imágenes para {que}', self,
                                        Gtk.FileChooserAction.SELECT_FOLDER, 'Usar esta carpeta', 'Cancelar')
        dlg.set_current_folder(str(self._carpeta_selector()))
        if dlg.run() != Gtk.ResponseType.ACCEPT or not dlg.get_filename():
            return
        carpeta = Path(dlg.get_filename())
        imagenes, error = velo_media.imagenes_de_carpeta(carpeta)
        if error:
            self._estado(error)
            return
        self._recordar_carpeta(carpeta)
        self._asignar(destino, imagenes)

    def _recordar_carpeta(self, carpeta):
        self.ajustes['ultima_carpeta'] = str(carpeta)
        guardar_ajustes(self.ajustes)

    def _al_aceptar(self, _boton):
        if self._hay_cambios():
            self._guardar(cerrar=True)
        else:
            self.close()

    def _guardar(self, cerrar=False, luego=None):
        if self.ocupado or not self._hay_cambios():
            return
        self.ocupado = True
        self.cerrar_al_guardar = cerrar
        self.luego_guardar = luego
        self._actualizar_botones()
        self._estado('Guardando… (si el vídeo es grande puede tardar unos segundos)')
        elegido = {s: list(r) for s, r in self.elegido.items()}
        modo = self._modo_actual()
        intervalo = self._intervalo_actual()
        parametros = self._param_cambiados() + self._idioma_cambios()
        idioma_estado = self._idioma_estado()

        def trabajo():
            try:
                nombres = {}
                for seccion, rutas in elegido.items():
                    nombres[seccion] = [
                        r.name if r.parent.resolve() == self.fondos.resolve()
                        else velo_media.copiar_al_tema(r, self.fondos)
                        for r in rutas]
                for seccion, lista in nombres.items():
                    self.conf.set(seccion, 'background', SEPARADOR.join(lista))
                video = next((n for lista in nombres.values() for n in lista
                              if velo_media.tipo(self.fondos / n) == 'video'), None)
                # con vídeo, su primer fotograma sirve de marcador mientras carga; sin vídeo, no hace falta
                marcador = velo_media.crear_marcador(self.fondos / video, self.fondos) if video else ''
                self.marcador_fallido = bool(video) and not marcador
                self.conf.set('General', 'animated-background-placeholder', marcador)
                self.conf.set('General', 'background-fill-mode', modo)
                principal = velo_pantallas.principal_de_kde()
                if principal:
                    self.conf.set('General', 'primary-screen', principal)
                for seccion, clave, valor, entre_comillas in parametros:
                    self.conf.set(seccion, clave, valor, texto=entre_comillas)
                if any(len(lista) > 1 for lista in nombres.values()):
                    self.conf.set('General', 'slideshow-interval', intervalo, texto=False)
                copia = self.conf.guardar()
                limpieza = self._limpiar_sobrantes()
                GLib.idle_add(self._guardado_ok, nombres, modo, intervalo, copia, limpieza, parametros, idioma_estado)
            except Exception as e:   # noqa: BLE001 - se muestra al usuario
                GLib.idle_add(self._guardado_error, str(e))
        self.ejecutor.submit(trabajo)

    def _limpiar_sobrantes(self):
        """Mueve a la papelera los fondos del tema que ya no usa ninguna configuración."""
        textos = [p.read_text(encoding='utf-8', errors='ignore')
                  for p in self.conf.ruta.parent.glob('*.conf')]
        sobran = velo_media.huerfanos(self.fondos, textos)
        mb = sum(p.stat().st_size for p in sobran) / 1_048_576
        movidos, fallos = velo_media.a_la_papelera(sobran)
        return {'movidos': len(movidos), 'fallos': len(fallos), 'mb': mb}

    def _guardado_ok(self, nombres, modo, intervalo, copia, limpieza, parametros, idioma_estado):
        self.ocupado = False
        self.inicial = {s: [self.fondos / n for n in lista] for s, lista in nombres.items()}
        self.elegido = {s: list(r) for s, r in self.inicial.items()}
        self.modo_inicial = modo
        for seccion, clave, valor, _q in parametros:
            for llave in ((seccion, clave), ('*', clave)):
                if llave in self.iniciales_param:
                    self.iniciales_param[llave] = valor
        self.idioma_inicial = idioma_estado
        self.ajustes['idioma'] = idioma_estado
        guardar_ajustes(self.ajustes)
        if any(len(lista) > 1 for lista in nombres.values()):
            self.intervalo_inicial = intervalo
        self._refrescar_tarjetas()
        texto = f'Aplicado. Copia de seguridad: {copia.name}.'
        if limpieza['movidos']:
            texto += (f' A la papelera: {limpieza["movidos"]} fondo(s) que ya no se usaban '
                      f'({limpieza["mb"]:.0f} MB).')
        if limpieza['fallos']:
            texto += f' No se pudieron quitar {limpieza["fallos"]} archivo(s) sobrantes.'
        luego, self.luego_guardar = self.luego_guardar, None
        if luego:
            self._estado(texto)
            luego()
            return False
        if velo_sistema.diferencias(self.tema):
            texto += ' Para verlo al iniciar sesión pulsa «Aplicar al sistema».'
        self._estado(texto)
        if self.cerrar_al_guardar:
            self.close()
        return False

    def _guardado_error(self, mensaje):
        self.ocupado = False
        self.cerrar_al_guardar = False
        self.luego_guardar = None
        self._actualizar_botones()
        self._estado(f'No se pudo guardar: {mensaje}')
        return False

    # ---------- pantalla de inicio del sistema ----------
    def _al_probar(self, _boton):
        if self.ocupado:
            return
        pendiente = self._hay_cambios()
        texto = ('Se abrirá una ventana con la pantalla de bloqueo y la de inicio de sesión tal como quedan '
                 'con tus ajustes. No se puede iniciar sesión desde ahí: es solo una vista previa.\n\n'
                 'Para cerrarla: pulsa Alt+F4 o la tecla Meta (Windows). Si no la cierras, se cierra sola '
                 f'a los {velo_sistema.TIEMPO_PRUEBA // 60} minutos.\n\n'
                 'Dentro de la prueba: cualquier tecla pasa del bloqueo al inicio de sesión y Esc vuelve.')
        if pendiente:
            texto += '\n\nAntes se guardarán los cambios pendientes (con copia de seguridad).'
        dlg = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.INFO,
                                text='Probar la pantalla de inicio', secondary_text=texto)
        dlg.add_button('Cancelar', Gtk.ResponseType.CANCEL)
        dlg.add_button('Probar', Gtk.ResponseType.OK)
        respuesta = dlg.run()
        dlg.destroy()
        if respuesta != Gtk.ResponseType.OK:
            return
        if pendiente:
            self._guardar(cerrar=False, luego=self._lanzar_prueba)
        else:
            self._lanzar_prueba()

    def _lanzar_prueba(self):
        self.ocupado = True
        self._actualizar_botones()
        self._estado('Prueba en marcha: ciérrala con Alt+F4 o la tecla Meta (Windows).')

        def trabajo():
            ok, mensaje = velo_sistema.probar(self.tema)
            GLib.idle_add(self._prueba_terminada, ok, mensaje)
        self.ejecutor.submit(trabajo)

    def _prueba_terminada(self, ok, mensaje):
        self.ocupado = False
        self._actualizar_botones()
        self.present()
        self._estado(mensaje if ok else f'No se pudo probar: {mensaje}')
        return False

    def _comprobar_sistema(self):
        self._estado(velo_sistema.texto_estado(velo_sistema.diferencias(self.tema)))
        return False

    def _seguir_pantalla_principal(self):
        """Apunta en la configuración la pantalla principal de KDE (el inicio de sesión sale en esa)."""
        nombre = velo_pantallas.principal_de_kde()
        if nombre and self.conf.get('General', 'primary-screen', '') != nombre:
            self.conf.set('General', 'primary-screen', nombre)
            self.conf.guardar()

    def _al_aplicar_sistema(self, _boton):
        if self.ocupado:
            return
        self._seguir_pantalla_principal()
        dlg = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
            text='Cambiar la pantalla de inicio necesita permiso de administrador',
            secondary_text='Sin ese permiso no se puede aplicar. Se abrirá una terminal: escribe tu '
                           'contraseña (no se ve al escribir) y pulsa Intro. Se cerrará sola y volverás aquí.')
        dlg.add_button('Cancelar', Gtk.ResponseType.CANCEL)
        dlg.add_button('Continuar', Gtk.ResponseType.OK)
        respuesta = dlg.run()
        dlg.destroy()
        if respuesta != Gtk.ResponseType.OK:
            return
        if self._hay_cambios():
            self._guardar(cerrar=False, luego=self._enviar_al_sistema)
        else:
            self._enviar_al_sistema()

    def _enviar_al_sistema(self):
        self.ocupado = True
        self._actualizar_botones()
        self._estado('Esperando en la terminal: escribe tu contraseña allí…')

        def trabajo():
            ok, mensaje = velo_sistema.aplicar(self.tema)
            GLib.idle_add(self._sistema_terminado, ok, mensaje)
        self.ejecutor.submit(trabajo)

    def _sistema_terminado(self, ok, mensaje):
        self.ocupado = False
        self._actualizar_botones()
        self.present()                       # vuelve a primer plano al cerrarse la terminal
        if ok:
            self._estado('Listo: la pantalla de inicio está actualizada. Se verá la próxima vez que '
                         f'cierres sesión o reinicies. ({mensaje})')
        else:
            self._estado(f'No se aplicó al sistema: {mensaje}')
        return False

    # ---------- utilidades ----------
    def _estado(self, texto):
        self.estado.set_text(texto)

    def _actualizar_botones(self):
        if not self._listo:
            return
        self.btn_aplicar.set_sensitive(self._hay_cambios() and not self.ocupado)
        self.btn_aceptar.set_sensitive(not self.ocupado)
        self.btn_sistema.set_sensitive(not self.ocupado)
        self.btn_probar.set_sensitive(not self.ocupado)
        hay = self._hay_slideshow()
        self.caja_intervalo.set_sensitive(hay)
        self.lbl_intervalo.set_text(
            'Solo hace falta si eliges varias imágenes en una pantalla.' if not hay else
            f'Las imágenes cambiarán cada {self._texto_intervalo(self._intervalo_actual())}.')

    @staticmethod
    def _texto_intervalo(segundos):
        if segundos % 60 == 0:
            m = segundos // 60
            return f'{m} minuto' + ('' if m == 1 else 's')
        return f'{segundos} segundos'

    def _al_cerrar(self, *_):
        if self.ocupado:
            return True
        if not self._hay_cambios():
            return False
        dlg = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                                text='Hay cambios sin aplicar',
                                secondary_text='Si sales ahora se pierden.')
        dlg.add_button('Volver', Gtk.ResponseType.CANCEL)
        dlg.add_button('Salir sin aplicar', Gtk.ResponseType.OK)
        respuesta = dlg.run()
        dlg.destroy()
        return respuesta != Gtk.ResponseType.OK


def main():
    tema = Path(sys.argv[1]) if len(sys.argv) > 1 else TEMA_POR_DEFECTO
    if not (tema / 'metadata.desktop').exists():
        print(f'No parece una carpeta del tema Velo: {tema}', file=sys.stderr)
        return 1
    GLib.set_prgname('velo-gui')         # agrupa la ventana con el lanzador del menú
    GLib.set_application_name(TITULO)
    Gdk.set_program_class('velo-gui')
    if Gtk.IconTheme.get_default().has_icon('velo'):
        Gtk.Window.set_default_icon_name('velo')
    else:                                # todavía sin lanzador instalado: se usa el icono de la carpeta
        try:
            Gtk.Window.set_default_icon_from_file(str(Path(__file__).resolve().parent / 'velo.svg'))
        except GLib.Error:
            pass
    ventana = Ventana(tema)
    ventana.connect('destroy', Gtk.main_quit)
    ventana.show_all()
    Gtk.main()
    return 0


if __name__ == '__main__':
    sys.exit(main())
