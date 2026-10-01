from pathlib import Path

import cv2

# ---------- Configuración ----------
VIDEO_ENTRADA = Path(r"C:\Users\E-PIM-L_07\Documents\JorgeProyectos\utils\videos\moringa_1_video.mp4")
FACTOR_LENTITUD = 15.0   # 2.0 = el video dura el doble; 3.0 = el triple, etc.
# -----------------------------------


def alargar_video(entrada: Path, factor: float) -> Path:
    if factor <= 1:
        raise ValueError("FACTOR_LENTITUD debe ser mayor a 1 para alargar el video.")
    if not entrada.is_file():
        raise FileNotFoundError(f"No existe el video: {entrada}")

    salida = entrada.with_name(f"{entrada.stem}_x{factor:g}{entrada.suffix}")

    cap = cv2.VideoCapture(str(entrada))
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir el video: {entrada}")

    try:
        ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps_original = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps_original <= 0:
            raise RuntimeError("No se pudo leer el FPS del video original.")

        # Mismos frames, menor FPS => más duración, cero frames perdidos
        fps_nuevo = fps_original / factor

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(salida), fourcc, fps_nuevo, (ancho, alto))
        if not out.isOpened():
            raise RuntimeError("No se pudo crear el archivo de salida (codec no disponible).")

        escritos = 0
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                out.write(frame)  # se escribe TODOS los frames
                escritos += 1
        finally:
            out.release()

        print(f"Frames leídos/escritos: {escritos} de {total_frames}")
        print(f"FPS: {fps_original:.2f} -> {fps_nuevo:.2f}")
        if total_frames > 0 and fps_original > 0:
            print(f"Duración: {total_frames / fps_original:.1f}s -> {escritos / fps_nuevo:.1f}s")
        print(f"Guardado en: {salida}")
        return salida
    finally:
        cap.release()


if __name__ == "__main__":
    alargar_video(VIDEO_ENTRADA, FACTOR_LENTITUD)