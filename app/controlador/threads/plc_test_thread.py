"""Ejecuta una operación manual sin bloquear la ventana."""
from PyQt6.QtCore import QThread, pyqtSignal


class PLCTestThread(QThread):
    resultado = pyqtSignal(bool, bool)
    error = pyqtSignal(str)

    def __init__(self, servicio, accion, parent=None):
        super().__init__(parent)
        self.servicio = servicio
        self.accion = accion

    def run(self):
        try:
            avance, retroceso = self.servicio.ejecutar(self.accion)
            self.resultado.emit(avance, retroceso)
        except Exception as error:
            self.error.emit(str(error))
