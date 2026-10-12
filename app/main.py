#main.py
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout, QDialog, QMainWindow, QMessageBox, QTableWidgetItem
from PyQt6.QtGui import QImage, QPixmap, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QTimer, QRect, pyqtSlot
from PyQt6 import QtWidgets
import pyqtgraph as pg

#imports de librerias locales
import sys
import json
import os
from vista.ui.plantillas.moringa import Ui_MoringaMain
from controlador.threads.camara_thread import CamaraThread
import cv2
from controlador.threads.ia_thread import IAThread 

SERIALES_PATH = "C:/Users/E-PIM_15/OneDrive - GRUPO PLASMA AUTOMATION S.A. DE C.V/Documentos/ProyectosCIEM/MoringaCIP/app/seriales.json"

#Clase Principal
class MoringaMain(QMainWindow, Ui_MoringaMain): # Heredar clase generada por qt designer

    def __init__(self):
        super(MoringaMain, self).__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)
        self.showNormal()
        self.camara_izquierda_thread = None
        self.ia_thread = None                        
        self.cargarSeriales()

    def showConfigurar(self):
        self.stackedWidget.setCurrentIndex(0)

    def showConfigurarCamaras(self):
        self.stackedWidget.setCurrentIndex(2)

    def iniciarIA(self):
        if self.camara_izquierda_thread is None or not self.camara_izquierda_thread.isRunning():
            QMessageBox.warning(self, "Aviso", "Primero inicia la cámara.")
            return
        if self.ia_thread is not None and self.ia_thread.isRunning():
            return

        self.ia_thread = IAThread()
        self.ia_thread.resultado_signal.connect(self.recibir_frame_ia)
        self.ia_thread.error_signal.connect(self.mostrar_error)
        self.camara_izquierda_thread.ia_thread = self.ia_thread
        self.ia_thread.start()

    def confirmarDatos(self):
        self.stackedWidget.setCurrentIndex(1)
        self._iniciarCamaras(self.recibir_frame_izquierdo)

    def detenerIA(self):
        # Desconectar cámara del hilo IA
        if self.camara_izquierda_thread is not None:
            self.camara_izquierda_thread.ia_thread = None

        # Parar hilo IA
        if self.ia_thread is not None:
            self.ia_thread.resultado_signal.disconnect(self.recibir_frame_ia)
            self.ia_thread.stop()
            self.ia_thread = None

        # Parar cámara y limpiar label
        self._detenerCamaras(
            self.recibir_frame_izquierdo,
            self.FrameCamIzquierda_lbl
        )

    def testCamarasOn(self):
        self._iniciarCamaras(self.recibir_frame_izquierdo_test)

    def testCamarasOff(self):
        self._detenerCamaras(
            self.recibir_frame_izquierdo_test,
            self.CamaraPruebaIzquierda_lbl
        )

    def _iniciarCamaras(self, slot_izquierda):
        """Inicia ambos threads de cámara y conecta los slots indicados."""
        serial_izquierda = self.obtenerSeriales()

        if self.camara_izquierda_thread is None or not self.camara_izquierda_thread.isRunning():
            self.camara_izquierda_thread = CamaraThread(str(serial_izquierda))
            self.camara_izquierda_thread.frame_signal.connect(slot_izquierda)
            self.camara_izquierda_thread.error_signal.connect(self.mostrar_error)
            self.camara_izquierda_thread.start()

    def _detenerCamaras(self, slot_izquierda, lbl_izquierda):
        """Detiene ambos threads de cámara, desconecta slots y limpia los labels."""
        if self.camara_izquierda_thread is not None and self.camara_izquierda_thread.isRunning():
            self.camara_izquierda_thread.frame_signal.disconnect()
            self.camara_izquierda_thread.stop()
            self.camara_izquierda_thread = None

        lbl_izquierda.clear()

    def mostrar_error(self, msg):
        QMessageBox.critical(self, "Error del sistema de visión / PLC", msg)

    def closeEvent(self, event):
        self.detenerIA()
        event.accept()

    def mostrar_frame(self, frame_bgr, frame_lado_lbl: QLabel):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w

        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        frame_lado_lbl.setPixmap(pixmap.scaled(
            frame_lado_lbl.width(),
            frame_lado_lbl.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))

    def recibir_frame_ia(self, annotated_frame):
        """Muestra el frame con anotaciones cuando la IA está activa."""
        self.mostrar_frame(annotated_frame, self.FrameCamIzquierda_lbl)


    def recibir_frame_izquierdo(self, color_frame, depth_frame):
        self.mostrar_frame(color_frame, self.FrameCamIzquierda_lbl)

    def recibir_frame_izquierdo_test(self, color_frame, depth_frame):
        self.mostrar_frame(color_frame, self.CamaraPruebaIzquierda_lbl)

    def guardarSeriales(self):
        serial_izquierda = self.SerialCamIzquierda_lineEdit.text().strip()

        # Validar que no estén vacíos
        if not serial_izquierda:
            QMessageBox.warning(self, "Campos vacíos", "Por favor ingresa ambos números de serie antes de guardar.")
            return

        # Guardar en JSON
        datos = {
            "serial_cam_izquierda": serial_izquierda
        }

        try:
            with open(SERIALES_PATH, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)

            # Actualizar labels con los valores guardados
            self.SerialCamIzquierda_lbl.setText(serial_izquierda)

            QMessageBox.information(self, "Éxito", "Números de serie guardados correctamente.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{str(e)}")

    def obtenerSeriales(self):
        if not os.path.exists(SERIALES_PATH):
            return

        try:
            with open(SERIALES_PATH, "r", encoding="utf-8") as f:
                datos = json.load(f)

            serial_izquierda = datos.get("serial_cam_izquierda", "")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo de seriales:\n{str(e)}")

        return serial_izquierda

    def cargarSeriales(self):
        """Carga los seriales desde el JSON al iniciar la aplicación."""

        try:
            serial_izquierda = self.obtenerSeriales()

            # Mostrar en labels
            self.SerialCamIzquierda_lbl.setText(serial_izquierda)
          
            # Prellenar los lineEdits con los valores guardados
            self.SerialCamIzquierda_lineEdit.setText(serial_izquierda)
           
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo de seriales:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MoringaMain()
    window.show()
    sys.exit(app.exec())
