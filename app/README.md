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
Para apagar, ordena retroceso, espera los dos sensores BOOL de retroceso
(máximo 10 segundos) y después desactiva ambos mandos. Un timeout mantiene
la consigna de retroceso e informa el fallo. No se envían órdenes adicionales
al salir de la pantalla.

### Medición temporal para pruebas de pistones

Los botones Avanzar, Retroceder y Apagar usan `PLCTest(..., medir=True)`.
Se conserva el mando común izquierdo para ambos pistones y se leen:

| Movimiento | Pistón 1 | Pistón 2 |
| --- | --- | --- |
| Avance | `tag_piston_1_avance` | `tag_piston_2_avance` |
| Retroceso | `tag_piston_1_retroceso` | `tag_piston_2_retroceso` |

Los cuatro tags deben ser BOOL, con `True` al alcanzar el extremo.
Cada orden agrega dos filas a `logs/pruebas_tiempos_pistones.csv`, creado
automáticamente, sin sobrescribir las pruebas anteriores. Incluye un ID
común de operación, fecha con zona horaria, IP, acción, movimiento, pistón,
sensor, estado inicial, tiempo en milisegundos y estado del resultado.
El tiempo empieza justo antes de enviar la escritura que activa el sentido
y termina al recibir la lectura del sensor activo. Cada pistón se mide
independientemente con reloj monotónico de alta resolución.

Se consulta cada 10 ms más el tiempo de comunicación; la medida incluye
escritura, procesamiento del PLC y lectura por red. No equivale a una
medición tomada dentro del PLC ni garantiza resolución de 10 ms.
`timeout` e `intervalo` pueden ajustarse en el constructor de `PLCTest`.
Los tiempos completados aparecen también al colocar el cursor sobre el
indicador Conectado.

Si el sensor ya estaba activo antes de la orden, se registra
`sensor_ya_activo` sin tiempo: para medir un recorrido completo primero
llevar los pistones al extremo opuesto. `timeout` y `error` tampoco llevan
tiempo de recorrido; los resultados de pistones que sí terminaron se conservan.
La ventana espera a que termine la prueba antes de permitir otra orden.
La prueba de comunicación no mueve los pistones ni genera mediciones.
Esta instrumentación corresponde a pruebas manuales; no modifica el ciclo de IA.

Ingresar la IPv4 en `IngresarIP_lineEdit` y pulsar Guardar IP, conectado
desde Designer al slot `saveIP()`. La configuración se guarda en
`app/plc.json` con la clave `plc_ip` y se recupera al abrir la ventana.
Sin una IP guardada no se inicia IA. `VisionSession` pasa la IP guardada
a `IAThread`; no existe una IP de respaldo hardcodeada. Los cambios se
aplican al próximo inicio de IA y no alteran una conexión activa.
