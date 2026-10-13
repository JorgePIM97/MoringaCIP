# Organización de la aplicación

Ejecutar desde la raíz del proyecto con `python app/main.py`.

| Archivo | Responsabilidad |
| --- | --- |
| `main.py` | Construir la ventana, conservar los slots de Designer y delegar acciones. |
| `controlador/navegation/screen_navegation.py` | Cambiar páginas del QStackedWidget de la ventana existente. |
| `controlador/vision_session.py` | Crear, conectar y detener los hilos de cámara e IA. |
| `controlador/configuracion/serial_repository.py` | Leer y guardar el serial en JSON, sin dependencias de Qt. |
| `controlador/configuracion/plc_repository.py` | Validar y guardar la dirección IPv4 del PLC. |
| `vista/frame_presenter.py` | Convertir frames BGR a imágenes Qt y presentarlos en labels. |
| `controlador/threads/camara_thread.py` | Capturar y entregar frames de RealSense. |
| `controlador/camara/realsense_depth.py` | Acceder al SDK de RealSense. |
| `controlador/threads/ia_thread.py` | Ejecutar tracking, decisiones y comunicación PLC en el hilo de IA. |

## Trabajo con Qt Designer

Editar `vista/ui/plantillas/moringa.ui` y regenerar su archivo Python con
el conversor existente. Mantener los nombres de los slots conectados en
Designer: `showConfigurar`, `showConfigurarCamaras`, `confirmarDatos`,
`iniciarIA`, `detenerIA`, `guardarSeriales`, `testCamarasOn` y `testCamarasOff`.
Sus implementaciones permanecen en `MoringaMain`; los archivos generados
no necesitan modificaciones manuales para esta organización.

`ScreenNavegation` recibe `self.stackedWidget` después de `setupUi(self)`.
Las páginas iniciales 0, 1 y 2 corresponden a configuración de trabajo,
visión y configuración de cámara. Si se cambian estas páginas en Designer,
actualizar ese mapeo en el navegador. No crear otra instancia de la UI para
navegar: debe utilizarse el widget visible de la ventana.

`VisionSession` es propietario de los hilos. Al detener la cámara también
detiene IA; al cambiar de vista de cámara cambia el slot receptor sin abrir
otra captura. El cierre de conexión PLC sigue gestionado por `IAThread`.

La modularización conserva 848×480 px, umbral y=240, `device=0`, mando
bidireccional izquierdo y canal derecho sin escrituras. Parar la sesión
no envía una consigna adicional al actuador.

Pruebas sin hardware: `python -m unittest discover -s test -p "test_*.py" -v`.

## Dirección IP del PLC

Las pruebas manuales usan la IP del campo de configuración y se ejecutan
en `PLCTestThread`, sin bloquear la ventana. No pueden ejecutarse mientras
la IA está activa. La prueba de comunicación lee los dos tags de mando sin
escribir; los indicadores muestran consignas, no posiciones físicas.

`PLCTest` desactiva el sentido opuesto antes de activar avance o retroceso.
Para apagar, ordena retroceso, espera el sensor BOOL (máximo 10 segundos) y
después desactiva ambos mandos. Configurar `tag_fin_retroceso` y
`valor_fin_retroceso` en `MoringaMain` con el tag real y su polaridad.
Mientras falte ese dato, el botón Apagar informa que falta configuración
y no envía órdenes. Un timeout mantiene la consigna de retroceso e informa
el fallo. No se envían órdenes adicionales al salir de la pantalla.

Ingresar la IPv4 en `IngresarIP_lineEdit` y pulsar Guardar IP, conectado
desde Designer al slot `saveIP()`. La configuración se guarda en
`app/plc.json` con la clave `plc_ip` y se recupera al abrir la ventana.
Sin una IP guardada no se inicia IA. `VisionSession` pasa la IP guardada
a `IAThread`; no existe una IP de respaldo hardcodeada. Los cambios se
aplican al próximo inicio de IA y no alteran una conexión activa.
