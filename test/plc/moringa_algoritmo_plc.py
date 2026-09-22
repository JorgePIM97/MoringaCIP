from collections import defaultdict
import cv2
from ultralytics import YOLO
import threading
import pandas as pd
import os
from datetime import datetime

# Allen-Bradley / EtherNet-IP
from pycomm3 import LogixDriver


class MoringaAlgoritmo():

    def __init__(self):

        # ============================================================
        # VISIÓN
        # ============================================================

        self.modelo_path = (
            "C:/Users/E-GPA-L_01/Documents/"
            "MoringaCIP/models/best_moringa_1.pt"
        )

        self.video_path = (
            "C:/Users/E-GPA-L_01/Documents/"
            "VideosTestVision/moringa_1_video.mp4"
        )

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
        self.tag_izquierdo = "CMD_Cuchilla_Izquierda"
        self.tag_derecho = "CMD_Cuchilla_Derecha"

        # Lock adicional para proteger la comunicación con el PLC
        self.lock_plc = threading.Lock()


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

        try:

            # Evita que dos threads intenten comunicarse
            # simultáneamente con el PLC
            with self.lock_plc:

                with LogixDriver(self.plc_ip) as plc:

                    resultado = plc.write(tag, valor)

                    if resultado:
                        print(
                            f"[PLC] {tag} = {valor}"
                        )
                    else:
                        print(
                            f"[PLC] Error escribiendo {tag}"
                        )

        except Exception as error:

            print(
                f"[PLC] Error de comunicación: {error}"
            )


    # ================================================================
    # CONTROL CUCHILLAS
    # ================================================================

    def encender_gpio(self, tag_lado):

        """
        TRUE = cuchilla cerrada
        TRUE = desmalezar
        """

        self.escribir_tag(
            tag_lado,
            True
        )

        print(
            f"[PLC] Cuchilla CERRADA -> {tag_lado}"
        )


    def apagar_gpio(self, tag_lado):

        """
        FALSE = cuchilla abierta
        FALSE = proteger moringa
        """

        self.escribir_tag(
            tag_lado,
            False
        )

        print(
            f"[PLC] Cuchilla ABIERTA -> {tag_lado}"
        )


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

                # FALSE en el Tag
                self.apagar_gpio(
                    tag_lado
                )

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

                # TRUE en el Tag
                self.encender_gpio(
                    tag_lado
                )

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

        model = self.cargar_modelo(
            self.modelo_path
        )

        cap = self.cargar_video(
            self.video_path
        )


        while cap.isOpened():

            success, frame = cap.read()

            if not success:
                break


            result = model.track(
                frame,
                persist=True
            )[0]


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

                                self.tag_izquierdo
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


            cv2.imshow(
                "Moringa Algoritmo",
                annotated_frame
            )


            if (
                cv2.waitKey(1)
                & 0xFF
                ==
                ord("q")
            ):
                break


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