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
