"""Validación y persistencia de la dirección IPv4 del PLC."""
from ipaddress import IPv4Address
import json
from pathlib import Path


class PLCRepository:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else Path(__file__).resolve().parents[2] / "plc.json"

    @staticmethod
    def validar(ip):
        try:
            return str(IPv4Address(ip.strip()))
        except (ValueError, AttributeError) as error:
            raise ValueError("Ingresa una dirección IPv4 válida para el PLC.") from error

    def cargar(self):
        if not self.path.exists():
            return ""
        with self.path.open(encoding="utf-8") as archivo:
            datos = json.load(archivo)
        ip = datos.get("plc_ip", "")
        return self.validar(ip) if ip else ""

    def guardar(self, ip):
        ip = self.validar(ip)
        datos = {}
        if self.path.exists():
            with self.path.open(encoding="utf-8") as archivo:
                datos = json.load(archivo)
        datos["plc_ip"] = ip
        with self.path.open("w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=4, ensure_ascii=False)
        return ip
