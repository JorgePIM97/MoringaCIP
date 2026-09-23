from collections import defaultdict
import cv2
import numpy as np
from ultralytics import YOLO
import threading
import datetime
import pandas as pd
import os
from datetime import datetime

class MoringaAlgoritmo():
    def __init__(self):
        self.modelo_path = "C:/Moringa/utils/models/best_moringa_1.pt"
        self.video_path = "C:/Moringa/utils/videos/moringa_1_video.mp4"

        self.track_history = defaultdict(lambda: [])

        self.ancho_frame = 1280
        self.largo_frame = 720
        self.mitad_ancho_frame = self.ancho_frame / 2

        self.inicio_region_izq = 0
        self.fin_region_izq = self.mitad_ancho_frame
        self.inicio_region_der = self.mitad_ancho_frame
        self.fin_region_der = self.ancho_frame

        self.conteo_cuchillas_abiertas = {
            "izquierdo": {"contadas": [], "total": 0},
            "derecho":   {"contadas": [], "total": 0},
        }

        self.conteo_cuchillas_cerradas = {
            "izquierdo": {"contadas": [], "total": 0},
            "derecho":   {"contadas": [], "total": 0},
        }

        self.lock_izq = threading.Lock()
        self.lock_der = threading.Lock()

        self.csv_path = "C:/Moringa/utils/reportes/recorrido_video_1.csv"



    def cargar_modelo(self, modelo_path):
        return YOLO(modelo_path)

    def cargar_video(self, video_path):
        return cv2.VideoCapture(video_path)

    def fecha_y_hora(self):
        # Obtener fecha y hora actual
        now = datetime.now()
        fecha = now.strftime("%d/%m/%Y")
        hora  = now.strftime("%H:%M:%S")
        return fecha, hora

    def control_cuchilla(
            self,
            annotated_frame,
            bbx,                      # xywh — para verificar región por centro x
            id_moringa,
            centro_moringa,
            punto_abrir,
            punto_cerrar,
            umbral_abrir,
            umbral_cerrar,
            rectangulo_arriba_start,
            rectangulo_arriba_end,
            rectangulo_abajo_start,
            rectangulo_abajo_end,
            inicio_region,
            fin_region,
            lado: str,
            lock: threading.Lock):

        # Solo procesar si la moringa está en esta región (centro x del box)
        if not (inicio_region < bbx[0] < fin_region):
            return

        with lock:
            conteo_lado_cuchillas_abiertas = self.conteo_cuchillas_abiertas[lado]
            conteo_lado_cuchillas_cerradas = self.conteo_cuchillas_cerradas[lado]

            cuchilla_abierta_contada = conteo_lado_cuchillas_abiertas["contadas"]
            cuchilla_cerrada_contada = conteo_lado_cuchillas_cerradas["contadas"]

            fecha, hora = self.fecha_y_hora()

            cv2.putText(
                annotated_frame,
                "Desmalezadora Vision",
                (int(10), int(50)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
            )

            cv2.putText(
                annotated_frame,
                f"Fecha {fecha}",
                (int(10), int(85)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
            )
            cv2.putText(
                annotated_frame,
                f"Hora {hora}",
                (int(10), int(115)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
            )

            cv2.line(annotated_frame, (0, 500), (1280, 500), (255, 0, 0), 1)
            cv2.line(annotated_frame, (640, 0), (640, 720), (255, 0, 0), 1)

            # ── Determinar si cada punto cruzó el umbral ──────────────────────
            punto_abrir_activo  = umbral_abrir  <= 500
            punto_cerrar_activo = umbral_cerrar <= 500

            # ── Color: blanco si activo (cruzó umbral), azul si no ───────────
            color_abrir  = (255, 255, 255) if punto_abrir_activo  else (255, 0, 0)
            color_cerrar = (255, 255, 255) if punto_cerrar_activo else (0, 255, 0)

            cv2.circle(annotated_frame, centro_moringa, 5, (0, 255, 255), -1)

            # ── Rectángulos arriba/abajo del bounding box ─────────────────────
            # Se pintan BLANCO cuando cruzan el umbral, color base si no
            cv2.rectangle(annotated_frame, rectangulo_arriba_start, rectangulo_arriba_end, color_abrir,  2)
            cv2.rectangle(annotated_frame, rectangulo_abajo_start,  rectangulo_abajo_end,  color_cerrar, 2)

            cv2.line(annotated_frame, punto_abrir, punto_cerrar, (0, 255, 255), 2)

            # ── Lógica de conteo ──────────────────────────────────────────────
            if umbral_abrir <= 500 and id_moringa not in cuchilla_abierta_contada:
                print(f"[{lado}] Cuchilla ABIERTA - ID {id_moringa}")
                cuchilla_abierta_contada.append(id_moringa)
                conteo_lado_cuchillas_abiertas["total"] += 1

            elif umbral_cerrar <= 500 and id_moringa not in cuchilla_cerrada_contada:
                print(f"[{lado}] Cuchilla CERRADA - ID {id_moringa}")
                cuchilla_cerrada_contada.append(id_moringa)
                conteo_lado_cuchillas_cerradas["total"] += 1

            else:
                cv2.circle(annotated_frame, centro_moringa, 5, (0, 255, 255), -1)

            # ── HUD de conteo en pantalla ─────────────────────────────────────
            cv2.putText(
                annotated_frame,
                f"Surco {lado}",
                (int(inicio_region + 30), 620),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
            )
            cv2.putText(
                annotated_frame,
                f"Abiertas: {conteo_lado_cuchillas_abiertas['total']}",
                (int(inicio_region + 30), 660),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2
            )
            cv2.putText(
                annotated_frame,
                f"Cerradas: {conteo_lado_cuchillas_cerradas['total']}",
                (int(inicio_region + 30), 690),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )

    def generar_csv(self, id_moringa, timestamp, lado, total_abiertas, total_cerradas, estado):
        datos = {
            "id_moringa": id_moringa,
            "fecha_y_hora": timestamp,
            "lado": lado,
            "total_abiertas": total_abiertas,
            "total_cerradas": total_cerradas,
            "estado": estado
        }
        df_datos = pd.DataFrame([datos])
        if os.path.exists(self.csv_path):
            df_datos.to_csv(self.csv_path, mode='a', header=False, index=False)
        else:
            df_datos.to_csv(self.csv_path, index=False)

    def main(self):
        model = self.cargar_modelo(self.modelo_path)
        cap = self.cargar_video(self.video_path)

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            result = model.track(frame, persist=True)[0]
            annotated_frame = result.plot(labels=False,boxes=True, masks=False)

            if result.boxes and result.boxes.is_track:
                # ── Obtener ambos formatos de boxes ───────────────────────────
                boxes_xywh = result.boxes.xywh.cpu()   # (cx, cy, w, h)
                boxes_xyxy = result.boxes.xyxy.cpu()   # (x_min, y_min, x_max, y_max)
                track_ids  = result.boxes.id.int().cpu().tolist()

                threads = []

                for box_xywh, box_xyxy, track_id in zip(boxes_xywh, boxes_xyxy, track_ids):
                    x, y, w, h = box_xywh

                    track = self.track_history[track_id]
                    track.append((float(x), float(y)))
                    if len(track) > 30:
                        track.pop(0)

                    # ── Puntos de control ──────────────────────────────────────
                    punto_centro  = (int(x), int(y))
                    punto_abrir   = (int(x), int(y - 20))
                    punto_cerrar  = (int(x), int(y + 20))
                    umbral_abrir  = int(y) - 20
                    umbral_cerrar = int(y) + 20

                    # ── Esquinas del bounding box (desde xyxy) ─────────────────
                    x_min = float(box_xyxy[0])
                    y_min = float(box_xyxy[1])
                    x_max = float(box_xyxy[2])
                    y_max = float(box_xyxy[3])

                    # ── Rectángulos arriba y abajo del bbox ───────────────────
                    # Se vuelven BLANCOS cuando el punto cruza el umbral (< 500)

                    rectangulo_arriba_start = (int(x_min), int(y-20))
                    rectangulo_arriba_end   = (int(x_max), int(y-15))

                    
                    rectangulo_abajo_start  = (int(x_min), int(y+20))
                    rectangulo_abajo_end    = (int(x_max), int(y+15))

                    args_comunes = (
                        annotated_frame, box_xywh, track_id,  # <-- box_xywh para región
                        punto_centro, punto_abrir, punto_cerrar,
                        umbral_abrir, umbral_cerrar,
                        rectangulo_arriba_start, rectangulo_arriba_end,
                        rectangulo_abajo_start,  rectangulo_abajo_end
                    )

                    threads.append(threading.Thread(
                        target=self.control_cuchilla,
                        args=(*args_comunes,
                              self.inicio_region_izq, self.fin_region_izq,
                              "izquierdo", self.lock_izq)
                    ))

                    threads.append(threading.Thread(
                        target=self.control_cuchilla,
                        args=(*args_comunes,
                              self.inicio_region_der, self.fin_region_der,
                              "derecho", self.lock_der)
                    ))

                for t in threads:
                    t.start()
                for t in threads:
                    t.join()

            cv2.imshow("Moringa Algoritmo", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    moringa_algoritmo = MoringaAlgoritmo()
    moringa_algoritmo.main()