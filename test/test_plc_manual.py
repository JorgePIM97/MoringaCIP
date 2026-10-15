import sys
import unittest
import csv
from tempfile import TemporaryDirectory
from unittest.mock import patch
from pathlib import Path
from pycomm3 import Tag

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from controlador.plc_test import PLCTest


class FakePLC:
    def __init__(self):
        self.values = {PLCTest.AVANCE: True, PLCTest.RETROCESO: False, "sensor": True}
        self.writes = []
        self.closed = False

    def open(self):
        return True

    def close(self):
        self.closed = True

    def read(self, *tags):
        results = [Tag(t, self.values[t], "BOOL", None) for t in tags]
        return results if len(tags) > 1 else results[0]

    def write(self, tag, value):
        self.values[tag] = value
        self.writes.append((tag, value))
        if self.values[PLCTest.AVANCE] and self.values[PLCTest.RETROCESO]:
            raise AssertionError("Mandos simultáneos")
        return Tag(tag, value, "BOOL", None)


class ManualPLCTests(unittest.TestCase):
    def service(self, plc, **kwargs):
        return PLCTest("192.168.1.10", driver_factory=lambda ip: plc, **kwargs)

    def test_single_false_tag_is_successful_response(self):
        response = Tag(PLCTest.RETROCESO, False, "BOOL", None)
        self.assertEqual(PLCTest._validar(response), [response])

    def test_real_tag_error_is_rejected(self):
        response = Tag(PLCTest.AVANCE, False, "BOOL", "Write failed")
        for responses in (response, [response], (response,)):
            with self.subTest(responses=responses), self.assertRaises(RuntimeError):
                PLCTest._validar(responses)

    def test_missing_tag_value_is_rejected(self):
        with self.assertRaises(RuntimeError):
            PLCTest._validar(Tag(PLCTest.AVANCE, None, "BOOL", None))

    def test_connection_does_not_write(self):
        plc = FakePLC()
        self.assertEqual(self.service(plc).ejecutar("comunicacion"), (True, False))
        self.assertEqual(plc.writes, [])
        self.assertTrue(plc.closed)

    def test_reverse_disables_advance_first(self):
        plc = FakePLC()
        self.assertEqual(self.service(plc).ejecutar("retroceso"), (False, True))
        self.assertEqual(plc.writes[0], (PLCTest.AVANCE, False))

    def test_shutdown_requires_sensor(self):
        plc = FakePLC()
        with self.assertRaises(ValueError):
            self.service(plc).ejecutar("apagar")
        self.assertEqual(plc.writes, [])

    def test_shutdown_retracts_before_deenergizing(self):
        plc = FakePLC()
        self.assertEqual(self.service(plc, tag_retraido="sensor").ejecutar("apagar"), (False, False))
        self.assertEqual(plc.writes, [(PLCTest.AVANCE, False), (PLCTest.RETROCESO, True),
                                      (PLCTest.AVANCE, False), (PLCTest.RETROCESO, False)])

    def test_timeout_does_not_claim_shutdown(self):
        plc = FakePLC()
        plc.values["sensor"] = False
        with self.assertRaises(RuntimeError):
            self.service(plc, tag_retraido="sensor", timeout=0).ejecutar("apagar")
        self.assertTrue(plc.values[PLCTest.RETROCESO])
        self.assertTrue(plc.closed)

    def test_measures_each_piston_and_appends_csv(self):
        plc = FakePLC()
        tags = PLCTest.SENSORES["avance"]
        plc.values.update(dict.fromkeys(tags, False))
        original_read = plc.read
        readings = iter([(False, False), (True, False), (True, True),
                         (True, True), (True, True)])

        def read(*requested):
            if requested == tags:
                plc.values.update(zip(tags, next(readings)))
            return original_read(*requested)

        plc.read = read
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tiempos.csv"
            service = self.service(plc, medir=True, csv_path=path)
            with patch("controlador.plc_test.time.perf_counter", side_effect=[1, 1.02, 1.05]):
                service.ejecutar("avance")
            self.assertEqual([r["tiempo_ms"] for r in service.mediciones], [20, 50])
            service.ejecutar("avance")
            with path.open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 4)
            self.assertEqual([r["estado"] for r in rows],
                             ["completado", "completado", "sensor_ya_activo", "sensor_ya_activo"])
            self.assertEqual(rows[2]["tiempo_ms"], "")

    def test_measured_shutdown_requires_both_sensors_and_logs_timeout(self):
        plc = FakePLC()
        tags = PLCTest.SENSORES["retroceso"]
        plc.values.update({tags[0]: True, tags[1]: False})
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tiempos.csv"
            service = self.service(plc, medir=True, csv_path=path, timeout=0)
            with self.assertRaises(RuntimeError):
                service.ejecutar("apagar")
            self.assertTrue(plc.values[PLCTest.RETROCESO])
            self.assertEqual([r["estado"] for r in service.mediciones],
                             ["sensor_ya_activo", "timeout"])
            plc.values[tags[1]] = True
            self.assertEqual(service.ejecutar("apagar"), (False, False))

    def test_invalid_sensor_prevents_movement(self):
        plc = FakePLC()
        plc.values.update(dict.fromkeys(PLCTest.SENSORES["avance"], 1))
        with TemporaryDirectory() as directory:
            service = self.service(plc, medir=True, csv_path=Path(directory) / "tiempos.csv")
            with self.assertRaises(RuntimeError):
                service.ejecutar("avance")
            self.assertEqual(plc.writes, [])
            self.assertTrue(plc.closed)
