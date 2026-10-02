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

# Experimento 3A — Latencia de comando y readback del PLC

**Corte: 24/09/2026**

## Objetivo

El Experimento 3A se diseñó para medir cuánto tiempo transcurre desde que
Python ya tomó la decisión de cambiar el estado de la cuchilla izquierda
hasta que Python puede observar, mediante EtherNet/IP, que la imagen de
salida utilizada por la lógica Ladder tiene el mismo estado solicitado.

La ruta evaluada es:

```text
Decisión de abrir/cerrar ya tomada en Python
                │
                │ T0
                ▼
plc.write("CMD_Cuchilla_Izquierda", valor)
                │
                │ T1
                ▼
Controller Tag: CMD_Cuchilla_Izquierda
                │
                ▼
Lógica Ladder
XIC CMD_Cuchilla_Izquierda
                │
                ▼
OTE Local:1:O.Data.0
                │
                ▼
plc.read("Local:1:O.Data.0")
                │
                │ T2
                ▼
Python recibe el estado de readback
```

## Punto exacto de inicio y final de la medición

La medición `T_3A` **no inicia cuando la cámara captura la imagen ni
cuando YOLO comienza la inferencia**. Para esta prueba, el procesamiento
de visión y la decisión lógica ya ocurrieron.

El instante `T0` se registra inmediatamente antes de ejecutar:

```python
self.plc.write(tag, valor)
```

Por tanto, `T0` representa el momento en que Python ya decidió
ABRIR/CERRAR y está a punto de enviar el comando al PLC mediante
EtherNet/IP.

El instante `T1` se registra inmediatamente después de que termina
`plc.write()`. De esta forma:

```text
T_WRITE = T1 - T0
```

mide el tiempo de la operación de escritura observada desde Python.

Para el canal izquierdo, después de la escritura se ejecuta:

```python
self.plc.read("Local:1:O.Data.0")
```

El instante `T2` se registra cuando esa operación de lectura termina y
Python ya recibió el valor de `Local:1:O.Data.0`.

Por tanto:

```text
T_READBACK = T2 - T1
T_3A       = T2 - T0
```

`T_3A` comienza justo antes del envío del comando y termina cuando Python
ha recibido por EtherNet/IP el readback de `Local:1:O.Data.0`.

## Qué incluye T_3A

La medición contiene, desde la perspectiva del programa Python:

```text
escritura EtherNet/IP del comando
+ procesamiento/scan del PLC observable entre las transacciones
+ ejecución de la lógica que relaciona CMD_Cuchilla_Izquierda
  con Local:1:O.Data.0
+ transacción EtherNet/IP de lectura
+ recepción del readback en Python
```

El readback se realizó sobre `Local:1:O.Data.0`, no sobre el mismo
Controller Tag escrito, para observar el estado asociado a la salida
después de la lógica Ladder.

## Qué NO mide T_3A

`T_3A` no debe interpretarse como latencia física total de la máquina.

No mide directamente:

```text
latencia cámara → frame disponible
tiempo completo de YOLO/tracking previo a la decisión
transición eléctrica real en el borne físico del PLC
retardo del driver/relevador/actuador
tiempo mecánico de movimiento de la cuchilla
momento en que la cuchilla alcanza una posición segura
```

Aunque `Local:1:O.Data.0` representa la imagen de salida utilizada por el
controlador, leerla mediante CIP no demuestra por sí solo el instante
exacto en que el voltaje cambió físicamente en el borne.

## Validación previa

Antes de ejecutar la prueba se verificó manualmente desde Python que:

```text
CMD_Cuchilla_Izquierda = False
→ Local:1:O.Data.0 = False

CMD_Cuchilla_Izquierda = True
→ Local:1:O.Data.0 = True
```

Esto confirmó que Python podía utilizar `Local:1:O.Data.0` como readback
para el Experimento 3A.

## Resultados

El Experimento 3A se ejecutó en E-PIM_15 utilizando la conexión
`LogixDriver` persistente.

