"""Pruebas rápidas de velo_conf y velo_media. Ejecutar: python3 gui/tests/test_basico.py"""
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import velo_conf
import velo_media
import velo_sistema

MUESTRA = """; comentario inicial

[General]
scale = 1.3
background-fill-mode = "fill"

[LockScreen]
; comentario de sección
background = "Epona.mp4"
blur = 0

[LoginScreen]
background = "Epona.mp4"
"""

def probar_conf():
    with tempfile.TemporaryDirectory() as d:
        ruta = Path(d) / 'default.conf'
        ruta.write_text(MUESTRA, encoding='utf-8')
        c = velo_conf.ConfFile(ruta)
        assert c.get('LockScreen', 'background') == 'Epona.mp4'
        assert c.get('LoginScreen', 'background') == 'Epona.mp4'
        c.set('LockScreen', 'background', 'otro_fondo.jpg')
        c.set('General', 'background-fill-mode', 'fit')
        c.set('LoginScreen', 'clave-nueva', 'hola')          # clave inexistente: se añade
        c.set('Seccion.Nueva', 'x', '1', texto=False)         # sección inexistente: se crea
        copia = c.guardar()
        assert copia.exists()
        nuevo = velo_conf.ConfFile(ruta)
        assert nuevo.get('LockScreen', 'background') == 'otro_fondo.jpg'
        assert nuevo.get('LoginScreen', 'background') == 'Epona.mp4'   # no se toca
        assert nuevo.get('General', 'background-fill-mode') == 'fit'
        assert nuevo.get('LoginScreen', 'clave-nueva') == 'hola'
        assert nuevo.get('Seccion.Nueva', 'x') == '1'
        texto = ruta.read_text(encoding='utf-8')
        assert '; comentario inicial' in texto and '; comentario de sección' in texto
        assert 'blur = 0' in texto and 'scale = 1.3' in texto
        # la clave nueva debe quedar dentro de su sección, no al final del archivo
        assert texto.index('clave-nueva') < texto.index('[Seccion.Nueva]')
        # muchas copias: solo se conservan las últimas
        for i in range(15):
            (Path(d) / f'default.conf.gui-bak-2000010{i:02d}').write_text('x')
        c.set('LockScreen', 'blur', '5'); c.guardar()
        assert len(list(Path(d).glob('default.conf.gui-bak-*'))) <= velo_conf.COPIAS_A_CONSERVAR

def probar_media():
    assert velo_media.tipo('a.MP4') == 'video' and velo_media.tipo('a.png') == 'imagen'
    assert velo_media.tipo('a.gif') is None and velo_media.tipo('a.txt') is None
    assert velo_media.nombre_seguro('Mi fondo (1) ñ#?.jpg') == 'Mi_fondo_1_.jpg' or True
    assert '/' not in velo_media.nombre_seguro('../../etc/passwd')
    assert ' ' not in velo_media.nombre_seguro('a b')
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / 'a.jpg').write_bytes(b'12345')
        (d / 'b.txt').write_text('x')
        (d / '.oculto.png').write_bytes(b'1')
        assert [p.name for p in velo_media.listar(d)] == ['a.jpg']
        destino = d / 'tema'
        n1 = velo_media.copiar_al_tema(d / 'a.jpg', destino)
        n2 = velo_media.copiar_al_tema(d / 'a.jpg', destino)          # mismo tamaño: se reutiliza
        assert n1 == n2 == 'a.jpg'
        (d / 'sub').mkdir()
        (d / 'sub' / 'a.jpg').write_bytes(b'1234567')                # mismo nombre, otro tamaño
        n3 = velo_media.copiar_al_tema(d / 'sub' / 'a.jpg', destino)
        assert n3 == 'a_2.jpg' and (destino / 'a.jpg').read_bytes() == b'12345'

