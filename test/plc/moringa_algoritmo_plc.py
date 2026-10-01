from collections import defaultdict
import cv2
from ultralytics import YOLO
import threading
import pandas as pd
import os
from datetime import datetime
import time

# Allen-Bradley / EtherNet-IP
from pycomm3 import LogixDriver


class MoringaAlgoritmo():

    def __init__(self):

        # ============================================================
        # VISIÓN
        # ============================================================

        self.modelo_path = "C:/Users/E-PIM-L_07/Documents/JorgeProyectos/MoringaCIP/models/best_moringa_1.pt"
        self.video_path = "C:/Users/E-PIM-L_07/Documents/JorgeProyectos/utils/videos/moringa_1_video_x15.mp4"

        self.track_history = defaultdict(lambda: [])

        self.ancho_frame = 1280
        self.largo_frame = 720
        self.mitad_ancho_frame = self.ancho_frame / 2

        self.inicio_region_izq = 0
        self.fin_region_izq = self.mitad_ancho_frame

        self.inicio_region_der = self.mitad_ancho_frame
        self.fin_region_der = self.ancho_frame

        # ============================================================
        # CONTEO CUCHILLAS
        # ============================================================

        self.conteo_cuchillas_abiertas = {
            "izquierdo": {
                "contadas": [],
                "total": 0
            },
            "derecho": {
                "contadas": [],
                "total": 0
            },
        }

        self.conteo_cuchillas_cerradas = {
            "izquierdo": {
                "contadas": [],
                "total": 0
            },
            "derecho": {
                "contadas": [],
                "total": 0
            },
        }

        self.lock_izq = threading.Lock()
        self.lock_der = threading.Lock()

        self.csv_path = (
            "C:/Moringa/utils/reportes/"
            "recorrido_video_1.csv"
        )

        # ============================================================
        # CONFIGURACIÓN ALLEN-BRADLEY
        # ============================================================

        # IP real del PLC
        self.plc_ip = "192.168.1.10"

        # Tags BOOL creados en Studio 5000
        # Cuchilla izquierda: electroválvula de dos órdenes mutuamente excluyentes.
        # AVANCE  = cerrar cuchillas / desmalezar
        # RETROCESO = abrir cuchillas / proteger moringa
        self.tag_avance_izq = "CMD_ON_Cuchilla_Izquierda"
        self.tag_retroceso_izq = "CMD_OFF_Cuchilla_Izquierda"

        # El canal derecho se conserva sin cambios por ahora.
        self.tag_derecho = "CMD_Cuchilla_Derecha"

        # Lock adicional para proteger la comunicación con el PLC
        self.lock_plc = threading.Lock()

        # Conexión persistente
        self.plc = None

        # NOTA: las direcciones físicas de AVANCE y RETROCESO se mantienen
        # gestionadas en Ladder. Python escribe únicamente los Controller Tags.

    # ================================================================
    # VISIÓN
    # ================================================================

    def cargar_modelo(self, modelo_path):
        return YOLO(modelo_path)


    def cargar_video(self, video_path):
        return cv2.VideoCapture(video_path)


    def fecha_y_hora(self):

        now = datetime.now()

        fecha = now.strftime("%d/%m/%Y")
        hora = now.strftime("%H:%M:%S")

        return fecha, hora


    # ================================================================
    # COMUNICACIÓN ALLEN-BRADLEY
    # ================================================================

    def escribir_tag(self, tag, valor):
        """Escritura simple. Se conserva para el canal derecho y pruebas."""
        try:
            with self.lock_plc:
                if self.plc is None:
                    print("[PLC] No existe conexión con el PLC")
                    return False

                t0 = time.perf_counter()
                resultado = self.plc.write(tag, valor)
                t1 = time.perf_counter()

                print(
                    f"[PERF] T_WRITE={((t1 - t0) * 1000):.3f} ms | "
                    f"{tag}={valor}"
                )

            if resultado:
                print(f"[PLC] {tag} = {valor}")
                return True

            print(f"[PLC] Error escribiendo {tag}")
            return False

        except Exception as error:
            print(f"[PLC] Error de comunicación: {error}")
            return False

    def escribir_estado_cuchilla_izquierda(self, avance, retroceso, accion):
        """
        Escribe las dos órdenes de la electroválvula izquierda en una misma
        llamada de pycomm3. La combinación AVANCE=1 / RETROCESO=1 está
        prohibida por software.
        """
        if avance and retroceso:
            print(
                "[PLC][ERROR] Estado inválido: "
                "AVANCE y RETROCESO no pueden estar activos simultáneamente"
            )
            return False

        try:
            with self.lock_plc:
                if self.plc is None:
                    print("[PLC] No existe conexión con el PLC")
                    return False

                t0 = time.perf_counter()

                # Se envían ambas consignas juntas:
                # cerrar -> AVANCE=1, RETROCESO=0
                # abrir  -> AVANCE=0, RETROCESO=1
                resultados = self.plc.write(
                    (self.tag_avance_izq, avance),
                    (self.tag_retroceso_izq, retroceso)
                )

                t1 = time.perf_counter()
                tiempo_write_ms = (t1 - t0) * 1000

                # Readback de los Controller Tags para comprobar la consigna.
                # Esto NO sustituye la futura medición 3B de las salidas físicas.
                lecturas = self.plc.read(
                    self.tag_avance_izq,
                    self.tag_retroceso_izq
                )
                t2 = time.perf_counter()

                valor_avance = lecturas[0].value
                valor_retroceso = lecturas[1].value

                tiempo_readback_ms = (t2 - t1) * 1000
                tiempo_3a_ms = (t2 - t0) * 1000

                print(
                    f"[PERF-3A-{accion}] "
                    f"T_WRITE={tiempo_write_ms:.3f} ms | "
                    f"T_READBACK={tiempo_readback_ms:.3f} ms | "
                    f"T_3A={tiempo_3a_ms:.3f} ms | "
                    f"AVANCE={valor_avance} | "
                    f"RETROCESO={valor_retroceso}"
                )

                if (valor_avance != avance or
                        valor_retroceso != retroceso):
                    print(
                        f"[PERF-3A-{accion}][WARNING] "
                        f"Esperado AVANCE={avance}, RETROCESO={retroceso}; "
                        f"leído AVANCE={valor_avance}, "
                        f"RETROCESO={valor_retroceso}"
                    )
                    return False

                if valor_avance and valor_retroceso:
                    print(
                        "[PLC][CRITICAL] Readback inválido: "
                        "AVANCE=1 y RETROCESO=1"
                    )
                    return False

                return all(bool(r) for r in resultados)

        except Exception as error:
            print(f"[PLC] Error de comunicación: {error}")
            return False

    # ================================================================
    # CONTROL CUCHILLA IZQUIERDA - ELECTROVÁLVULA
    # ================================================================

    def cerrar_cuchilla_izquierda(self):
        """AVANCE: cerrar cuchillas para desmalezar."""
        ok = self.escribir_estado_cuchilla_izquierda(
            avance=True,
            retroceso=False,
            accion="CIERRE"
        )
        if ok:
            print(
                "[PLC] Cuchilla izquierda CERRADA / DESMALEZAR -> "
                "AVANCE=1, RETROCESO=0"
            )
        return ok

    def abrir_cuchilla_izquierda(self):
        """RETROCESO: abrir cuchillas para proteger la moringa."""
        ok = self.escribir_estado_cuchilla_izquierda(
            avance=False,
            retroceso=True,
            accion="APERTURA"
        )
        if ok:
            print(
                "[PLC] Cuchilla izquierda ABIERTA / PROTEGER -> "
                "AVANCE=0, RETROCESO=1"
            )
        return ok

    def encender_gpio(self, tag_lado):
        """Compatibilidad temporal para el canal derecho: TRUE=cerrar."""
        self.escribir_tag(tag_lado, True)
        print(f"[PLC] Cuchilla CERRADA -> {tag_lado}")

    def apagar_gpio(self, tag_lado):
        """Compatibilidad temporal para el canal derecho: FALSE=abrir."""
        self.escribir_tag(tag_lado, False)
        print(f"[PLC] Cuchilla ABIERTA -> {tag_lado}")

    def conectar_plc(self):
        try:
            print(f"[PLC] Conectando con {self.plc_ip}...")

            self.plc = LogixDriver(self.plc_ip)
            self.plc.open()

            print("[PLC] Conexión establecida")

        except Exception as error:
            print(f"[PLC] Error al conectar: {error}")
            self.plc = None


    def desconectar_plc(self):
        if self.plc is not None:
            try:
                self.plc.close()
                print("[PLC] Conexión cerrada")
            except Exception as error:
                print(f"[PLC] Error al cerrar conexión: {error}")
            finally:
                self.plc = None

    # ================================================================
    # LÓGICA DE CONTROL
    # ================================================================

    def control_cuchilla(
            self,
            annotated_frame,
            bbx,
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
            lock: threading.Lock,
            tag_lado):


        # Verificar si la moringa pertenece
        # a esta región del frame
        if not (
            inicio_region
            < bbx[0]
            < fin_region
        ):
            return


        with lock:

            conteo_abiertas = (
                self.conteo_cuchillas_abiertas[lado]
            )

            conteo_cerradas = (
                self.conteo_cuchillas_cerradas[lado]
            )


            cuchilla_abierta_contada = (
                conteo_abiertas["contadas"]
            )

            cuchilla_cerrada_contada = (
                conteo_cerradas["contadas"]
            )


            fecha, hora = self.fecha_y_hora()


            # ========================================================
            # HUD
            # ========================================================

            cv2.putText(
                annotated_frame,
                "Desmalezadora Vision",
                (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )


            cv2.putText(
                annotated_frame,
                f"Fecha {fecha}",
                (10, 85),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )


            cv2.putText(
                annotated_frame,
                f"Hora {hora}",
                (10, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )


            # Línea de activación
            cv2.line(
                annotated_frame,
                (0, 500),
                (1280, 500),
                (255, 0, 0),
                1
            )


            # División izquierda / derecha
            cv2.line(
                annotated_frame,
                (640, 0),
                (640, 720),
                (255, 0, 0),
                1
            )


            # ========================================================
            # UMBRALES
            # ========================================================

            punto_abrir_activo = (
                umbral_abrir <= 500
            )

            punto_cerrar_activo = (
                umbral_cerrar <= 500
            )


            color_abrir = (
                (255, 255, 255)
                if punto_abrir_activo
                else (255, 0, 0)
            )


            color_cerrar = (
                (255, 255, 255)
                if punto_cerrar_activo
                else (0, 255, 0)
            )


            cv2.circle(
                annotated_frame,
                centro_moringa,
                5,
                (0, 255, 255),
                -1
            )


            cv2.rectangle(
                annotated_frame,
                rectangulo_arriba_start,
                rectangulo_arriba_end,
                color_abrir,
                2
            )


            cv2.rectangle(
                annotated_frame,
                rectangulo_abajo_start,
                rectangulo_abajo_end,
                color_cerrar,
                2
            )


            cv2.line(
                annotated_frame,
                punto_abrir,
                punto_cerrar,
                (0, 255, 255),
                2
            )


            # ========================================================
            # APERTURA DE CUCHILLA
            # ========================================================

            if (
                umbral_abrir <= 500
                and
                id_moringa
                not in cuchilla_abierta_contada
            ):

                print(
                    f"[{lado}] "
                    f"Cuchilla ABIERTA "
                    f"- ID {id_moringa}"
                )

                cuchilla_abierta_contada.append(
                    id_moringa
                )

                if lado == "izquierdo":
                    # RETROCESO: abrir / proteger moringa
                    self.abrir_cuchilla_izquierda()
                else:
                    # Canal derecho conservado temporalmente con lógica anterior
                    # self.apagar_gpio(tag_lado)
                    print("Lado derecho del frame deshabilitado")
                    
                conteo_abiertas["total"] += 1


            # ========================================================
            # CIERRE DE CUCHILLA
            # ========================================================

            elif (
                umbral_cerrar <= 500
                and
                id_moringa
                not in cuchilla_cerrada_contada
            ):

                print(
                    f"[{lado}] "
                    f"Cuchilla CERRADA "
                    f"- ID {id_moringa}"
                )

                cuchilla_cerrada_contada.append(
                    id_moringa
                )

                if lado == "izquierdo":
                    # AVANCE: cerrar / desmalezar
                    self.cerrar_cuchilla_izquierda()
                else:
                    # Canal derecho conservado temporalmente con lógica anterior
                    # self.encender_gpio(tag_lado)
                    print("Lado derecho del frame deshabilitado")
                conteo_cerradas["total"] += 1


            # ========================================================
            # CONTADORES EN PANTALLA
            # ========================================================

            cv2.putText(
                annotated_frame,
                f"Surco {lado}",
                (
                    int(inicio_region + 30),
                    620
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )


            cv2.putText(
                annotated_frame,
                f"Abiertas: {conteo_abiertas['total']}",
                (
                    int(inicio_region + 30),
                    660
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2
            )


            cv2.putText(
                annotated_frame,
                f"Cerradas: {conteo_cerradas['total']}",
                (
                    int(inicio_region + 30),
                    690
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )


    # ================================================================
    # CSV
    # ================================================================

    def generar_csv(
            self,
            id_moringa,
            timestamp,
            lado,
            total_abiertas,
            total_cerradas,
            estado):


        datos = {

            "id_moringa":
                id_moringa,

            "fecha_y_hora":
                timestamp,

            "lado":
                lado,

            "total_abiertas":
                total_abiertas,

            "total_cerradas":
                total_cerradas,

            "estado":
                estado
        }


        df_datos = pd.DataFrame(
            [datos]
        )


        if os.path.exists(
            self.csv_path
        ):

            df_datos.to_csv(
                self.csv_path,
                mode="a",
                header=False,
                index=False
            )

        else:

            df_datos.to_csv(
                self.csv_path,
                index=False
            )


    # ================================================================
    # MAIN
    # ================================================================

    def main(self):
        model = self.cargar_modelo(self.modelo_path)
        cap = self.cargar_video(self.video_path)

        # FPS del video (el x8 tendrá un valor bajo, p. ej. 3.75)
        fps_video = cap.get(cv2.CAP_PROP_FPS)
        if fps_video <= 0:
            fps_video = 30.0  # respaldo si el archivo no trae FPS
        tiempo_objetivo_frame = 1.0 / fps_video
        print(f"[VIDEO] FPS del archivo: {fps_video:.2f}")

        self.conectar_plc()

        while cap.isOpened():
            inicio_frame = time.perf_counter()

            success, frame = cap.read()
            if not success:
                break


            inicio_yolo = time.perf_counter()

            result = model.track(
                frame,
                persist=True,
                device=0
            )[0]

            fin_yolo = time.perf_counter()

            tiempo_yolo_ms = (
                fin_yolo - inicio_yolo
            ) * 1000


            annotated_frame = result.plot(
                labels=False,
                boxes=True,
                masks=False
            )


            if (
                result.boxes
                and
                result.boxes.is_track
            ):


                boxes_xywh = (
                    result.boxes.xywh.cpu()
                )

                boxes_xyxy = (
                    result.boxes.xyxy.cpu()
                )

                track_ids = (
                    result.boxes.id
                    .int()
                    .cpu()
                    .tolist()
                )


                threads = []


                for (
                    box_xywh,
                    box_xyxy,
                    track_id
                ) in zip(
                    boxes_xywh,
                    boxes_xyxy,
                    track_ids
                ):


                    x, y, w, h = box_xywh


                    track = (
                        self.track_history[
                            track_id
                        ]
                    )

                    track.append(
                        (
                            float(x),
                            float(y)
                        )
                    )


                    if len(track) > 30:
                        track.pop(0)


                    # =================================================
                    # PUNTOS DE CONTROL
                    # =================================================

                    punto_centro = (
                        int(x),
                        int(y)
                    )

                    punto_abrir = (
                        int(x),
                        int(y - 20)
                    )

                    punto_cerrar = (
                        int(x),
                        int(y + 20)
                    )


                    umbral_abrir = (
                        int(y) - 20
                    )

                    umbral_cerrar = (
                        int(y) + 20
                    )


                    # =================================================
                    # BOUNDING BOX
                    # =================================================

                    x_min = float(
                        box_xyxy[0]
                    )

                    y_min = float(
                        box_xyxy[1]
                    )

                    x_max = float(
                        box_xyxy[2]
                    )

                    y_max = float(
                        box_xyxy[3]
                    )


                    rectangulo_arriba_start = (
                        int(x_min),
                        int(y - 20)
                    )

                    rectangulo_arriba_end = (
                        int(x_max),
                        int(y - 15)
                    )


                    rectangulo_abajo_start = (
                        int(x_min),
                        int(y + 20)
                    )

                    rectangulo_abajo_end = (
                        int(x_max),
                        int(y + 15)
                    )


                    args_comunes = (

                        annotated_frame,

                        box_xywh,

                        track_id,

                        punto_centro,

                        punto_abrir,

                        punto_cerrar,

                        umbral_abrir,

                        umbral_cerrar,

                        rectangulo_arriba_start,

                        rectangulo_arriba_end,

                        rectangulo_abajo_start,

                        rectangulo_abajo_end
                    )


                    # =================================================
                    # LADO IZQUIERDO
                    # =================================================

                    threads.append(

                        threading.Thread(

                            target=
                            self.control_cuchilla,

                            args=(

                                *args_comunes,

                                self.inicio_region_izq,

                                self.fin_region_izq,

                                "izquierdo",

                                self.lock_izq,

                                self.tag_avance_izq
                            )
                        )
                    )


                    # =================================================
                    # LADO DERECHO
                    # =================================================

                    threads.append(

                        threading.Thread(

                            target=
                            self.control_cuchilla,

                            args=(

                                *args_comunes,

                                self.inicio_region_der,

                                self.fin_region_der,

                                "derecho",

                                self.lock_der,

                                self.tag_derecho
                            )
                        )
                    )


                for t in threads:
                    t.start()


                for t in threads:
                    t.join()

            fin_procesamiento = time.perf_counter()

            tiempo_procesamiento_ms = (
                fin_procesamiento - fin_yolo
            ) * 1000

            fin_frame = time.perf_counter()

            tiempo_frame_ms = (
                fin_frame - inicio_frame
            ) * 1000

            fps_real = (
                1 / (fin_frame - inicio_frame)
            )                

            print(
                f"[PERF] "
                f"T_YOLO={tiempo_yolo_ms:.2f} ms | "
                f"T_PROCESAMIENTO={tiempo_procesamiento_ms:.2f} ms | "
                f"T_FRAME={tiempo_frame_ms:.2f} ms | "
                f"FPS={fps_real:.2f}"
            )

            fin_frame = time.perf_counter()
            # (aquí van tus prints de [PERF], para medir solo el procesamiento real)

            cv2.imshow("Moringa Algoritmo", annotated_frame)

            # Esperar solo el tiempo que sobra para respetar el FPS del video
            transcurrido = time.perf_counter() - inicio_frame
            espera_ms = max(1, int((tiempo_objetivo_frame - transcurrido) * 1000))

            if cv2.waitKey(espera_ms) & 0xFF == ord("q"):
                break

        self.desconectar_plc()
        cap.release()
        cv2.destroyAllWindows()


# ================================================================
# EJECUCIÓN
# ================================================================

if __name__ == "__main__":

    moringa_algoritmo = (
        MoringaAlgoritmo()
    )

    moringa_algoritmo.main()