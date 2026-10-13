import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

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
        results = [SimpleNamespace(value=self.values[t]) for t in tags]
        return results if len(tags) > 1 else results[0]

    def write(self, tag, value):
        self.values[tag] = value
        self.writes.append((tag, value))
        if self.values[PLCTest.AVANCE] and self.values[PLCTest.RETROCESO]:
            raise AssertionError("Mandos simultáneos")
        return SimpleNamespace(value=value)


class ManualPLCTests(unittest.TestCase):
    def service(self, plc, **kwargs):
        return PLCTest("192.168.1.10", driver_factory=lambda ip: plc, **kwargs)

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
