# MoringaCIP --- Development

## Objetivo

Desarrollar un sistema de visión artificial para detectar y seguir
moringa mientras una plataforma avanza por el cultivo. Las cuchillas
permanecen cerradas para desmalezar y se abren al aproximarse a una
moringa para protegerla.

## Estructura actual

``` text
MoringaCIP/
├── .gitignore
├── requirements.txt
├── logs/
│   ├── development.md
│   ├── dev_log.csv
│   └── roadmap.md
├── models/
│   └── best_moringa_1.pt
└── test/
    ├── plc/
    │   ├── moringa_algoritmo_plc.py
    │   └── prueba_plc.py
    └── vision/
        └── moringa_algoritmo.py
```

## Arquitectura actual

``` text
Cámara/video → YOLO → tracking → ID/posición → lado izquierdo/derecho
→ decisión ABRIR/CERRAR → Python + pycomm3 → CIP/EtherNet/IP
→ Allen-Bradley 1769-L18ER → Tags → Ladder → salidas digitales → cuchillas
```

## Algoritmo de visión

El frame actual es 1280×720. Se divide en región izquierda (x=0--640) y
derecha (x=640--1280). Cada moringa se sigue mediante `track_id`. Desde
el centro `(x,y)` se calculan `punto_abrir=(x,y-20)` y
`punto_cerrar=(x,y+20)`, usando actualmente una referencia horizontal en
`y=500`.

Semántica de control: - Cuchilla abierta: proteger moringa. - Cuchilla
cerrada: desmalezar. - Se registran IDs ya procesados para evitar
repetir aperturas/cierres. - Cada lado mantiene control y conteo
independiente.

## Evolución de comunicación

### Raspberry Pi 4

El prototipo inicial utilizó Modbus TCP/IP con `pymodbus` y coils.
`False` representaba apertura y `True` cierre.

### Allen-Bradley 1769-L18ER

El objetivo actual es usar CIP/EtherNet/IP mediante `pycomm3`. En lugar
de coils, Python escribirá Tags BOOL creados en Studio 5000. Nombres
provisionales:

``` text
Cuchilla_Izquierda
Cuchilla_Derecha
```

Los nombres finales deben coincidir exactamente con Studio 5000.

## Dos programas

### PC / Jetson

Responsable de captura, YOLO, tracking, selección de lado, decisión
abrir/cerrar y escritura de Tags. Archivos principales:
`test/vision/moringa_algoritmo.py`, `test/plc/prueba_plc.py` y
`test/plc/moringa_algoritmo_plc.py`.

### PLC

Se desarrolla en Studio 5000 y se ejecuta en el 1769-L18ER. Recibe Tags,
ejecuta Ladder y gobierna salidas físicas. Más adelante deberá
incorporar las condiciones de habilitación, enclavamientos y seguridad
que correspondan.

## Red Ethernet

PC y PLC deben tener IP distintas dentro de la misma subred. Ejemplo
conceptual:

``` text
PLC 192.168.1.10 / 255.255.255.0
PC  192.168.1.20 / 255.255.255.0
```

La IP real del PLC está pendiente de confirmación. Orden de prueba:
configurar IPv4 → `ping` → leer Tag → escribir True/False → observar en
Studio 5000 → vincular Ladder/salida.

## pycomm3

Prueba mínima prevista:

``` python
from pycomm3 import LogixDriver

PLC_IP = "IP_REAL_DEL_PLC"
TAG = "Prueba_Python"

with LogixDriver(PLC_IP) as plc:
    plc.write(TAG, True)
    print(plc.read(TAG))
    plc.write(TAG, False)
    print(plc.read(TAG))
```

## Refactor de integración

La capa `pymodbus + ModbusTcpClient + coils` se sustituye por
`pycomm3 + LogixDriver + Tags`, conservando la lógica de visión.
Inicialmente pueden mantenerse `encender_gpio()` y `apagar_gpio()` para
reducir cambios, pero se prevé renombrarlas a `cerrar_cuchilla()` y
`abrir_cuchilla()`.

## Pendientes inmediatos

