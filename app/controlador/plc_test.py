"""Pruebas manuales del mando izquierdo, independientes de la IA."""
import time

from pycomm3 import LogixDriver


class PLCTest:
    AVANCE = "CMD_ON_Cuchilla_Izquierda"
    RETROCESO = "CMD_OFF_Cuchilla_Izquierda"

    def __init__(self, ip, tag_retraido=None, valor_retraido=True,
                 timeout=10, driver_factory=LogixDriver):
        self.ip = ip
        self.tag_retraido = tag_retraido
        self.valor_retraido = valor_retraido
        self.timeout = timeout
        self.driver_factory = driver_factory

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
            self._validar(plc.write(tag, valor))
        if self._estado(plc) != (avance, retroceso):
            raise RuntimeError("La lectura del PLC no coincide con la orden enviada.")

    def ejecutar(self, accion):
        if accion not in ("comunicacion", "avance", "retroceso", "apagar"):
            raise ValueError("Acción PLC desconocida.")
        if accion == "apagar" and not self.tag_retraido:
            raise ValueError("Configura el tag de fin de retroceso para confirmar la posición antes de apagar.")
        plc = self.driver_factory(self.ip)
        try:
            if not plc.open():
                raise RuntimeError(f"No se pudo conectar al PLC {self.ip}.")
            if accion == "comunicacion":
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
