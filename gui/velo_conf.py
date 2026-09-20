"""Lee y escribe configs/default.conf sin perder comentarios, orden ni formato.

Solo cambia la línea de la clave pedida; si la clave no existe, la añade al final
de su sección. Antes de escribir hace una copia de seguridad con fecha.
"""
import os
import re
import tempfile
import time
from pathlib import Path

_SECCION = re.compile(r'^\s*\[([^\]]+)\]\s*$')
_CLAVE = re.compile(r'^(\s*)([A-Za-z0-9_.\-]+)(\s*=\s*)(.*?)\s*$')
COPIAS_A_CONSERVAR = 10


def _sin_comillas(valor):
    valor = valor.strip()
    if len(valor) >= 2 and valor[0] == valor[-1] == '"':
        return valor[1:-1]
    return valor


class ConfFile:
    def __init__(self, ruta):
        self.ruta = Path(ruta)
        self.lineas = self.ruta.read_text(encoding='utf-8').splitlines()
        self.modificado = False

    # ---- búsqueda ----
    def _rango_seccion(self, seccion):
        """Devuelve (inicio, fin) de las líneas de una sección, o None."""
        inicio = None
        for i, linea in enumerate(self.lineas):
            m = _SECCION.match(linea)
            if m:
                if inicio is not None:
                    return inicio, i
                if m.group(1) == seccion:
                    inicio = i + 1
        return (inicio, len(self.lineas)) if inicio is not None else None

    def _indice_clave(self, seccion, clave):
        rango = self._rango_seccion(seccion)
        if rango is None:
            return None
        for i in range(*rango):
            if self.lineas[i].lstrip().startswith(';'):
                continue
            m = _CLAVE.match(self.lineas[i])
            if m and m.group(2) == clave:
                return i
        return None

    def secciones_con(self, clave):
        """Nombres de las secciones que tienen esa clave (para ajustes globales, como la fuente)."""
        salida, actual = [], None
        for linea in self.lineas:
            m = _SECCION.match(linea)
            if m:
                actual = m.group(1)
                continue
            c = _CLAVE.match(linea)
            if actual and c and c.group(2) == clave and not linea.lstrip().startswith(';') and actual not in salida:
                salida.append(actual)
        return salida

    def items(self):
        """[(sección, clave, valor sin comillas)] en el orden del archivo (ignora comentarios)."""
        salida, actual = [], None
        for linea in self.lineas:
            m = _SECCION.match(linea)
            if m:
                actual = m.group(1)
                continue
            c = _CLAVE.match(linea)
            if actual and c and not linea.lstrip().startswith(';'):
                salida.append((actual, c.group(2), _sin_comillas(c.group(4))))
        return salida

    # ---- lectura / escritura en memoria ----
    def get(self, seccion, clave, defecto=''):
        i = self._indice_clave(seccion, clave)
        if i is None:
            return defecto
        return _sin_comillas(_CLAVE.match(self.lineas[i]).group(4))

    def set(self, seccion, clave, valor, texto=True):
        """Pone un valor. Si la clave ya existe, respeta si llevaba comillas."""
        valor = str(valor)
        i = self._indice_clave(seccion, clave)
        if i is not None:
            m = _CLAVE.match(self.lineas[i])
            llevaba_comillas = m.group(4).strip().startswith('"')
            nuevo = f'"{valor}"' if (llevaba_comillas or texto) else valor
            if _sin_comillas(m.group(4)) == valor:
                return
            self.lineas[i] = f'{m.group(1)}{m.group(2)}{m.group(3)}{nuevo}'
        else:
            nuevo = f'"{valor}"' if texto else valor
            rango = self._rango_seccion(seccion)
            if rango is None:
                if self.lineas and self.lineas[-1].strip():
                    self.lineas.append('')
                self.lineas += [f'[{seccion}]', f'{clave} = {nuevo}']
            else:
                fin = rango[1]
                while fin > rango[0] and not self.lineas[fin - 1].strip():
                    fin -= 1
                self.lineas.insert(fin, f'{clave} = {nuevo}')
        self.modificado = True

    # ---- guardar ----
    def guardar(self):
        """Escribe el archivo. Devuelve la ruta de la copia de seguridad."""
        copia = self.ruta.with_name(f'{self.ruta.name}.gui-bak-{time.strftime("%Y%m%d-%H%M%S")}')
        copia.write_bytes(self.ruta.read_bytes())
        fd, tmp = tempfile.mkstemp(dir=self.ruta.parent, prefix='.velo-')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.lineas) + '\n')
            # mkstemp crea el archivo en modo 600; el greeter de SDDM (otro usuario) tiene que poder leerlo.
            os.chmod(tmp, (self.ruta.stat().st_mode | 0o644) & 0o777)
            os.replace(tmp, self.ruta)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        self.modificado = False
        self._limpiar_copias()
        return copia

    def _limpiar_copias(self):
        copias = sorted(self.ruta.parent.glob(f'{self.ruta.name}.gui-bak-*'))
        for vieja in copias[:-COPIAS_A_CONSERVAR]:
            vieja.unlink()
