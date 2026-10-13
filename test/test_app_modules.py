"""Regresión de navegación Designer, configuración y ciclo de vida sin hardware."""
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from PyQt6.QtWidgets import QApplication
from controlador.configuracion.serial_repository import SerialRepository
from controlador.configuracion.plc_repository import PLCRepository
from controlador.vision_session import VisionSession
from main import MoringaMain


class ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_designer_slots_navigate_existing_window(self):
        window = MoringaMain()
        window.vision_session = Mock()
        window.ConfigurarCamaras_toolButton.click()
        self.assertEqual(window.stackedWidget.currentIndex(), 2)
        window.Configurar_toolButton.click()
        self.assertEqual(window.stackedWidget.currentIndex(), 0)
        window.ConfirmarDatos_lineEdit.click()
        self.assertEqual(window.stackedWidget.currentIndex(), 1)
        window.Iniciar_toolButton.click()
        window.vision_session.iniciar_ia.assert_called_once()
        window.Finalizar_toolButton.click()
        window.vision_session.detener.assert_called_once()
        window.close()

    def test_serial_roundtrip_and_preserve_extra_keys(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "seriales.json"
            repository = SerialRepository(path)
            self.assertEqual(repository.cargar(), "")
            path.write_text('{"otra_configuracion": 1}', encoding="utf-8")
            repository.guardar(" 123456 ")
            self.assertEqual(repository.cargar(), "123456")
            self.assertEqual(json.loads(path.read_text())["otra_configuracion"], 1)
            with self.assertRaises(ValueError):
                repository.guardar(" ")

    def session(self):
        camera, ia = Mock(), Mock()
        camera.isRunning.return_value = True
        ia.isRunning.return_value = True
        session = VisionSession(Mock(), Mock(), Mock(), Mock(return_value=camera), Mock(return_value=ia))
        return session, camera, ia

    def test_switch_camera_receiver_without_restarting(self):
        session, camera, _ = self.session()
        first, second = Mock(), Mock()
        session.iniciar_camara("123", first)
        session.iniciar_camara("123", second)
        camera.start.assert_called_once()
        camera.frame_signal.disconnect.assert_called_once_with(first)
        self.assertEqual(camera.frame_signal.connect.call_args.args, (second,))

    def test_camera_stop_stops_ia_first_and_is_repeatable(self):
        session, camera, ia = self.session()
        calls = []
        ia.stop.side_effect = lambda: calls.append("ia")
        camera.stop.side_effect = lambda: calls.append("camera")
        session.iniciar_camara("123", Mock())
        session.iniciar_ia("192.168.1.25")
        session.iniciar_ia("192.168.1.25")
        ia.start.assert_called_once()
        session.detener()
        session.detener()
        self.assertEqual(calls, ["ia", "camera"])
        self.assertIsNone(camera.ia_thread)

    def test_ia_requires_camera_and_missing_serial_does_not_start(self):
        session, camera, ia = self.session()
        with self.assertRaises(ValueError):
            session.iniciar_ia("192.168.1.25")
        with self.assertRaises(ValueError):
            session.iniciar_camara("", Mock())
        camera.start.assert_not_called()
        ia.start.assert_not_called()

    def test_plc_ip_persistence_and_invalid_ip_preserves_saved_value(self):
        with TemporaryDirectory() as directory:
            repository = PLCRepository(Path(directory) / "plc.json")
            self.assertEqual(repository.cargar(), "")
            self.assertEqual(repository.guardar(" 192.168.1.25 "), "192.168.1.25")
            for ip in ("", "300.1.1.1", "hostname", "::1"):
                with self.assertRaises(ValueError):
                    repository.guardar(ip)
            self.assertEqual(PLCRepository(repository.path).cargar(), "192.168.1.25")

    def test_session_passes_saved_ip_and_requires_configuration(self):
        session, camera, _ = self.session()
        session.iniciar_camara("123", Mock())
        with self.assertRaises(ValueError):
            session.iniciar_ia("")
        session._ia_factory.assert_not_called()
        session.iniciar_ia("192.168.1.25")
        session._ia_factory.assert_called_once_with(plc_ip="192.168.1.25")

    def test_designer_save_ip_and_reload(self):
        with TemporaryDirectory() as directory:
            repository = PLCRepository(Path(directory) / "plc.json")
            with patch("main.PLCRepository", return_value=repository), patch("main.QMessageBox.information"):
                window = MoringaMain()
                window.IngresarIP_lineEdit.setText("192.168.1.25")
                window.GuardarIP_pushButton.click()
                self.assertEqual(repository.cargar(), "192.168.1.25")
                self.assertEqual(window.IP_label.text(), "192.168.1.25")
                window.vision_session = Mock()
                window.iniciarIA()
                window.vision_session.iniciar_ia.assert_called_once_with("192.168.1.25")
                window.close()
                reopened = MoringaMain()
                self.assertEqual(reopened.IngresarIP_lineEdit.text(), "192.168.1.25")
                reopened.close()


if __name__ == "__main__":
    unittest.main()
