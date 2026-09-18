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
