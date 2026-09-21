"""Pantalla principal de KDE, para que el inicio de sesión salga en esa y no en otra."""
import json
import shutil
import subprocess


def principal_de_kde():
    """Nombre de la pantalla con prioridad 1 en KDE (p. ej. 'eDP-1'), o '' si no se puede saber."""
    kscreen = shutil.which('kscreen-doctor')
    if kscreen is None:
        return ''
    try:
        salida = subprocess.run([kscreen, '-j'], capture_output=True, text=True, timeout=5, check=True).stdout
        pantallas = json.loads(salida)['outputs']
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        return ''
    activas = [p for p in pantallas if p.get('enabled') and p.get('connected') and p.get('name')]
    if not activas:
        return ''
    return str(min(activas, key=lambda p: p.get('priority', 9999))['name'])
