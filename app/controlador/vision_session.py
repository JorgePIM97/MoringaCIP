"""Coordina el ciclo de vida de cámara e IA; no contiene el algoritmo."""
from controlador.threads.camara_thread import CamaraThread
from controlador.threads.ia_thread import IAThread
from controlador.configuracion.plc_repository import PLCRepository


class VisionSession:
    def __init__(self, frame_slot, ia_slot, error_slot,
                 camera_factory=CamaraThread, ia_factory=IAThread):
        self.camara = None
        self.ia = None
        self._frame_slot = frame_slot
        self._ia_slot = ia_slot
        self._error_slot = error_slot
        self._camera_factory = camera_factory
        self._ia_factory = ia_factory

    def iniciar_camara(self, serial, frame_slot):
        if not serial:
            raise ValueError("Configura el número de serie de la cámara izquierda.")
        if self.camara is not None and self.camara.isRunning():
            if frame_slot != self._frame_slot:
                self.camara.frame_signal.disconnect(self._frame_slot)
                self.camara.frame_signal.connect(frame_slot)
                self._frame_slot = frame_slot
            return
        self._frame_slot = frame_slot
        self.camara = self._camera_factory(str(serial))
        self.camara.frame_signal.connect(frame_slot)
        self.camara.error_signal.connect(self._error_slot)
        self.camara.start()

    def iniciar_ia(self, plc_ip):
        if self.camara is None or not self.camara.isRunning():
            raise ValueError("Primero inicia la cámara.")
        if self.ia is not None and self.ia.isRunning():
            return
        if not plc_ip:
            raise ValueError("Guarda la dirección IP del PLC antes de iniciar la IA.")
        self.ia = self._ia_factory(plc_ip=PLCRepository.validar(plc_ip))
        self.ia.resultado_signal.connect(self._ia_slot)
        self.ia.error_signal.connect(self._error_slot)
        self.camara.ia_thread = self.ia
        self.ia.start()

    def detener_ia(self):
        if self.camara is not None:
            self.camara.ia_thread = None
        if self.ia is not None:
            self.ia.resultado_signal.disconnect(self._ia_slot)
            self.ia.stop()
            self.ia = None

    def detener_camara(self):
        # No dejar IA/PLC funcionando al desconectar la fuente de frames.
        self.detener_ia()
        if self.camara is not None:
            self.camara.frame_signal.disconnect(self._frame_slot)
            self.camara.stop()
            self.camara = None

    def detener(self):
        self.detener_camara()
