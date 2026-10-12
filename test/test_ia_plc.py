"""Pruebas de control sin importar SDKs ni conectar hardware real."""
import ast
from collections import defaultdict
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
import time
import unittest
from unittest.mock import Mock


SOURCE = Path(__file__).resolve().parents[1] / "app/controlador/threads/ia_thread.py"


class FakeThread:
    def __init__(self, parent=None):
        self.interrupted = False

    def isInterruptionRequested(self):
        return self.interrupted

    def requestInterruption(self):
        self.interrupted = True

    def wait(self):
        pass


def load_thread():
    # Ejecutar la clase de producción con adaptadores de sus dependencias;
    # ninguna importación dispara CUDA, RealSense o comunicación EtherNet/IP.
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    namespace = {
        "__file__": str(SOURCE), "QThread": FakeThread,
        "pyqtSignal": lambda *_: Mock(), "np": SimpleNamespace(ndarray=object),
        "defaultdict": defaultdict, "Lock": Lock, "Path": Path,
        "time": time, "cv2": Mock(), "YOLO": Mock(), "LogixDriver": Mock(),
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace["IAThread"], namespace


class ControlTests(unittest.TestCase):
    def setUp(self):
        cls, self.namespace = load_thread()
        self.ia = cls()
        self.ia.plc = Mock()

    def readings(self, avance, retroceso):
        self.ia.plc.write.return_value = [True, True]
        self.ia.plc.read.return_value = [
            SimpleNamespace(value=avance), SimpleNamespace(value=retroceso),
        ]

    def control(self, track_id=1, y=220, lado="izquierdo"):
        x = 100 if lado == "izquierdo" else 600
        start, end = (0, 424) if lado == "izquierdo" else (424, 848)
        self.ia._control_cuchilla(
            object(), [x, y, 10, 10], track_id,
            (x, y), (x, y-20), (x, y+20), y-20, y+20,
            (x-5, y-20), (x+5, y-15), (x-5, y+20), (x+5, y+15),
            start, end, lado, Lock(),
        )

    def test_geometry_and_open_close_once_per_id(self):
        self.assertEqual((self.ia.ancho_frame, self.ia.umbral_trigger), (848, 240))
        self.readings(False, True)
        self.control(y=250)  # y-20 <= 240; y+20 > 240
        self.ia.plc.write.assert_called_with(
            ("CMD_ON_Cuchilla_Izquierda", False),
            ("CMD_OFF_Cuchilla_Izquierda", True),
        )
        self.readings(True, False)
        self.control(y=220)
        self.ia.plc.write.assert_called_with(
            ("CMD_ON_Cuchilla_Izquierda", True),
            ("CMD_OFF_Cuchilla_Izquierda", False),
        )
        self.control(y=220)
        self.assertEqual(self.ia.plc.write.call_count, 2)

    def test_right_region_never_writes(self):
        self.control(lado="derecho")
        self.control(lado="derecho")
        self.ia.plc.write.assert_not_called()

    def test_invalid_combination_rejected(self):
        with self.assertRaises(ValueError):
            self.ia.escribir_estado_cuchilla_izquierda(True, True, "INVALIDO")
        self.ia.plc.write.assert_not_called()

    def test_write_error_does_not_count_or_read(self):
        self.ia.plc.write.return_value = [True, False]
        with self.assertRaises(RuntimeError):
            self.control()
        self.assertEqual(self.ia.conteo_cuchillas_abiertas["izquierdo"]["total"], 0)
        self.ia.plc.read.assert_not_called()

    def test_readback_mismatch_does_not_count(self):
        self.readings(True, False)
        with self.assertRaises(RuntimeError):
            self.control()
        self.assertEqual(self.ia.conteo_cuchillas_abiertas["izquierdo"]["contadas"], [])

    def test_stop_prevents_new_commands(self):
        self.ia.stop()
        self.control()
        self.ia.plc.write.assert_not_called()

    def test_connection_closed_when_processing_fails(self):
        plc = self.ia.plc
        self.namespace["LogixDriver"].return_value = plc
        self.ia._procesar_frames = Mock(side_effect=RuntimeError("fallo simulado"))
        self.ia.run()
        plc.open.assert_called_once()
        plc.close.assert_called_once()
        self.assertIsNone(self.ia.plc)
        self.ia.error_signal.emit.assert_called_once()

    def test_cuda_explicit_in_processing(self):
        self.ia._running = True
        self.ia._frame_pendiente = object()
        model = Mock()
        model.track.return_value = [SimpleNamespace(boxes=None, plot=Mock())]
        self.ia.model = model
        self.ia.resultado_signal.emit.side_effect = lambda *_: self.ia.requestInterruption()
        self.ia._procesar_frames()
        self.assertEqual(model.track.call_args.kwargs, {"persist": True, "device": 0})


if __name__ == "__main__":
    unittest.main()
