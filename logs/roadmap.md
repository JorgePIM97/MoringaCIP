# MoringaCIP --- Roadmap

## Fase 1 --- Visión artificial base

**Estado: prototipo completado.** Modelo YOLO disponible, tracking
persistente, frame 1280×720, regiones izquierda/derecha, referencia
y=500, puntos de apertura/cierre y control por `track_id`.

## Fase 2 --- Raspberry Pi + Modbus TCP/IP

**Estado: completada como referencia.** Se validó la arquitectura con
`pymodbus`: `False` abre/protege y `True` cierra/desmaleza. Esta fase
queda como antecedente.

## Fase 3 --- Migración a Allen-Bradley

**Estado: en progreso.** Controlador objetivo: Allen-Bradley 1769-L18ER.
Protocolo: CIP/EtherNet/IP. Cliente Python: `pycomm3`/`LogixDriver`.
Aprendizaje necesario: Studio 5000, red Ethernet, Tags y Ladder básico.

## Fase 4 --- Comunicación PC ↔ PLC

**Estado: preparada para pruebas.** Usar `test/plc/prueba_plc.py`.
Secuencia: confirmar IP → configurar IPv4 → ping → conectar LogixDriver
→ leer Tag → escribir True/False → comprobar en Studio 5000.
**Criterio:** lectura/escritura confiable de Tags desde Python.

## Fase 5 --- Tags → Ladder → salidas

**Estado: pendiente.** Crear comandos izquierdo/derecho, mapearlos a
Ladder, validar ON/OFF e identificar salidas físicas. **Criterio:** una
escritura desde Python produce el estado esperado en la salida del PLC.

## Fase 6 --- Visión + PLC

**Estado: código inicial preparado.** Archivo
`test/plc/moringa_algoritmo_plc.py`. Pruebas: izquierda, derecha,
apertura/cierre único por ID, múltiples detecciones, pérdida de
detección y pérdida/recuperación de comunicación.

## Fase 7 --- Optimización

**Estado: pendiente.** Evaluar conexión persistente con `LogixDriver`,
evitar escrituras redundantes, medir latencia, manejar timeouts y
registrar errores.

## Fase 8 --- Seguridad y control industrial

**Estado: pendiente.** Antes de cuchillas reales: definir estado seguro
ante pérdida de comunicación, separar comando de visión de salida
física, habilitación, modo manual/automático si aplica y enclavamientos
definidos con automatización.

## Fase 9 --- Pruebas dinámicas

**Estado: pendiente.** Caracterizar FPS, inferencia, comunicación, scan
del PLC, actuador, velocidad de avance y distancia cámara-cuchilla. Con
esos datos ajustar la anticipación real de apertura/cierre.

## Próximo hito

**Realizar la primera escritura real de un Tag del 1769-L18ER desde
`test/plc/prueba_plc.py` y observar el cambio en Studio 5000.** Después,
vincularlo con una salida física y ejecutar la integración de visión.

# MoringaCIP --- Roadmap

**Corte: 22/09/2026**

## Completado

-   Visión YOLO + tracking y lógica izquierda/derecha.
-   Migración de Modbus a `pycomm3` / CIP/EtherNet/IP.
-   Red PC ↔ Allen-Bradley 1769-L18ER-BB1B.
-   Respaldo mediante Upload del proyecto previo.
-   Proyecto `TestPycomm3`.
-   Tags `Prueba_Python`, `CMD_Cuchilla_Izquierda` y
    `CMD_Cuchilla_Derecha`.
-   Escritura exitosa de los tres Tags desde Python.
-   Escritura de Tags desde el algoritmo de visión.
-   Rutina `TEST_PY_OUT` llamada mediante JSR.
-   `CMD_Cuchilla_Izquierda` → `Local:1:O.Data.0`.
-   Activación física exitosa de la salida local desde Python.

## Siguiente fase --- Rendimiento

Medir por separado: - tiempo de `model.track()`; - procesamiento
posterior; - `plc.write()`; - tiempo total por frame; - FPS reales.

Después: - mantener una conexión `LogixDriver` persistente; - evitar
escrituras redundantes; - revisar threads y `join()`; - comparar
latencias antes/después.

## Fase posterior --- Dos cuchillas

-   Definir salida física del canal derecho.
-   Crear Ladder para `CMD_Cuchilla_Derecha`.
-   Verificar ambos canales independientemente.
-   Mantener Tags de comando separados de las salidas físicas.

## Antes de pruebas reales

Definir con automatización estado seguro ante pérdida de comunicación,
habilitación general, interlocks y comportamiento manual/automático que
corresponda.

## Pruebas dinámicas

Caracterizar FPS, latencia PC→PLC, tiempo del PLC/actuador, velocidad de
avance y distancia cámara-cuchilla para calibrar anticipación de
apertura/cierre.

## Próximo hito

Obtener una línea base de `moringa_algoritmo_plc.py` con `T_YOLO`,
`T_PLC`, tiempo total por frame y FPS; después implementar conexión
persistente y comparar.

# Actualización del Roadmap

**Corte: 23/09/2026**

## Fase 3 --- Migración a Allen-Bradley

**Estado: completada para la integración actual.** Se adoptó el
Allen-Bradley 1769-L18ER-BB1B con CIP/EtherNet/IP y `pycomm3`.

## Fase 4 --- Comunicación PC ↔ PLC

