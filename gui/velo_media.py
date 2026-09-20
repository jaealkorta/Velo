"""Ayudas para imágenes y vídeos de fondo: listar, describir, miniaturas y copiar.

Todo es local: solo usa ffmpeg/ffprobe y la carpeta de caché del usuario.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

IMAGENES = {'.jpg', '.jpeg', '.png'}
VIDEOS = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm'}   # .gif no: puede colgar SDDM
CACHE = Path.home() / '.cache' / 'velo-gui'

# A partir de aquí un vídeo se considera pesado para una pantalla de inicio.
AVISO_MB = 25
AVISO_ALTO = 1080
AVISO_FPS = 30

# Carpeta con imágenes que cambian solas: tope y aviso de peso total.
MAX_IMAGENES_CARPETA = 50
AVISO_TOTAL_MB = 200


def tipo(ruta):
    ext = Path(ruta).suffix.lower()
    if ext in IMAGENES:
        return 'imagen'
    if ext in VIDEOS:
        return 'video'
    return None


def listar(carpeta):
    """Imágenes y vídeos válidos de una carpeta (sin entrar en subcarpetas)."""
    try:
        return sorted(
            (p for p in Path(carpeta).iterdir()
             if p.is_file() and not p.name.startswith('.') and tipo(p)),
            key=lambda p: p.name.lower())
    except OSError:
        return []


def nombre_seguro(nombre):
    """Nombre apto para el tema (Qt lo usa dentro de una URL)."""
    limpio = re.sub(r'[^A-Za-z0-9._-]+', '_', nombre).strip('._') or 'fondo'
    return limpio


def _fps(texto):
    try:
        a, b = texto.split('/')
        return round(int(a) / int(b)) if int(b) else 0
    except (ValueError, ZeroDivisionError, AttributeError):
        return 0


def describir(ruta):
    """Datos y aviso (si lo hay) de un fondo. Nunca lanza excepciones."""
    ruta = Path(ruta)
    datos = {'tipo': tipo(ruta), 'mb': 0.0, 'ancho': 0, 'alto': 0, 'fps': 0, 'aviso': ''}
    try:
        datos['mb'] = ruta.stat().st_size / 1_048_576
        salida = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height,avg_frame_rate', '-of', 'json', str(ruta)],
            capture_output=True, text=True, timeout=20).stdout
        flujo = (json.loads(salida).get('streams') or [{}])[0]
        datos['ancho'] = flujo.get('width', 0)
        datos['alto'] = flujo.get('height', 0)
        if datos['tipo'] == 'video':
            datos['fps'] = _fps(flujo.get('avg_frame_rate', ''))
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    if datos['tipo'] == 'video':
        motivos = []
        if datos['mb'] > AVISO_MB:
            motivos.append(f'{datos["mb"]:.0f} MB')
        if datos['alto'] > AVISO_ALTO:
            motivos.append(f'{datos["alto"]}p')
        if datos['fps'] > AVISO_FPS:
            motivos.append(f'{datos["fps"]} fps')
        if motivos:
            datos['aviso'] = 'Pesado para una pantalla de inicio: ' + ', '.join(motivos)
    return datos


def resumen(datos):
    partes = ['Vídeo' if datos['tipo'] == 'video' else 'Imagen']
    if datos['ancho']:
        partes.append(f'{datos["ancho"]}×{datos["alto"]}')
    if datos['fps']:
        partes.append(f'{datos["fps"]} fps')
    partes.append(f'{datos["mb"]:.1f} MB')
    return ' · '.join(partes)


def miniatura_video(ruta, ancho=320):
    """Primer fotograma de un vídeo, en caché. Devuelve la ruta del jpg o None."""
    ruta = Path(ruta)
    try:
        st = ruta.stat()
        clave = hashlib.sha1(f'{ruta}|{st.st_mtime_ns}|{st.st_size}|{ancho}'.encode()).hexdigest()
        destino = CACHE / f'{clave}.jpg'
        if destino.exists():
            return destino
        CACHE.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ['ffmpeg', '-v', 'error', '-y', '-ss', '1', '-i', str(ruta),
             '-frames:v', '1', '-vf', f'scale={ancho}:-1', str(destino)],
            capture_output=True, timeout=30)
        if not destino.exists():   # vídeos de menos de 1 s
            subprocess.run(
                ['ffmpeg', '-v', 'error', '-y', '-i', str(ruta),
                 '-frames:v', '1', '-vf', f'scale={ancho}:-1', str(destino)],
                capture_output=True, timeout=30)
        return destino if destino.exists() else None
    except (OSError, subprocess.SubprocessError):
        return None


def copiar_al_tema(origen, carpeta_fondos):
    """Copia un fondo a backgrounds/ del tema y devuelve el nombre final.

    Si ya hay uno con el mismo nombre y tamaño, se reutiliza; si tiene otro tamaño
    se añade un número al nombre para no pisar nada.
    """
    origen = Path(origen)
    carpeta = Path(carpeta_fondos)
    carpeta.mkdir(parents=True, exist_ok=True)
    base = nombre_seguro(origen.stem)
    ext = origen.suffix.lower()
    destino = carpeta / f'{base}{ext}'
    n = 2
    while destino.exists():
        if destino.stat().st_size == origen.stat().st_size:
            return destino.name
        destino = carpeta / f'{base}_{n}{ext}'
        n += 1
    shutil.copy2(origen, destino)
    os.chmod(destino, 0o644)     # el greeter de SDDM es otro usuario: tiene que poder leerlo
    return destino.name


def crear_marcador(video, carpeta):
    """Guarda en `carpeta` el primer fotograma del vídeo (jpg) y devuelve su nombre, o '' si no se pudo.

    El tema lo enseña mientras el vídeo carga (así no hay un pantallazo negro) y si el vídeo falla.
    """
    video = Path(video)
    destino = Path(carpeta) / f'{video.stem}-fotograma.jpg'
    try:
        if destino.exists() and destino.stat().st_mtime >= video.stat().st_mtime:
            return destino.name
        for espera in ('1', '0'):           # el segundo 1; si el vídeo es más corto, el primer fotograma
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', espera, '-i', str(video),
                            '-frames:v', '1', '-q:v', '3', str(destino)], capture_output=True, timeout=60)
            if destino.exists() and destino.stat().st_size > 0:
                os.chmod(destino, 0o644)
                return destino.name
    except (OSError, subprocess.SubprocessError):
        pass
    return ''


def imagenes_de_carpeta(carpeta):
    """Imágenes de una carpeta (sin subcarpetas ni vídeos), por orden de nombre.

    Devuelve (lista, mensaje_de_error). Si hay error, la lista va vacía.
    """
    imagenes = [p for p in listar(carpeta) if tipo(p) == 'imagen']
    if not imagenes:
        return [], 'Esa carpeta no tiene imágenes compatibles (jpg o png).'
    if len(imagenes) > MAX_IMAGENES_CARPETA:
        return [], (f'Esa carpeta tiene {len(imagenes)} imágenes y el máximo es '
                    f'{MAX_IMAGENES_CARPETA}. Elige una con menos.')
    return imagenes, None


def huerfanos(carpeta_fondos, textos_conf, protegidos=('default.jpg',)):
    """Imágenes y vídeos de backgrounds/ cuyo nombre no aparece en ninguna configuración."""
    junto = '\n'.join(textos_conf)
    return [p for p in listar(carpeta_fondos) if p.name not in protegidos and p.name not in junto]


def a_la_papelera(rutas):
    """Mueve archivos a la papelera (se pueden recuperar). Devuelve (movidos, fallos)."""
    movidos, fallos = [], []
    for ruta in rutas:
        try:
            r = subprocess.run(['gio', 'trash', str(ruta)], capture_output=True, text=True, timeout=120)
            (movidos if r.returncode == 0 else fallos).append(ruta)
        except (OSError, subprocess.SubprocessError):
            fallos.append(ruta)
    return movidos, fallos
