#controlador/threads/camara_thread.py
from PyQt6.QtCore import QThread, pyqtSignal
import cv2
import numpy as np
from controlador.camara.realsense_depth import DepthCamera


class CamaraThread(QThread):
    frame_signal = pyqtSignal(np.ndarray, np.ndarray)
    error_signal = pyqtSignal(str)

    def __init__(self, no_serial, parent=None):
        super().__init__(parent)
        self.running   = False
        self.camera    = None
        self.no_serial = no_serial
        self.ia_thread = None          # ← agregar esto

    def run(self):
        try:
            self.camera  = DepthCamera(self.no_serial)
            self.running = True

            while self.running and not self.isInterruptionRequested():
                ret, depth_frame, color_frame, _ = self.camera.get_frame()
                if not ret:
                    continue

                # Solo emitir frame crudo si la IA NO está corriendo
                ia_thread = self.ia_thread
                if ia_thread is None or not ia_thread.isRunning():
                    self.frame_signal.emit(color_frame, depth_frame)

                # Siempre pasar el frame al hilo de IA si está activo
                if ia_thread is not None and ia_thread.isRunning():
                    ia_thread.enviar_frame(color_frame, depth_frame)

        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            if self.camera is not None:
                self.camera.release()

    def stop(self):
        self.requestInterruption()
        self.running = False
        self.wait()
