"""Ventana principal y slots conectados desde Qt Designer."""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import Qt
from vista.ui.plantillas.moringa import Ui_MoringaMain
from vista.frame_presenter import mostrar_frame
from controlador.navegation.screen_navegation import ScreenNavegation
from controlador.configuracion.serial_repository import SerialRepository
from controlador.configuracion.plc_repository import PLCRepository
from controlador.vision_session import VisionSession


class MoringaMain(QMainWindow, Ui_MoringaMain):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)
        self.showNormal()
        self.screen_navigation = ScreenNavegation(self.stackedWidget)
        self.screen_navigation.screen_principal()
        self.serial_repository = SerialRepository()
        self.plc_repository = PLCRepository()
        self.vision_session = VisionSession(
            self.recibir_frame_izquierdo, self.recibir_frame_ia, self.mostrar_error,
        )
        self.cargarSeriales()
        self.cargarIP()

    def showConfigurar(self):
        self.screen_navigation.screen_principal()

    def showConfigurarCamaras(self):
        self.screen_navigation.screen_configurar_camara()

    def confirmarDatos(self):
        self.screen_navigation.screen_vision_artificial()
        self._iniciarCamaras(self.recibir_frame_izquierdo)

    def iniciarIA(self):
        try:
            self.vision_session.iniciar_ia(self.plc_repository.cargar())
        except ValueError as error:
            QMessageBox.warning(self, "Aviso", str(error))
        except Exception as error:
            self.mostrar_error(str(error))

    def detenerIA(self):
        self.vision_session.detener()
        self.FrameCamIzquierda_lbl.clear()
        self.CamaraPruebaIzquierda_lbl.clear()

    def testCamarasOn(self):
        self._iniciarCamaras(self.recibir_frame_izquierdo_test)

    def testCamarasOff(self):
        self._detenerCamaras(self.recibir_frame_izquierdo_test, self.CamaraPruebaIzquierda_lbl)

    def showConfigurarPLC(self):
        self.screen_navigation.screen_configurar_plc()

    def exitConfigPLC(self):
        self.screen_navigation.screen_principal()

    def exitConfigCamara(self):
        self.screen_navigation.screen_principal()

    def saveIP(self):
        try:
            ip = self.plc_repository.guardar(self.IngresarIP_lineEdit.text())
        except ValueError as error:
            QMessageBox.warning(self, "IP inválida", str(error))
        except Exception as error:
            self.mostrar_error(f"No se pudo guardar la IP del PLC: {error}")
        else:
            self.IngresarIP_lineEdit.setText(ip)
            self.IP_label.setText(ip)
            QMessageBox.information(
                self, "IP guardada",
                "La IP se utilizará al iniciar la IA. Si está activa, detén y vuelve a iniciar la sesión para aplicar el cambio.",
            )

    def cargarIP(self):
        try:
            ip = self.plc_repository.cargar()
        except Exception as error:
            self.mostrar_error(f"No se pudo cargar la IP del PLC: {error}")
            ip = ""
        self.IngresarIP_lineEdit.setText(ip)
        self.IP_label.setText(ip or "Sin configurar")

    def testComunicacionPLC(self):
        """
        Solo prueba comu
        """
        pass

    def activarAvancePistones(self):
        pass

    def activarRetrocesoPistones(self):
        pass

    def apagarPistones(self):
        pass


    def _iniciarCamaras(self, slot_izquierda):
        try:
            self.vision_session.iniciar_camara(self.serial_repository.cargar(), slot_izquierda)
        except ValueError as error:
            QMessageBox.warning(self, "Aviso", str(error))
        except Exception as error:
            self.mostrar_error(str(error))

    def _detenerCamaras(self, slot_izquierda, lbl_izquierda):
        self.vision_session.detener_camara()
        lbl_izquierda.clear()

    def guardarSeriales(self):
        serial = self.SerialCamIzquierda_lineEdit.text().strip()
        try:
            self.serial_repository.guardar(serial)
        except ValueError as error:
            QMessageBox.warning(self, "Serial inv?lido", str(error))
        except Exception as error:
            self.mostrar_error(f"No se pudo guardar el serial: {error}")
        else:
            self.SerialCamIzquierda_lbl.setText(serial)
            QMessageBox.information(self, "?xito", "N?mero de serie guardado correctamente.")

    def obtenerSeriales(self):
        try:
            return self.serial_repository.cargar()
        except Exception as error:
            self.mostrar_error(f"No se pudo cargar el serial: {error}")
            return ""

    def cargarSeriales(self):
        serial = self.obtenerSeriales()
        self.SerialCamIzquierda_lbl.setText(serial)
        self.SerialCamIzquierda_lineEdit.setText(serial)

    def mostrar_error(self, msg):
        QMessageBox.critical(self, "Error del sistema de visi?n / PLC", msg)

    def closeEvent(self, event):
        self.detenerIA()
        event.accept()

    def mostrar_frame(self, frame_bgr, frame_lado_lbl):
        mostrar_frame(frame_bgr, frame_lado_lbl)

    def recibir_frame_ia(self, annotated_frame):
        self.mostrar_frame(annotated_frame, self.FrameCamIzquierda_lbl)

    def recibir_frame_izquierdo(self, color_frame, depth_frame):
        self.mostrar_frame(color_frame, self.FrameCamIzquierda_lbl)

    def recibir_frame_izquierdo_test(self, color_frame, depth_frame):
        self.mostrar_frame(color_frame, self.CamaraPruebaIzquierda_lbl)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MoringaMain()
    window.show()
    sys.exit(app.exec())
