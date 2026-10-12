#C:\MoringaQT\controlador\threads\ia_thread.py
from PyQt6.QtCore import QThread, pyqtSignal
from collections import defaultdict
from threading import Lock
import numpy as np
import time
from pathlib import Path
import cv2
from ultralytics import YOLO
from pycomm3 import LogixDriver


class IAThread(QThread):
    resultado_signal = pyqtSignal(np.ndarray)
    error_signal     = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.modelo_path = str(Path(__file__).resolve().parents[3] / "models" / "best_moringa_1.pt")
        self.plc_ip = "192.168.1.10"
        self.tag_avance_izq = "CMD_ON_Cuchilla_Izquierda"
        self.tag_retroceso_izq = "CMD_OFF_Cuchilla_Izquierda"
        self.plc = None
        self.lock_plc = Lock()

        # ── Geometría del frame ──────────────────────────────────────────
        self.ancho_frame        = 848   # resolución RealSense
        self.alto_frame         = 480
        self.mitad_ancho_frame  = self.ancho_frame / 2
        self.inicio_region_izq  = 0
        self.fin_region_izq     = self.mitad_ancho_frame
        self.inicio_region_der  = self.mitad_ancho_frame
        self.fin_region_der     = self.ancho_frame
        self.umbral_trigger     = 240   # ajusta según tu cámara

        # ── Historial de tracks ──────────────────────────────────────────
        self.track_history = defaultdict(list)

        # ── Conteo ───────────────────────────────────────────────────────
        self.conteo_cuchillas_abiertas = {
            "izquierdo": {"contadas": [], "total": 0},
            "derecho":   {"contadas": [], "total": 0},
        }
        self.conteo_cuchillas_cerradas = {
            "izquierdo": {"contadas": [], "total": 0},
            "derecho":   {"contadas": [], "total": 0},
        }

        # ── Locks por lado ───────────────────────────────────────────────
        self.lock_izq = Lock()
        self.lock_der = Lock()

        # ── Estado interno ───────────────────────────────────────────────
        self.model            = None
        self._frame_pendiente = None
        self._running         = False
        self._frame_lock      = Lock()

    # ────────────────────────────────────────────────────────────────────
    # API pública
    # ────────────────────────────────────────────────────────────────────

    def iniciar_modelo(self):
        """Carga YOLO desde el hilo de IA durante su arranque."""
        self.model = YOLO(self.modelo_path)

    def enviar_frame(self, color_frame, _depth_frame=None):
        """CamaraThread llama esto en cada frame. Guarda solo el más reciente."""
        with self._frame_lock:
            self._frame_pendiente = color_frame.copy()

    def stop(self):
        self.requestInterruption()
        self._running = False
        self.wait()

    def conectar_plc(self):
        self.plc = LogixDriver(self.plc_ip)
        if not self.plc.open():
            raise RuntimeError(f"No se pudo conectar con el PLC {self.plc_ip}")
        print(f"[PLC] Conexión persistente establecida: {self.plc_ip}")

    def desconectar_plc(self):
        with self.lock_plc:
            if self.plc is not None:
                try:
                    self.plc.close()
                finally:
                    self.plc = None

    def escribir_estado_cuchilla_izquierda(self, avance, retroceso, accion):
        """Mando del maestro; readback de consignas, no de salidas físicas."""
        if avance and retroceso:
            raise ValueError("AVANCE y RETROCESO no pueden estar activos simultáneamente")
        with self.lock_plc:
            if self.isInterruptionRequested():
                return False
            if self.plc is None:
                raise RuntimeError("No existe conexión con el PLC")
            t0 = time.perf_counter()
            resultados = self.plc.write(
                (self.tag_avance_izq, avance),
                (self.tag_retroceso_izq, retroceso),
            )
            t1 = time.perf_counter()
            if len(resultados) != 2 or not all(bool(r) for r in resultados):
                raise RuntimeError(f"Error PLC escribiendo la orden de {accion}")
            lecturas = self.plc.read(self.tag_avance_izq, self.tag_retroceso_izq)
            t2 = time.perf_counter()
            if len(lecturas) != 2 or not all(bool(r) for r in lecturas):
                raise RuntimeError(f"Error PLC leyendo la consigna de {accion}")
            valor_avance, valor_retroceso = (r.value for r in lecturas)
            print(
                f"[PERF-3A-{accion}] T_WRITE={(t1-t0)*1000:.3f} ms | "
                f"T_READBACK={(t2-t1)*1000:.3f} ms | T_3A={(t2-t0)*1000:.3f} ms | "
                f"AVANCE={valor_avance} | RETROCESO={valor_retroceso}"
            )
            if (valor_avance, valor_retroceso) != (avance, retroceso):
                raise RuntimeError(f"Readback PLC distinto de la consigna de {accion}")
            return True

    def abrir_cuchilla_izquierda(self):
        return self.escribir_estado_cuchilla_izquierda(False, True, "APERTURA")

    def cerrar_cuchilla_izquierda(self):
        return self.escribir_estado_cuchilla_izquierda(True, False, "CIERRE")

    # ────────────────────────────────────────────────────────────────────
    # Lógica del maestro adaptada a 848×480 y umbral y=240
    # ────────────────────────────────────────────────────────────────────

    def _control_cuchilla(
            self,
            annotated_frame,
            bbx,
            id_moringa,
            centro_moringa,
            punto_abrir,
            punto_cerrar,
            umbral_abrir,
            umbral_cerrar,
            rect_arr_start, rect_arr_end,
            rect_aba_start, rect_aba_end,
            inicio_region,
            fin_region,
            lado: str,
            lock: Lock):

        if not (inicio_region < bbx[0] < fin_region):
            return

        with lock:
            c_abiertas = self.conteo_cuchillas_abiertas[lado]
            c_cerradas = self.conteo_cuchillas_cerradas[lado]

            cv2.line(annotated_frame,
                     (0, self.umbral_trigger),
                     (self.ancho_frame, self.umbral_trigger),
                     (255, 0, 0), 1)
            cv2.line(annotated_frame,
                     (int(self.mitad_ancho_frame), 0),
                     (int(self.mitad_ancho_frame), self.alto_frame),
                     (255, 0, 0), 1)

            punto_abrir_activo  = umbral_abrir  <= self.umbral_trigger
            punto_cerrar_activo = umbral_cerrar <= self.umbral_trigger

            color_abrir  = (255, 255, 255) if punto_abrir_activo  else (255, 0, 0)
            color_cerrar = (255, 255, 255) if punto_cerrar_activo else (0, 255, 0)

            cv2.circle(annotated_frame, centro_moringa, 5, (0, 255, 255), -1)
            cv2.rectangle(annotated_frame, rect_arr_start, rect_arr_end, color_abrir,  2)
            cv2.rectangle(annotated_frame, rect_aba_start, rect_aba_end, color_cerrar, 2)
            cv2.line(annotated_frame, punto_abrir, punto_cerrar, (0, 255, 255), 2)

            if punto_abrir_activo and id_moringa not in c_abiertas["contadas"]:
                if lado == "izquierdo" and not self.abrir_cuchilla_izquierda():
                    return
                print(f"[{lado}] Cuchilla ABIERTA - ID {id_moringa}")
                c_abiertas["contadas"].append(id_moringa)
                c_abiertas["total"] += 1

            elif punto_cerrar_activo and id_moringa not in c_cerradas["contadas"]:
                if lado == "izquierdo" and not self.cerrar_cuchilla_izquierda():
                    return
                print(f"[{lado}] Cuchilla CERRADA - ID {id_moringa}")
                c_cerradas["contadas"].append(id_moringa)
                c_cerradas["total"] += 1

            cv2.putText(annotated_frame, f"Surco {lado}",
                        (int(inicio_region + 30), 360),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(annotated_frame, f"Abiertas: {c_abiertas['total']}",
                        (int(inicio_region + 30), 390),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.putText(annotated_frame, f"Cerradas: {c_cerradas['total']}",
                        (int(inicio_region + 30), 420),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # ────────────────────────────────────────────────────────────────────
    # Loop principal del hilo
    # ────────────────────────────────────────────────────────────────────

    def run(self):
        self._running = True
        try:
            self.iniciar_modelo()
            if self.isInterruptionRequested():
                return
            self.conectar_plc()
            self._procesar_frames()
        except Exception as e:
            self.error_signal.emit(f"Error IA/PLC: {e}")
        finally:
            self._running = False
            try:
                self.desconectar_plc()
            except Exception as e:
                self.error_signal.emit(f"Error al cerrar conexión PLC: {e}")

    def _procesar_frames(self):
        while self._running and not self.isInterruptionRequested():
            inicio_frame = time.perf_counter()
            # 1. Tomar el frame más reciente
            frame = None
            with self._frame_lock:
                if self._frame_pendiente is not None:
                    frame = self._frame_pendiente
                    self._frame_pendiente = None

            if frame is None:
                self.msleep(5)
                continue

            try:
                # 2. Inferencia YOLO
                inicio_yolo = time.perf_counter()
                result = self.model.track(frame, persist=True, device=0)[0]
                fin_yolo = time.perf_counter()
                annotated_frame = result.plot(labels=False, boxes=True, masks=False)

                # 3. Procesar detecciones con hilos por lado
                if result.boxes and result.boxes.is_track:
                    boxes_xywh = result.boxes.xywh.cpu()
                    boxes_xyxy = result.boxes.xyxy.cpu()
                    track_ids  = result.boxes.id.int().cpu().tolist()

                    for box_xywh, box_xyxy, track_id in zip(boxes_xywh, boxes_xyxy, track_ids):
                        x, y, w, h = box_xywh

                        track = self.track_history[track_id]
                        track.append((float(x), float(y)))
                        if len(track) > 30:
                            track.pop(0)

                        punto_centro  = (int(x), int(y))
                        punto_abrir   = (int(x), int(y - 20))
                        punto_cerrar  = (int(x), int(y + 20))
                        umbral_abrir  = int(y) - 20
                        umbral_cerrar = int(y) + 20

                        x_min, y_min = float(box_xyxy[0]), float(box_xyxy[1])
                        x_max, y_max = float(box_xyxy[2]), float(box_xyxy[3])

                        rect_arr_start = (int(x_min), int(y - 20))
                        rect_arr_end   = (int(x_max), int(y - 15))
                        rect_aba_start = (int(x_min), int(y + 20))
                        rect_aba_end   = (int(x_max), int(y + 15))

                        args = (
                            annotated_frame, box_xywh, track_id,
                            punto_centro, punto_abrir, punto_cerrar,
                            umbral_abrir, umbral_cerrar,
                            rect_arr_start, rect_arr_end,
                            rect_aba_start, rect_aba_end,
                        )

                        if self.isInterruptionRequested():
                            return
                        # El QThread ya separa la IA de la interfaz. Procesar
                        # en orden permite propagar fallos PLC y detener el ciclo.
                        self._control_cuchilla(
                            *args, self.inicio_region_izq, self.fin_region_izq,
                            "izquierdo", self.lock_izq,
                        )
                        # Canal derecho: solo tracking/HUD/conteos, sin escritura PLC.
                        self._control_cuchilla(
                            *args, self.inicio_region_der, self.fin_region_der,
                            "derecho", self.lock_der,
                        )

                # 4. Emitir frame anotado a la UI
                self.resultado_signal.emit(annotated_frame)
                fin_frame = time.perf_counter()
                print(
                    f"[PERF] T_YOLO={(fin_yolo-inicio_yolo)*1000:.2f} ms | "
                    f"T_PROCESAMIENTO={(fin_frame-fin_yolo)*1000:.2f} ms | "
                    f"T_FRAME={(fin_frame-inicio_frame)*1000:.2f} ms | "
                    f"FPS={1/(fin_frame-inicio_frame):.2f}"
                )

            except Exception as e:
                raise RuntimeError(f"Procesamiento de visión/control: {e}") from e
