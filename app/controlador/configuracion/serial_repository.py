"""Persistencia de seriales sin dependencias de la interfaz ni del hardware."""
import json
from pathlib import Path


class SerialRepository:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else Path(__file__).resolve().parents[2] / "seriales.json"

    def cargar(self):
        if not self.path.exists():
            return ""
        with self.path.open(encoding="utf-8") as archivo:
            datos = json.load(archivo)
        serial = datos.get("serial_cam_izquierda", "")
        return str(serial).strip() if serial is not None else ""

    def guardar(self, serial):
        serial = serial.strip()
        if not serial:
            raise ValueError("Ingresa el número de serie de la cámara izquierda.")
        # Conservar otras claves de configuración existentes.
        datos = {}
        if self.path.exists():
            with self.path.open(encoding="utf-8") as archivo:
                datos = json.load(archivo)
        datos["serial_cam_izquierda"] = serial
        with self.path.open("w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=4, ensure_ascii=False)
