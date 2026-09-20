"""Plantillas de Velo: archivos pequeños de configs/presets/ que solo llevan los ajustes de aspecto.

Una plantilla es un .conf parcial (mismo formato que default.conf). Al usarla, la GUI rellena
los controles con sus valores; no toca el fondo, el idioma ni la fuente. Las dos primeras líneas
de comentario dan el nombre y la descripción:

    ; Nombre: Windows 11
    ; Descripción: ...
"""
from pathlib import Path

import velo_conf


def _cabecera(ruta, etiqueta):
    try:
        for linea in Path(ruta).read_text(encoding='utf-8').splitlines():
            if linea.startswith(';') and linea[1:].strip().lower().startswith(etiqueta):
                return linea.split(':', 1)[1].strip()
    except OSError:
        pass
    return ''


def listar(carpeta):
    """[{'id', 'nombre', 'descripcion', 'valores': [(sección, clave, valor)]}] ordenadas por nombre de archivo."""
    salida = []
    for ruta in sorted(Path(carpeta).glob('*.conf')):
        try:
            valores = velo_conf.ConfFile(ruta).items()
        except (OSError, UnicodeDecodeError):
            continue
        salida.append({'id': ruta.stem, 'nombre': _cabecera(ruta, 'nombre') or ruta.stem,
                       'descripcion': _cabecera(ruta, 'descripci'), 'valores': valores})
    return salida
