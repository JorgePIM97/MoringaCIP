import subprocess
import sys

ui_file = "C:/Users/E-PIM_15/OneDrive - GRUPO PLASMA AUTOMATION S.A. DE C.V/Documentos/ProyectosCIEM/MoringaCIP/app/vista/ui/plantillas/moringa.ui"
py_file = "C:/Users/E-PIM_15/OneDrive - GRUPO PLASMA AUTOMATION S.A. DE C.V/Documentos/ProyectosCIEM/MoringaCIP/app/vista/ui/plantillas/moringa.py"

subprocess.run([
    sys.executable, "-m", "PyQt6.uic.pyuic",
    "-x", ui_file,
    "-o", py_file
], check=True)

print("Conversión completada:", py_file)