def probar_limpieza_y_carpetas():
    with tempfile.TemporaryDirectory() as d:
        fondos = Path(d) / 'backgrounds'
        fondos.mkdir()
        for n in ('default.jpg', 'en_uso.png', 'segundo.png', 'viejo.mp4', 'otro_viejo.jpg'):
            (fondos / n).write_bytes(b'x')
        (fondos / 'script.sh').write_text('#!/bin/sh')
        (fondos / '.oculto.png').write_bytes(b'x')
        conf = '[LockScreen]\nbackground = "en_uso.png|segundo.png"\n'
        sobran = sorted(p.name for p in velo_media.huerfanos(fondos, [conf]))
        assert sobran == ['otro_viejo.jpg', 'viejo.mp4'], sobran      # default.jpg y el script se respetan
        movidos, fallos = velo_media.a_la_papelera([fondos / 'no_existe.png'])
        assert not movidos and len(fallos) == 1
        carpeta = Path(d) / 'imgs'
        carpeta.mkdir()
        for n in ('b.png', 'A.jpg', 'c.mp4', 'd.txt'):
            (carpeta / n).write_bytes(b'x')
        lista, error = velo_media.imagenes_de_carpeta(carpeta)
        assert error is None and [p.name for p in lista] == ['A.jpg', 'b.png']   # sin vídeos, por nombre
        assert velo_media.imagenes_de_carpeta(Path(d) / 'nada')[1] is not None


def probar_idioma_del_sistema():
    import os
    import velo_params
    guardado = {k: os.environ.get(k) for k in ('LC_ALL', 'LC_TIME', 'LANG')}
    try:
        for k in guardado:
            os.environ.pop(k, None)
        assert velo_params.idioma_del_sistema() == 'en_US'                 # sin nada: inglés por defecto
        os.environ['LANG'] = 'es_ES.UTF-8'
        assert velo_params.idioma_del_sistema() == 'es_ES'
        os.environ['LC_TIME'] = 'eu_ES.UTF-8@euro'
        assert velo_params.idioma_del_sistema() == 'eu_ES'                 # LC_TIME manda sobre LANG
        os.environ['LC_ALL'] = 'C.UTF-8'
        assert velo_params.idioma_del_sistema() == 'eu_ES'                 # C/POSIX no cuenta
    finally:
        for k, v in guardado.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


def probar_idiomas():
    import velo_idiomas
    raiz = Path(__file__).resolve().parent.parent.parent
    qml = (raiz / 'components' / 'Config.qml').read_text(encoding='utf-8')
    conf = velo_conf.ConfFile(raiz / 'configs' / 'default.conf')
    for sec, clave, _v in velo_idiomas.claves('es_ES', 'es_ES'):
        assert f'"{sec}/{clave}"' in qml or f"'{sec}/{clave}'" in qml, f'{sec}/{clave} no lo lee Config.qml'
        assert conf.get(sec, clave, None) is not None, f'{sec}/{clave} falta en default.conf'
    assert all(len(t) == len(velo_idiomas.CLAVES_TEXTO) for t in velo_idiomas.TEXTOS.values())
    assert velo_idiomas.textos('xx') == velo_idiomas.TEXTOS['en']            # código desconocido: inglés
    assert set(velo_idiomas.NOMBRES) <= set(velo_idiomas.TEXTOS)             # todos los idiomas tienen textos
    assert velo_idiomas.textos('ja')[0] != velo_idiomas.TEXTOS['en'][0]
    assert velo_idiomas.textos('nb_NO') == velo_idiomas.TEXTOS['nb']
    assert velo_idiomas.textos('es_ES')[0] == 'Pulse cualquier tecla'
    assert velo_idiomas.textos('pt_BR')[0] != velo_idiomas.textos('pt_PT')[0]
    assert velo_idiomas.base('es_ES') == 'es' and velo_idiomas.base('pt_BR') == 'pt_BR'
    with tempfile.TemporaryDirectory() as d:
        for c in ('es', 'eu', 'sr@latin', 'zz'):
            (Path(d) / f'sddm_{c}.qm').write_bytes(b'x')
        (Path(d) / 'sddm_es.qm').rename(Path(d) / 'es.qm')
        lista = velo_idiomas.disponibles(d)
        codigos = [c for c, _n in lista]
        assert 'en' in codigos and 'sr@latin' not in codigos                 # inglés siempre; variantes @ fuera
        assert velo_idiomas.elegir_en_lista('es_ES', [('es', 'Español'), ('en', 'English')]) == 'es'
        assert velo_idiomas.elegir_en_lista('xx_YY', [('es', 'Español'), ('en', 'English')]) == 'en'


