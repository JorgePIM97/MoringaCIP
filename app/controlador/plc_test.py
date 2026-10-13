"""Pruebas manuales del mando izquierdo, independientes de la IA."""
import time
import csv
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pycomm3 import LogixDriver


class PLCTest:
    AVANCE = "CMD_ON_Cuchilla_Izquierda"
    RETROCESO = "CMD_OFF_Cuchilla_Izquierda"
    SENSORES = {
        "avance": ("tag_piston_1_avance", "tag_piston_2_avance"),
        "retroceso": ("tag_piston_1_retroceso", "tag_piston_2_retroceso"),
    }

    def __init__(self, ip, tag_retraido=None, valor_retraido=True,
                 timeout=10, driver_factory=LogixDriver, medir=False,
                 csv_path=None, intervalo=0.01):
        self.ip = ip
        self.tag_retraido = tag_retraido
        self.valor_retraido = valor_retraido
        self.timeout = timeout
        self.driver_factory = driver_factory
        self.medir = medir
        self.csv_path = Path(csv_path) if csv_path is not None else (
            Path(__file__).resolve().parents[2] / "logs" / "pruebas_tiempos_pistones.csv")
        self.intervalo = intervalo
        self.mediciones = []
        if timeout < 0 or intervalo <= 0:
            raise ValueError("El timeout debe ser no negativo y el intervalo positivo.")

    @staticmethod
    def _validar(resultados):
        if not isinstance(resultados, (list, tuple)):
            resultados = [resultados]
        if not resultados or not all(bool(r) for r in resultados):
            raise RuntimeError(f"El PLC rechazó la operación: {resultados}")
        return resultados

    def _estado(self, plc):
        lecturas = self._validar(plc.read(self.AVANCE, self.RETROCESO))
        if len(lecturas) != 2 or any(type(r.value) is not bool for r in lecturas):
            raise RuntimeError("Los tags de mando deben ser BOOL.")
        return tuple(r.value for r in lecturas)

    def _mando(self, plc, avance, retroceso):
        # Desactivar primero el sentido opuesto, comprobando cada escritura.
        orden = ((self.RETROCESO, False), (self.AVANCE, avance)) if avance else (
            (self.AVANCE, False), (self.RETROCESO, retroceso))
        for tag, valor in orden:
            if valor:
                inicio = time.perf_counter()
            self._validar(plc.write(tag, valor))
        if self._estado(plc) != (avance, retroceso):
            raise RuntimeError("La lectura del PLC no coincide con la orden enviada.")
        return inicio if avance or retroceso else None

    def _sensores(self, plc, tags):
        lecturas = self._validar(plc.read(*tags))
        if len(lecturas) != len(tags) or any(type(r.value) is not bool for r in lecturas):
            raise RuntimeError("Los sensores de los pistones deben ser BOOL.")
        return [r.value for r in lecturas]

    def _guardar_mediciones(self):
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        cabecera = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
        with self.csv_path.open("a", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=list(self.mediciones[0]))
            if cabecera:
                writer.writeheader()
            writer.writerows(self.mediciones)

    def _movimiento_medido(self, plc, accion):
        movimiento = "retroceso" if accion == "apagar" else accion
        tags = self.SENSORES[movimiento]
        iniciales = self._sensores(plc, tags)
        # Comprobar acceso al CSV antes de activar el movimiento.
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("a", newline="", encoding="utf-8"):
            pass
        operacion = uuid4().hex
        fecha = datetime.now().astimezone().isoformat(timespec="milliseconds")
        self.mediciones = [dict(
            operacion=operacion, fecha_orden=fecha, plc_ip=self.ip,
            accion=accion, movimiento=movimiento, piston=i + 1, sensor=tag,
            sensor_inicial=activo, tiempo_ms="", estado="error",
            intervalo_lectura_ms=self.intervalo * 1000,
        ) for i, (tag, activo) in enumerate(zip(tags, iniciales))]
        try:
            inicio = self._mando(plc, movimiento == "avance", movimiento == "retroceso")
            pendientes = set(range(len(tags)))
            while pendientes:
                valores = self._sensores(plc, tags)
                observado = time.perf_counter()
                for i in list(pendientes):
                    fila = self.mediciones[i]
                    if iniciales[i] and valores[i]:
                        # Una posición ya alcanzada no representa un nuevo recorrido.
                        fila["estado"] = "sensor_ya_activo"
                        pendientes.remove(i)
                    elif valores[i]:
                        fila["estado"] = "completado"
                        fila["tiempo_ms"] = round((observado - inicio) * 1000, 3)
                        pendientes.remove(i)
                if not pendientes:
                    break
                if observado - inicio >= self.timeout:
                    for i in pendientes:
                        self.mediciones[i]["estado"] = "timeout"
                    raise RuntimeError(
                        "No se confirmó el fin de recorrido de ambos pistones; "
                        "se mantiene la orden enviada. Revisa los sensores y el CSV de pruebas.")
                time.sleep(self.intervalo)
        finally:
            self._guardar_mediciones()
        if accion == "apagar":
            self._mando(plc, False, False)

    def ejecutar(self, accion):
        self.mediciones = []
        if accion not in ("comunicacion", "avance", "retroceso", "apagar"):
            raise ValueError("Acción PLC desconocida.")
        if accion == "apagar" and not self.tag_retraido and not self.medir:
            raise ValueError("Configura el tag de fin de retroceso para confirmar la posición antes de apagar.")
        plc = self.driver_factory(self.ip)
        try:
            if not plc.open():
                raise RuntimeError(f"No se pudo conectar al PLC {self.ip}.")
            if accion == "comunicacion":
                return self._estado(plc)
            if self.medir:
                self._movimiento_medido(plc, accion)
                return self._estado(plc)
            if accion == "apagar":
                sensor = self._validar(plc.read(self.tag_retraido))[0]
                if type(sensor.value) is not bool:
                    raise RuntimeError("El sensor de retroceso debe ser BOOL.")
                self._mando(plc, False, True)
                limite = time.monotonic() + self.timeout
                while True:
                    sensor = self._validar(plc.read(self.tag_retraido))[0]
                    if type(sensor.value) is not bool:
                        raise RuntimeError("El sensor de retroceso debe ser BOOL.")
                    if sensor.value == self.valor_retraido:
                        break
                    if time.monotonic() >= limite:
                        raise RuntimeError("No se confirmó el retroceso; se mantiene la orden de retroceso y no se declara apagado.")
                    time.sleep(0.05)
                self._mando(plc, False, False)
            else:
                self._mando(plc, accion == "avance", accion == "retroceso")
            return self._estado(plc)
        finally:
            plc.close()
