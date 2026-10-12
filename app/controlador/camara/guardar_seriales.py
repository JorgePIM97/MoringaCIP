import json
import os


def guardar_seriales_realsense(serial_camara_izquierda, serial_camara_derecha):
    ruta = r"C:\MoringaQT\controlador\camara"
    archivo = os.path.join(ruta, "seriales_realsense.json")

    data = {
        "camara_izquierda": serial_camara_izquierda,
        "camara_derecha": serial_camara_derecha
    }

    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"JSON guardado correctamente en: {archivo}")