```text
Readbacks canal izquierdo: 26
CMD != OUT:                 0

T_WRITE
  promedio:                 3.50 ms
  mediana:                  3.53 ms
  P95:                      5.63 ms
  mínimo:                   1.43 ms
  máximo:                   6.01 ms

T_READBACK
  promedio:                 5.26 ms
  mediana:                  5.28 ms
  P95:                      5.56 ms
  mínimo:                   4.81 ms
  máximo:                   5.57 ms

T_3A
  promedio:                 8.97 ms
  mediana:                  8.99 ms
  P95:                     10.90 ms
  mínimo:                   6.24 ms
  máximo:                  11.16 ms
```

Los 26 readbacks coincidieron con el valor solicitado. Durante esta
corrida no se observó ningún caso `CMD != OUT`.

## Interpretación

El resultado permite caracterizar la ruta de software/comunicación y el
estado observable del controlador. La conexión EtherNet/IP persistente
continúa mostrando tiempos de escritura de pocos milisegundos y no es el
principal cuello de botella del procesamiento de visión.

El `plc.read()` fue agregado con propósito de instrumentación. No se
considera todavía un requisito para la versión de producción, ya que
añade una segunda transacción EtherNet/IP al evento.

## Próxima etapa

El siguiente paso será el **Experimento 3B**, cuyo objetivo es medir la
transición eléctrica real de la salida física del PLC con una referencia
de medición externa adecuada.

Después, el **Experimento 3C** medirá el movimiento mecánico de la
cuchilla hasta alcanzar la posición requerida. Con la latencia total,
velocidad de avance y distancia cámara-cuchilla será posible calcular la
anticipación de apertura/cierre necesaria en campo.

# Actualización de rendimiento — E-PIM-L_07 y selección explícita de CUDA

**Corte: 30/09/2026**

## PC oficial para pruebas en tractor

Se definió `E-PIM-L_07` como la plataforma oficial para las pruebas de
MoringaCIP montadas en el tractor.

```text
Nombre: E-PIM-L_07
CPU: Intel Core i9-12900H @ 2.50 GHz
RAM: 16 GB
GPU: NVIDIA GeForce RTX 3050 Ti Laptop GPU 4 GB
GPU integrada: Intel Iris Xe Graphics
Sistema: x64
```

La arquitectura de control no cambia:

```text
cámara / video
→ YOLO + tracking
→ decisión ABRIR / CERRAR
→ pycomm3 / EtherNet/IP
→ CMD_Cuchilla_Izquierda
→ Ladder TEST_PY_OUT
→ Local:1:O.Data.0
```

Para el experimento físico actual sólo el canal izquierdo está mapeado a
una salida física.

## Experimento 3A en E-PIM-L_07 — corridas 1 a 3

Se repitió el Experimento 3A en la nueva plataforma antes de fijar
explícitamente el dispositivo de inferencia de Ultralytics.

Resultado agrupado:

```text
Frames:                    535
T_YOLO promedio:         62.28 ms
T_PROCESAMIENTO:         12.00 ms
T_FRAME promedio:        76.76 ms
FPS promedio:            13.20
T_WRITE promedio:         4.85 ms
T_READBACK promedio:      5.21 ms
T_3A promedio:            9.96 ms
Readbacks izquierdos:       83
CMD != OUT:                  0
```

El camino de control PLC continuó estable, pero el procesamiento de visión
fue más lento que el observado previamente en E-PIM_15.

## Verificación de CUDA

Se comprobó desde el entorno de ejecución:

```text
CUDA disponible: True
GPU detectada: NVIDIA GeForce RTX 3050 Ti Laptop GPU
```

Para evitar depender de la selección automática del dispositivo, se realizó
un cambio controlado en la llamada de tracking:

```python
results = model.track(
    frame,
    persist=True,
    device=0
)[0]
```

`device=0` solicita explícitamente la GPU CUDA 0. No se modificó la lógica
de detección, tracking, decisión, comunicación PLC ni la instrumentación.

## Validación con `device=0` — corridas 4 a 6

Resultados:

```text
                         Corrida 4    Corrida 5    Corrida 6
Frames                         188          179          191
T_YOLO promedio             41.52 ms      41.63 ms      41.06 ms
T_PROCESAMIENTO              7.13 ms       8.47 ms       7.06 ms
T_FRAME promedio            50.16 ms      51.68 ms      49.65 ms
FPS promedio                20.05         19.48         20.26
T_WRITE promedio             4.58 ms       4.76 ms       4.59 ms
T_READBACK promedio          5.25 ms       5.29 ms       5.25 ms
T_3A promedio                9.80 ms       9.59 ms       9.71 ms
```