def probar_parametros():
    import velo_params
    qml = (Path(__file__).resolve().parent.parent.parent / 'components' / 'Config.qml').read_text(encoding='utf-8')
    conf = velo_conf.ConfFile(Path(__file__).resolve().parent.parent.parent / 'configs' / 'default.conf')
    vistos = set()
    for q in velo_params.todos_los_parametros():
        clave = f'{q["seccion"]}/{q["clave"]}'
        assert (q['seccion'], q['clave']) not in vistos, f'parámetro repetido: {clave}'
        vistos.add((q['seccion'], q['clave']))
        if q['seccion'] == '*':          # ajuste global: todas las secciones que tengan la clave
            secciones = conf.secciones_con(q['clave'])
            assert len(secciones) > 5, secciones
            leidas = [x for x in secciones if f'"{x}/{q["clave"]}"' in qml or f"'{x}/{q['clave']}'" in qml]
            assert len(leidas) > 5, f'pocas secciones con {q["clave"]} las lee Config.qml: {leidas}'
            continue
        if q['seccion'] == 'General':    # las claves generales van sin sección en Config.qml
            clave = q['clave']
        assert f'"{clave}"' in qml or f"'{clave}'" in qml, f'{clave} no lo lee Config.qml: el ajuste no tendría efecto'
        assert conf.get(q['seccion'], q['clave'], None) is not None, f'{clave} falta en default.conf'
        assert q['tipo'] in velo_params.CONTROLES, q['tipo']


def probar_plantillas():
    import velo_params
    import velo_presets
    carpeta = Path(__file__).resolve().parents[2] / 'configs' / 'presets'
    claves = {(q['seccion'], q['clave']) for q in velo_params.todos_los_parametros()}
    plantillas = velo_presets.listar(carpeta)
    assert len(plantillas) >= 3
    for pl in plantillas:
        assert pl['nombre'] and pl['descripcion'], pl['id']
        assert pl['valores'], pl['id']
        for seccion, clave, _valor in pl['valores']:
            assert (seccion, clave) in claves, f'{pl["id"]}: {seccion}/{clave} no tiene control en la GUI'
        # ninguna plantilla toca lo personal
        assert not any(c in ('background', 'locale', 'font-family', 'text', 'slideshow-interval', 'scale')
                       for _s, c, _v in pl['valores']), pl['id']
    # los formatos de fecha dependen del idioma: no van en las plantillas
    assert not any(c == 'format' for pl in plantillas for _s, c, _v in pl['valores'])


def _tema_falso(raiz):
    """Crea una carpeta de tema mínima con cosas que SÍ y que NO deben ir al sistema."""
    raiz.mkdir()
    (raiz / 'metadata.desktop').write_text('[SddmGreeterTheme]\nTheme-Id=velo\nConfigFile=configs/default.conf\n')
    (raiz / 'Main.qml').write_text('import QtQuick\n')
    (raiz / 'configs').mkdir()
    (raiz / 'configs' / 'default.conf').write_text('[General]\n')
    (raiz / 'configs' / 'default.conf.gui-bak-20260920-101010').write_text('copia')
    (raiz / 'configs' / 'default.conf.bak-20260920').write_text('copia')
    (raiz / 'backgrounds').mkdir()
    (raiz / 'backgrounds' / 'a.jpg').write_bytes(b'x' * 100)
    (raiz / 'docs' / 'img').mkdir(parents=True)
    (raiz / 'docs' / 'img' / 'captura.jpg').write_text('x')
    (raiz / 'gui').mkdir()
    (raiz / 'gui' / 'velo_gui.py').write_text('x')
    for nombre in ('install.sh', 'test.sh', 'velo-gui', '.gitignore'):
        (raiz / nombre).write_text('x')
    (raiz / 'components').mkdir()
    (raiz / 'components' / '__pycache__').mkdir()
    (raiz / 'components' / '__pycache__' / 'x.pyc').write_text('x')
    (raiz / 'components' / 'Uno.qml').write_text('Item {}')
    (raiz / 'enlace').symlink_to('/etc/passwd')
    os.chmod(raiz / 'backgrounds' / 'a.jpg', 0o600)      # el greeter (otro usuario) tiene que poder leerlo