**Estado: completada.** Se validaron red, `ping`, conexión mediante
`LogixDriver` y escritura de Controller Tags desde Python.

## Fase 5 --- Tags → Ladder → salidas

**Estado: parcialmente completada.** El canal izquierdo está validado:

```text
CMD_Cuchilla_Izquierda
→ TEST_PY_OUT
→ Local:1:O.Data.0
→ salida digital física
```

El canal derecho conserva su Tag de comando, pero falta definir y validar
su salida física.

## Fase 6 --- Visión + PLC

**Estado: integración funcional validada.** YOLO/tracking genera
decisiones de apertura/cierre y Python escribe los Tags mediante
EtherNet/IP.

## Fase 7 --- Optimización

**Estado: en progreso con hito principal completado.**

Completado:

- Instrumentación de `T_YOLO`, `T_PROCESAMIENTO`, `T_PLC`, `T_FRAME` y FPS.
- Baseline en E-GPA-L_01.
- Implementación de conexión `LogixDriver` persistente.
- Reducción de `T_PLC` promedio de 77.29 ms a 3.63 ms en E-GPA-L_01.
- Repetición del Experimento 2 en E-PIM_15.
- En E-PIM_15: `T_FRAME` promedio 53.08 ms y 18.91 FPS.

Pendiente después de caracterizar la latencia extremo a extremo:

- Evaluar escrituras redundantes.
- Revisar arquitectura de threads y `join()`.
- Manejar reconexión/timeouts de forma robusta.
- Evaluar optimizaciones adicionales de inferencia solo si son necesarias.

## Fase 8 --- Seguridad y control industrial

**Estado: pendiente.** Antes de operar cuchillas reales se deben definir
estado seguro ante pérdida de comunicación, habilitación, interlocks,
modo manual/automático y responsabilidades entre visión y PLC.

## Fase 9 --- Latencia extremo a extremo y pruebas dinámicas

**Estado: siguiente fase.**

Experimento 3:

```text
3A  detección/decisión → escritura PLC → readback
3B  evento de referencia → transición eléctrica de salida
3C  detección → salida eléctrica → movimiento mecánico
```

Después se medirán velocidad de avance y distancia cámara-cuchilla para
calcular la anticipación necesaria.

## Referencia actual de rendimiento

```text
E-PIM_15
Intel Core i5-12400F
NVIDIA T400 4 GB
16 GB RAM

T_YOLO promedio:       43.95 ms
T_PROCESAMIENTO:        7.12 ms
T_PLC promedio:         3.92 ms
T_FRAME promedio:      53.08 ms
FPS promedio:          18.91
```

## Próximo hito

Ejecutar el **Experimento 3A** sin modificar todavía la lógica de
detección: instrumentar detección/decisión, `plc.write()` y readback para
comenzar a caracterizar la latencia de reacción extremo a extremo.

# Actualización del Roadmap — Cierre Experimento 3A

**Corte: 24/09/2026**

## Fase 9 — Latencia extremo a extremo y pruebas dinámicas

**Estado: en progreso.**

### Experimento 3A — Comando → readback del PLC

**Estado: completado.**

Alcance exacto:

```text
INICIO:
Python ya tomó la decisión de abrir/cerrar.
T0 se registra inmediatamente antes de plc.write().

        ↓

plc.write("CMD_Cuchilla_Izquierda", valor)

        ↓

Lógica Ladder:
CMD_Cuchilla_Izquierda
→ XIC
→ OTE Local:1:O.Data.0

        ↓

plc.read("Local:1:O.Data.0")

        ↓

FINAL:
T2 se registra cuando Python termina de recibir el readback.
```

Métricas:

```text
T_WRITE    = T1 - T0
T_READBACK = T2 - T1
T_3A       = T2 - T0
```

Resultado actual en E-PIM_15:

```text
Readbacks:              26
Coincidencias CMD/OUT:  26
CMD != OUT:              0

T_WRITE promedio:        3.50 ms
T_READBACK promedio:     5.26 ms
T_3A promedio:           8.97 ms
T_3A mediana:            8.99 ms
T_3A P95:               10.90 ms
T_3A mínimo:             6.24 ms
T_3A máximo:            11.16 ms
```

**Límite de la medición:** `T_3A` no incluye cámara/YOLO antes de la
decisión y tampoco demuestra el instante de transición eléctrica del
borne ni el movimiento mecánico de la cuchilla.

### Experimento 3B — Salida eléctrica física

**Estado: siguiente hito.**

Objetivo: medir con una referencia externa el tiempo hasta la transición
eléctrica real de la salida física asociada a `Local:1:O.Data.0`.

La prueba deberá distinguir el estado observable por CIP de la transición
eléctrica del borne.

### Experimento 3C — Movimiento mecánico

**Estado: pendiente.**

Objetivo: medir desde el evento de control hasta que la cuchilla alcance
físicamente la posición requerida de apertura/cierre.

### Calibración dinámica

**Estado: pendiente después de 3B y 3C.**

Con la latencia total medida se relacionarán:

```text
latencia total
velocidad de avance
distancia cámara-cuchilla
```

para calcular la anticipación necesaria mediante:

```text
distancia de anticipación = velocidad × latencia
```

## Próximo hito

Preparar y ejecutar el **Experimento 3B** sin confundir el readback de
`Local:1:O.Data.0` con una medición eléctrica del borne físico.