Las tres corridas reprodujeron el mismo régimen de rendimiento. En los
readbacks del canal izquierdo no se observaron discrepancias entre el
comando y `Local:1:O.Data.0`.

## Baseline oficial de cómputo

Las corridas 4 a 6 acumulan 558 frames. Para documentación y siguientes
pruebas se adopta como referencia aproximada:

```text
E-PIM-L_07 + RTX 3050 Ti + device=0

T_YOLO:              ~41.4 ms
T_FRAME:             ~50.5 ms
FPS:                 ~19.9
T_3A:                 ~9.7 ms
Inferencia Ultralytics: ~18-19 ms típicos
```

Respecto al conjunto de corridas 1 a 3, la selección explícita de
`device=0` produjo en este experimento una reducción aproximada de 33.5 %
en `T_YOLO` y un aumento aproximado de 51 % en FPS.

Las corridas 1 a 3 se conservan como historial experimental. No se
interpretan como prueba de que toda la inferencia anterior ocurriera en
CPU; demuestran que, en esta plataforma y configuración, hacer explícito
el dispositivo CUDA produjo un rendimiento sustancialmente mejor y
repetible.

## Alcance de T_3A

El nuevo baseline no modifica la interpretación de 3A:

```text
T0: decisión ya tomada, inmediatamente antes de plc.write()
T1: final de plc.write()
T2: final de plc.read(Local:1:O.Data.0)

T_WRITE    = T1 - T0
T_READBACK = T2 - T1
T_3A       = T2 - T0
```

`T_3A ≈ 9.7 ms` es una medición observable desde Python del camino de
control hasta el readback. No representa la transición eléctrica exacta
del borne ni el tiempo mecánico de apertura/cierre de la cuchilla.

## Siguiente etapa

Se mantiene la secuencia:

```text
3B → medir transición eléctrica real de Local:1:O.Data.0
3C → medir tiempo mecánico real de apertura y cierre
```

Después se integrarán cámara/adquisición, visión, decisión, PLC, salida
eléctrica y actuador para estimar la latencia física total. Con la
velocidad de avance y la geometría cámara-cuchilla se podrá calcular la
anticipación requerida para `D_OPEN` y `D_CLOSE`.

# Actualización 2026-10-01 a 2026-10-02 — Electroválvula bidireccional y validación física

## Cambio de arquitectura de mando de la cuchilla izquierda

La etapa de actuación dejó de representarse mediante una sola orden BOOL. La
electroválvula del actuador izquierdo dispone de dos órdenes/direcciones de
24 V mutuamente excluyentes:

```text
AVANCE     -> cerrar cuchillas -> desmalezar
RETROCESO  -> abrir cuchillas  -> proteger moringa
```

Controller Tags utilizados:

```text
CMD_ON_Cuchilla_Izquierda   -> AVANCE
CMD_OFF_Cuchilla_Izquierda  -> RETROCESO
```

Mapeo físico validado en Ladder:

```text
CMD_ON_Cuchilla_Izquierda   -> Local:1:O.Data.1
CMD_OFF_Cuchilla_Izquierda  -> Local:1:O.Data.0
```

Tabla funcional:

```text
CERRAR / DESMALEZAR : AVANCE=1, RETROCESO=0
ABRIR / PROTEGER    : AVANCE=0, RETROCESO=1
NEUTRO               : AVANCE=0, RETROCESO=0
PROHIBIDO            : AVANCE=1, RETROCESO=1
```

Python escribe ambas consignas en una misma llamada `plc.write()` y rechaza
por software la combinación `1/1`. La exclusión también debe conservarse en
la lógica Ladder; la escritura conjunta desde Python no se considera un
interlock de seguridad.

El canal derecho del frame se mantiene visible para tracking/HUD, pero sus
órdenes PLC fueron deshabilitadas para las pruebas actuales. El experimento
físico se concentra únicamente en el surco izquierdo.

## Repetición formal 3A — E-PIM_15

Se repitió 3A con la nueva lógica de dos órdenes antes de la prueba con
electroválvulas. Se registraron 36 actuaciones válidas:

```text
18 aperturas
18 cierres
```

Resultados:

```text
APERTURA / PROTEGER
T_WRITE promedio: 3.790 ms
T_3A promedio:    8.972 ms
T_3A mínimo:      6.648 ms
T_3A máximo:     11.784 ms

CIERRE / DESMALEZAR
T_WRITE promedio: 3.765 ms
T_3A promedio:    8.919 ms
T_3A mínimo:      6.174 ms
T_3A máximo:     11.004 ms
```

No se observaron estados `AVANCE=1 / RETROCESO=1` en las actuaciones
registradas.

## 3A con E-PIM-L_07 y electroválvulas conectadas — video original

Se conectaron físicamente las electroválvulas y los pistones. Se verificó
visualmente que:

```text
RETROCESO -> apertura/protección
AVANCE    -> cierre/desmalezado
```

Los pistones respondieron en ambas direcciones respetando la lógica de
mando. La velocidad del video original hacía muy corta la ventana entre el
evento de apertura y el evento de cierre, por lo que el retroceso era
perceptible pero el pistón tenía poco tiempo para recorrer su carrera.

Resultados del log con video original:

```text
Frames medidos: 208
Actuaciones 3A: 31
Aperturas:       15
Cierres:         16

APERTURA
T_WRITE promedio:    5.842 ms
T_READBACK promedio: 5.178 ms
T_3A promedio:      11.020 ms
Mediana T_3A:       11.255 ms
Máximo T_3A:        12.810 ms

CIERRE
T_WRITE promedio:    4.528 ms
T_READBACK promedio: 5.451 ms
T_3A promedio:       9.980 ms
Mediana T_3A:        9.668 ms
Máximo T_3A:        12.837 ms

Visión global:
T_YOLO promedio:  61.99 ms
T_FRAME promedio: 76.39 ms
FPS promedio:     13.23
```

Las consignas observadas respetaron `0/1` para apertura y `1/0` para cierre.

## Prueba funcional con video ralentizado x15

Para observar mejor la carrera física de los pistones se creó
`modificacion_video.py`. El script conserva todos los frames y reduce el FPS
del archivo a `fps_original / 15`, por lo que la secuencia dura 15 veces más
sin eliminar frames.

Esta prueba se considera una validación funcional/electromecánica y no una
representación de la velocidad real del tractor.

En el log x15 se registraron 38 actuaciones:

```text
19 aperturas
19 cierres

APERTURA
T_3A promedio: 17.585 ms
Mediana T_3A:  11.393 ms
Máximo T_3A:  137.309 ms

CIERRE
T_3A promedio: 18.887 ms
Mediana T_3A:  11.377 ms
Máximo T_3A:  138.700 ms
```

La diferencia entre media y mediana se debe a outliers importantes. La
latencia típica continúa alrededor de 10-12 ms. No se atribuye el aumento de
la media al video ralentizado sin evidencia adicional.

La prueba x15 permitió observar con claridad el cambio físico
desmalezado -> apertura/protección -> cierre/desmalezado.

## Observación neumática

Durante la prueba los pistones presentaron movimiento lento. Se sospecha una
condición relacionada con la presión/ajuste neumático, pero la causa debe ser
diagnosticada por el equipo de neumática. Esta observación se registra como
condición del ensayo y no se atribuye al algoritmo.

## Interpretación actual de 3A, 3B y 3C

La validación con electroválvulas confirma funcionalmente la cadena de mando,
pero no convierte 3A en una medición física completa.

```text
3A -> escritura/readback CIP y validación funcional del mando
3B -> transición eléctrica real de las salidas de 24 V
3C -> tiempo mecánico/neumático hasta posición segura de cuchilla
```

El tiempo mecánico observado puede ser mucho mayor que T_3A y será necesario
medirlo antes de calcular definitivamente `D_OPEN` y `D_CLOSE`.

## Estado al 2026-10-02

- Lógica bidireccional AVANCE/RETROCESO validada.
- Electroválvulas conectadas y accionadas correctamente.
- Pistones observados en avance y retroceso.
- Canal derecho sin escritura PLC.
- 3A repetido en E-PIM_15.
- 3A ejecutado en E-PIM-L_07 con electroválvulas.
- Prueba x15 utilizada únicamente para observación funcional.
- Próximo experimento: 3B, seguido de 3C.