1.  Confirmar IP del 1769-L18ER y nombres definitivos de Tags.
2.  Completar instalación/configuración de Studio 5000.
3.  Crear un Tag BOOL de prueba.
4.  Validar `ping`.
5.  Ejecutar `test/plc/prueba_plc.py`.
6.  Validar lectura/escritura en Studio 5000.
7.  Asociar Tags con Ladder y salidas.
8.  Ejecutar `moringa_algoritmo_plc.py`.
9.  Medir latencia de la cadena completa.

## Criterio inicial de validación

La integración quedará validada inicialmente cuando funcione:

``` text
YOLO → tracking → decisión → pycomm3 → Tag PLC → Ladder → salida digital
```

en ambos lados, respetando abrir para proteger y cerrar para desmalezar.

# MoringaCIP --- Development

**Corte: 22/09/2026**

## Avances desde el último corte

Se configuró y validó la comunicación Ethernet con el Allen-Bradley
1769-L18ER-BB1B. Durante las pruebas el PLC utilizó `192.168.1.10` y la
PC `192.168.1.55`. FactoryTalk Linx/Who Active detectó correctamente el
controlador.

Antes de modificar el controlador se realizó un **Upload** y se guardó
un respaldo del proyecto existente.

## Studio 5000 y Tags

Se creó el proyecto `TestPycomm3` y se definieron Controller Tags BOOL:

``` text
Prueba_Python
CMD_Cuchilla_Izquierda
CMD_Cuchilla_Derecha
```

El proyecto fue descargado al PLC y se verificó Online en `Rem Run`, con
`Controller OK`, `I/O OK` y sin Forces. Los tres Tags fueron escritos
exitosamente desde Python mediante `pycomm3`.

## Prueba con visión

`moringa_algoritmo_plc.py` ejecutó YOLO/tracking y logró escribir los
Tags del PLC. La ruta funcional quedó validada:

``` text
Video → YOLO/tracking → decisión → pycomm3 → Controller Tag
```

Se observaron latencias elevadas durante esta prueba.

PC utilizada:

``` text
CPU: Intel Core i5-7200U
RAM: 6 GB
GPU: Intel HD Graphics 620
SSD: Kingston SA400S37480G
Sistema: x64
```

## Ladder y salida digital

Se creó la rutina Ladder `TEST_PY_OUT`:

``` text
CMD_Cuchilla_Izquierda              Local:1:O.Data.0
---------] [------------------------------( )---------
          XIC                              OTE
```

`MainRoutine` ejecuta `TEST_PY_OUT` mediante `JSR`.

Después de descargar la configuración, un script Python escribió
`CMD_Cuchilla_Izquierda` y activó exitosamente `Local:1:O.Data.0`.

Por tanto quedó validada:

``` text
Python → pycomm3 → CMD_Cuchilla_Izquierda
       → JSR TEST_PY_OUT → XIC → OTE
       → Local:1:O.Data.0 → salida digital física
```

## Rendimiento: siguiente trabajo

La latencia todavía no debe atribuirse únicamente al hardware. El código
actual abre `LogixDriver` en cada escritura y espera la finalización de
threads antes de continuar.

Se medirán:

``` text
T_YOLO
T_PROCESAMIENTO
T_PLC
T_FRAME_TOTAL
FPS_REAL
```

Después se comparará la implementación actual con una conexión
persistente al PLC.

## Estado actual

La integración funcional **YOLO → decisión → Tag → Ladder → salida
digital** ya fue demostrada para el canal de prueba izquierdo. El
siguiente bloque es caracterizar y optimizar latencia antes de
implementar ambos canales de cuchilla para pruebas dinámicas.

# Actualización de rendimiento y latencia

**Corte: 23/09/2026**

## Instrumentación de rendimiento

Se instrumentó `test/plc/moringa_algoritmo_plc.py` para medir de forma
separada:

```text
T_YOLO
T_PROCESAMIENTO
T_PLC
T_FRAME
FPS
```