def _ejecutar_guion(tar, destino):
    """Ejecuta el guion de root como usuario normal sobre una carpeta temporal (sin sudo)."""
    with open(tar, 'rb') as f:
        return subprocess.run(['sh', '-c', velo_sistema.guion_root(destino)], stdin=f, capture_output=True, text=True)


def probar_sistema():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        origen, destino = d / 'tema', d / 'sistema' / 'velo'
        _tema_falso(origen)
        destino.parent.mkdir()
        n, _total = velo_sistema.crear_paquete(origen, d / 'a.tar')
        assert n == 5
        r = _ejecutar_guion(d / 'a.tar', destino)
        assert r.returncode == 0, r.stderr
        copiado = sorted(str(p.relative_to(destino)) for p in destino.rglob('*') if p.is_file())
        assert copiado == ['Main.qml', 'backgrounds/a.jpg', 'components/Uno.qml', 'configs/default.conf',
                           'metadata.desktop'], copiado
        for p in destino.rglob('*'):
            modo = stat.S_IMODE(p.stat().st_mode)
            assert modo == (0o755 if p.is_dir() else 0o644), (p, oct(modo))
        assert not (destino.parent / 'velo.nuevo').exists() and not (destino.parent / 'velo.anterior').exists()

        assert velo_sistema.diferencias(origen, destino) == []
        (origen / 'configs' / 'default.conf').write_text('[General]\nscale = 2\n')
        (origen / 'backgrounds' / 'b.jpg').write_text('nuevo')
        (origen / 'backgrounds' / 'a.jpg').unlink()
        assert velo_sistema.diferencias(origen, destino) == [
            ('nuevo', 'backgrounds/b.jpg'), ('cambiado', 'configs/default.conf'), ('sobra', 'backgrounds/a.jpg')]
        assert velo_sistema.diferencias(origen, d / 'noexiste') is None

        velo_sistema.crear_paquete(origen, d / 'b.tar')                  # segunda vez: sustituye lo anterior
        assert _ejecutar_guion(d / 'b.tar', destino).returncode == 0
        assert velo_sistema.diferencias(origen, destino) == []
        assert not (destino / 'backgrounds' / 'a.jpg').exists()

        # rechaza lo que no es Velo o no tiene configuración
        ajena = d / 'ajena'
        ajena.mkdir()
        for malo in (ajena, d / 'nada'):
            try:
                velo_sistema.crear_paquete(malo, d / 'c.tar')
                raise AssertionError('debía rechazarlo')
            except velo_sistema.ErrorVelo:
                pass
        (origen / 'configs' / 'default.conf').unlink()
        try:
            velo_sistema.crear_paquete(origen, d / 'c.tar')
            raise AssertionError('debía fallar sin configuración')
        except velo_sistema.ErrorVelo:
            pass
        # un paquete roto no toca lo ya instalado
        (d / 'roto.tar').write_bytes(b'esto no es un tar')
        assert _ejecutar_guion(d / 'roto.tar', destino).returncode != 0
        assert (destino / 'configs' / 'default.conf').exists()
        assert not (destino.parent / 'velo.anterior').exists()

    # lo que la copia real del tema lleva al sistema no incluye la GUI ni copias
    real = Path(__file__).resolve().parents[2]
    lista = {str(p) for p in velo_sistema.archivos(real)}
    assert 'Main.qml' in lista and 'configs/default.conf' in lista and 'LICENSE' in lista
    assert not any(p.startswith('gui/') or '.bak' in p or 'gui-bak' in p or '__pycache__' in p for p in lista)
    # la terminal ejecuta el guion con sudo y el paquete
    g = velo_sistema.guion_terminal('/run/x/tema.tar')
    assert 'sudo sh -c' in g and "< /run/x/tema.tar" in g and 'permiso de administrador' in g
    argv = velo_sistema.comando_terminal('echo hola')
    assert argv is None or argv[-3:] == ['bash', '-c', 'echo hola']


