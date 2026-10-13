"""Conversión y presentación de imágenes en los labels de Qt."""
import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap


def mostrar_frame(frame_bgr, label):
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w, _ = frame_rgb.shape
    imagen = QImage(
        frame_rgb.data, w, h, frame_rgb.strides[0],
        QImage.Format.Format_RGB888,
    ).copy()
    label.setPixmap(QPixmap.fromImage(imagen).scaled(
        label.width(), label.height(), Qt.AspectRatioMode.KeepAspectRatio,
    ))