`T_YOLO` corresponde al tiempo de pared alrededor de `model.track()`.
`T_PROCESAMIENTO` incluye el procesamiento posterior, representación,
manejo de detecciones y ejecución/sincronización de threads, además de la
comunicación PLC cuando ocurre un evento. `T_FRAME` representa la sección
medida de procesamiento del frame y no incluye `cv2.imshow()` ni
`waitKey()`.

## Experimento 1 --- Baseline E-GPA-L_01

Equipo:

```text
CPU: Intel Core i5-7200U
RAM: 6 GB
GPU: Intel HD Graphics 620
SSD: Kingston SA400S37480G
```

La implementación utilizada abría y cerraba `LogixDriver` en cada
escritura.

```text
Frames analizados:       118
Escrituras PLC:           35

T_YOLO promedio:      291.79 ms
T_PROCESAMIENTO:      148.87 ms
T_PLC promedio:        77.29 ms
T_FRAME promedio:     443.88 ms
FPS promedio:           2.34
```

La prueba mostró dos costos principales: inferencia/tracking sobre el
hardware disponible y el establecimiento repetido de la conexión con el
PLC.

## Experimento 2 --- Conexión LogixDriver persistente

Se modificó la arquitectura para crear la conexión `LogixDriver` una sola
vez antes del ciclo de procesamiento, reutilizarla para todas las
escrituras y cerrarla al terminar.

En E-GPA-L_01 se obtuvo:

```text
Frames analizados:       136
Escrituras PLC:           45

T_YOLO promedio:      273.94 ms
T_PROCESAMIENTO:      133.91 ms
T_PLC promedio:         3.63 ms
T_FRAME promedio:     411.08 ms
FPS promedio:           2.50
```

El tiempo medio de comunicación medido alrededor de la escritura pasó de
77.29 ms a 3.63 ms, una reducción aproximada del 95.3 %. La conexión
persistente queda adoptada como implementación actual.

## Repetición del Experimento 2 --- E-PIM_15

Se clonó la rama de medición de latencias en otro equipo y se ejecutó la
misma prueba con el mismo algoritmo, modelo, video y conexión persistente.

Equipo:

```text
Nombre: E-PIM_15
CPU: Intel Core i5-12400F
RAM: 16 GB
GPU: NVIDIA T400 4 GB
SSD: PNY CS3030 1 TB
Sistema: x64
```

Resultados:

```text
Frames analizados:       188
Escrituras PLC:           64

T_YOLO promedio:       43.95 ms
T_PROCESAMIENTO:        7.12 ms
T_PLC promedio:         3.92 ms
T_FRAME promedio:      53.08 ms
FPS promedio:          18.91
```

Comparado con E-GPA-L_01 usando también conexión persistente, el tiempo
medio de frame fue aproximadamente 7.74 veces menor y el FPS medio
aproximadamente 7.56 veces mayor. La comunicación PLC permaneció en el
mismo orden de magnitud, por lo que la diferencia principal de
rendimiento se encuentra en el procesamiento de visión y procesamiento
local.

## Estado de salidas

`CMD_Cuchilla_Izquierda` está vinculado mediante Ladder a
`Local:1:O.Data.0` y su activación física ya fue validada. El Tag
`CMD_Cuchilla_Derecha` puede escribirse desde Python, pero su salida
física todavía no está implementada.

## Siguiente etapa --- Experimento 3

El siguiente objetivo es medir la latencia real de reacción extremo a
extremo. Se realizará por capas:

```text
3A: detección/decisión → plc.write() → readback
3B: evento de referencia → transición eléctrica de Local:1:O.Data.0
3C: detección → salida eléctrica → movimiento mecánico de la cuchilla
```

Después se relacionará la latencia total con la velocidad de avance y la
distancia cámara-cuchilla para determinar la anticipación necesaria de
apertura y cierre.

## Estado actual

La cadena funcional del canal izquierdo está demostrada y la conexión
persistente redujo de forma importante el costo de comunicación. E-PIM_15
queda como referencia actual de rendimiento para las pruebas de visión.
Antes de modificar nuevamente la arquitectura se caracterizará la
latencia extremo a extremo.