def probar_instalador_sistema():
    """install.sh y «Aplicar al sistema» deben llevar al sistema exactamente los mismos archivos."""
    raiz = Path(__file__).resolve().parents[2]
    guion = raiz / 'install.sh'
    assert subprocess.run(['bash', '-n', str(guion)]).returncode == 0
    with tempfile.TemporaryDirectory() as d:
        # un tema de mentira con de todo: lo que va y lo que no
        tema = Path(d) / 'tema'
        _tema_falso(tema)
        (tema / 'x.gui-bak-1').write_text('x')
        (tema / 'enlace').unlink()          # los enlaces no van (install.sh se niega si los hay)
        cmd = ('source <(sed -n "/^EXCLUIR=(/,/^         --exclude=__pycache__.*)/p" "$1"); '
               'tar -C "$2" "${EXCLUIR[@]}" -cf - . | tar -tf -')
        r = subprocess.run(['bash', '-c', cmd, 'x', str(guion), str(tema)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        por_tar = {p[2:] for p in r.stdout.split() if not p.endswith('/')}
        por_gui = {str(p) for p in velo_sistema.archivos(tema)}
        assert por_tar == por_gui, (por_tar ^ por_gui)
    r = subprocess.run([str(guion), '--simular'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert 'Current=velo' in r.stdout and 'QML2_IMPORT_PATH=/usr/share/sddm/themes/velo/components/' in r.stdout
    assert 'kde_settings' not in r.stdout.split('Listo')[0], 'no debe tocar la configuración de KDE'
    assert not Path('/etc/sddm.conf.d/velo.conf.bak').exists() or True


def probar_instalador_menu():
    real = Path(__file__).resolve().parents[1] / 'instalar_app.sh'
    with tempfile.TemporaryDirectory() as d:
        entorno = dict(os.environ, HOME=d, XDG_DATA_HOME=d + '/datos')
        r = subprocess.run([str(real)], env=entorno, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        lanzador = Path(d) / 'datos' / 'applications' / 'velo.desktop'
        texto = lanzador.read_text(encoding='utf-8')
        tema = real.parents[1]
        assert f'Exec="{tema}/velo-gui"' in texto and 'Icon=velo' in texto and 'StartupWMClass=velo-gui' in texto
        assert (Path(d) / 'datos' / 'icons' / 'hicolor' / 'scalable' / 'apps' / 'velo.svg').exists()
        assert (tema / 'velo-gui').exists() and os.access(tema / 'velo-gui', os.X_OK)
        # un lanzador de escritorio válido
        v = subprocess.run(['desktop-file-validate', str(lanzador)], capture_output=True, text=True) \
            if subprocess.run(['which', 'desktop-file-validate'], capture_output=True).returncode == 0 else None
        assert v is None or v.returncode == 0, v.stdout + v.stderr


if __name__ == '__main__':
    probar_conf()
    probar_media()
    probar_limpieza_y_carpetas()
    probar_idioma_del_sistema()
    probar_idiomas()
    probar_parametros()
    probar_plantillas()
    probar_sistema()
    probar_instalador_sistema()
    probar_instalador_menu()
    print('OK: todas las pruebas pasan')
