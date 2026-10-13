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

# Actualización del Roadmap — Baseline GPU E-PIM-L_07

**Corte: 30/09/2026**

## Fase 7 — Optimización

**Estado: baseline de cómputo actualizado.**

Completado adicionalmente:

- Se definió `E-PIM-L_07` como PC oficial para las pruebas en tractor.
- Se verificó disponibilidad de CUDA y detección de la RTX 3050 Ti.
- Se fijó `device=0` en `model.track()` para solicitar explícitamente CUDA GPU 0.
- Se validó el cambio mediante tres corridas independientes.
- Las corridas 4 a 6 acumulan 558 frames y mantienen aproximadamente
  `T_YOLO ≈ 41.4 ms`, `T_FRAME ≈ 50.5 ms` y `FPS ≈ 19.9`.
- `T_3A` permanece alrededor de `9.7 ms`, por lo que el cambio de
  rendimiento se concentra en visión y no altera de forma importante el
  camino EtherNet/IP/readback.

Configuración que se conserva:

```python
results = model.track(
    frame,
    persist=True,
    device=0
)[0]
```

Pendiente de optimización, sólo después de las mediciones físicas:

- Evaluar escrituras redundantes.
- Revisar arquitectura de threads y `join()`.
- Implementar reconexión/timeouts robustos.
- Evaluar optimizaciones adicionales de inferencia únicamente si las
  pruebas reales lo requieren.

## Fase 9 — Latencia extremo a extremo y pruebas dinámicas

**Estado: Experimento 3A completado y baseline oficial actualizado.**

Referencia actual:

```text
PC: E-PIM-L_07
CPU: Intel Core i9-12900H
GPU: NVIDIA GeForce RTX 3050 Ti Laptop GPU 4 GB
RAM: 16 GB
YOLO device: 0

T_YOLO:  ~41.4 ms
T_FRAME: ~50.5 ms
FPS:     ~19.9
T_3A:    ~9.7 ms
```

### Experimento 3B — Salida eléctrica física

**Estado: siguiente hito.**

Medir con una referencia externa la transición eléctrica real de la
salida física asociada a `Local:1:O.Data.0`. La prueba debe distinguir
el readback por CIP de la transición real del borne.

### Experimento 3C — Movimiento mecánico

**Estado: pendiente después de 3B.**

Medir el tiempo desde el evento de control hasta que la cuchilla alcanza
una posición mecánicamente segura, separando apertura y cierre.

### Calibración física `D_OPEN` / `D_CLOSE`

**Estado: pendiente después de 3B y 3C.**

Integrar:

```text
latencia de adquisición / visión
latencia de decisión y control
latencia eléctrica
latencia mecánica
velocidad de avance
distancia cámara-cuchilla
margen de seguridad
```

para determinar la anticipación física de apertura y el cierre seguro.

## Próximo hito

Preparar y ejecutar el **Experimento 3B**. No utilizar `T_3A` como si
fuera la latencia física total de la cuchilla; `T_3A` termina en el
readback de `Local:1:O.Data.0`.

# Actualización 2026-10-02 — Ruta después de validación con electroválvulas

## Fase 9A — Mando bidireccional de la cuchilla izquierda

**Estado: completado.**

- [x] Crear/usar `CMD_ON_Cuchilla_Izquierda` para AVANCE.
- [x] Crear/usar `CMD_OFF_Cuchilla_Izquierda` para RETROCESO.
- [x] Vincular AVANCE a `Local:1:O.Data.1`.
- [x] Vincular RETROCESO a `Local:1:O.Data.0`.
- [x] Validar cierre/desmalezado con estado `1/0`.
- [x] Validar apertura/protección con estado `0/1`.
- [x] Impedir por software el estado `1/1`.
- [x] Deshabilitar escritura PLC del lado derecho durante el experimento.

## Fase 9B — Repetición formal del Experimento 3A

**Estado: completado.**

- [x] Repetir 3A en E-PIM_15 con la lógica bidireccional.
- [x] Ejecutar 3A en E-PIM-L_07 con electroválvulas conectadas.
- [x] Confirmar actuación física de AVANCE y RETROCESO.
- [x] Registrar por separado apertura y cierre.
- [x] Ejecutar prueba x15 para observación funcional de la carrera del pistón.

La prueba x15 no debe utilizarse para inferir la ventana temporal real del
tractor ni para calibrar directamente `D_OPEN`/`D_CLOSE`.

## Experimento 3B — Salida eléctrica física de 24 V

**Estado: siguiente hito.**

Objetivo: medir con instrumentación externa el intervalo entre el evento de
control y la transición eléctrica real de las dos órdenes físicas:

```text
AVANCE     -> Local:1:O.Data.1
RETROCESO  -> Local:1:O.Data.0
```

Requisitos del ensayo:

- medir AVANCE y RETROCESO por separado;
- distinguir flanco de activación y desactivación;
- verificar que no exista solapamiento eléctrico `1/1`;
- no confundir readback CIP con transición real del borne;
- utilizar adaptación eléctrica adecuada para señales de 24 V.

## Experimento 3C — Movimiento neumático/mecánico

**Estado: pendiente después de 3B.**

Objetivo: medir el tiempo real hasta alcanzar una posición segura de
apertura y de cierre.

Se deben separar como mínimo:

```text
T_open_mech
T_close_mech
```

La presión y regulación neumática deberán estar en una condición conocida y
repetible antes de formalizar estas mediciones.

## Fase posterior — D_OPEN / D_CLOSE

Con 3B y 3C medidos, integrar:

```text
adquisición de frame
YOLO/tracking
decisión
CIP/PLC
salida eléctrica
electroválvula
movimiento del pistón/cuchilla
velocidad del tractor
geometría cámara-cuchilla
margen de seguridad
```

No usar el factor x15 como sustituto de la velocidad física del tractor.

# Actualización 2026-10-12 — Continuidad de desarrollo e integración de app

## Referencia de implementación

**Estado: definida por el responsable del proyecto.** El algoritmo maestro
es `test/plc/moringa_algoritmo_plc.py`. La versión de IA incluida en `app/`
es anterior y su sustitución/integración queda pendiente. La revisión de
esta fecha fue estática y no agrega validaciones de hardware.

## Interfaz de configuración y operación

**Estado: prototipo incorporado y revisado.**

Disponible en código:

- Interfaz PyQt6 con pantallas de configuración, operación y prueba de cámara.
- Persistencia del serial de la cámara izquierda en JSON.
- Captura RealSense de color/profundidad a 848×480 y 60 FPS configurados.
- Hilos separados de cámara e IA, con procesamiento del frame más reciente.
- YOLO/tracking, anotaciones y conteos para dos regiones de la imagen.

Pendiente de validación en ejecución:

- Arranque, cambio entre pantallas, parada y cierre de cámara e IA.
- Comportamiento ante serial ausente/inválido y desconexión de cámara.
- Respuesta de la interfaz durante carga del modelo e inferencia.

## Preparación para incorporar el maestro

**Estado: pendiente; integración prevista para una etapa posterior.**

- [ ] Completar las dependencias de app y hacer portables sus rutas.
- [ ] Parametrizar resolución, regiones y umbrales para la cámara real.
- [ ] Definir la configuración del dispositivo de inferencia.
- [ ] Separar captura, visión y comunicación PLC para compartir la lógica
      del maestro con la interfaz y evitar mantener versiones divergentes.
- [ ] Integrar conexión persistente y mando bidireccional izquierdo,
      conservando el canal derecho sin órdenes hasta su validación.
- [ ] Distinguir eventos de visión, órdenes enviadas y confirmaciones PLC
      para que los conteos no oculten fallos de comunicación.
- [ ] Incorporar métricas de adquisición, visión, procesamiento y PLC;
      documentar qué Tag se usa para readback en cada ensayo.
- [ ] Definir manejo de errores, reconexión y comportamiento de parada
      junto con las condiciones de habilitación/interlocks del PLC.
- [ ] Validar primero el procesamiento sin actuación y después repetir
      las pruebas de integración con el hardware correspondiente.

## Mediciones físicas pendientes

Se mantiene la secuencia 3B → 3C → calibración `D_OPEN`/`D_CLOSE`.
El readback del maestro actual confirma Controller Tags de comando;
no equivale a leer la imagen de salida ni a medir la transición eléctrica.
Las mediciones históricas deben conservar su punto de lectura y condiciones
para permitir comparaciones correctas.

## Próximos hitos

- Desarrollo de software: preparar configuración y geometría de app para
  la futura incorporación del algoritmo maestro.
- Validación física: ejecutar 3B para AVANCE/RETROCESO y posteriormente
  3C, manteniendo documentadas las condiciones neumáticas del ensayo.

## Avance de integración — 2026-10-12

**Estado: implementación en app completada; validación física pendiente.**

- [x] Adaptar la lógica al frame de 848×480 y umbral y=240.
- [x] Fijar `device=0` en la inferencia de la interfaz.
- [x] Incorporar conexión persistente y mando bidireccional izquierdo.
- [x] Conservar el canal derecho sin escrituras PLC.
- [x] Confirmar consignas por readback y no contar órdenes fallidas.
- [x] Cargar el modelo desde el hilo de IA y cerrar la conexión al terminar.
- [x] Incorporar métricas por frame y escritura/readback.
- [x] Verificar comportamiento con ocho pruebas simuladas y sintaxis Python.
- [ ] Validar la interfaz con RealSense, CUDA y PLC reales.
- [ ] Definir el estado de parada y recuperación de comunicación con automatización.
- [ ] Unificar la lógica compartida entre maestro y app en un módulo común.

La implementación actual detiene el hilo ante errores y cierra la conexión;
no envía una consigna adicional al parar ni realiza reconexión automática.
La confirmación de Tags de comando no sustituye 3B/3C.

## Modularización de app — 2026-10-13

- [x] Separar navegación sobre el stackedWidget existente.
- [x] Separar persistencia de seriales y presentación de frames.
- [x] Centralizar propiedad y ciclo de vida de cámara/IA en VisionSession.
- [x] Conservar los slots conectados por Qt Designer y sus archivos generados.
- [x] Verificar navegación de la ventana y mantener regresión de visión/PLC.

Queda pendiente la validación con hardware. La extracción de una lógica común
entre el maestro y la interfaz continúa como trabajo posterior.

## Configuración PLC — 2026-10-13

- [x] Guardar IPv4 desde `IngresarIP_lineEdit` mediante `saveIP()`.
- [x] Recuperar configuración al abrir y pasarla a IA sin dirección fija.
- [x] Validar entradas y bloquear arranque sin IP guardada.
- [x] Verificar persistencia y transferencia mediante pruebas sin hardware.

Los cambios de IP se aplican al siguiente inicio de IA. La prueba real de
comunicación desde la pantalla PLC continúa pendiente.

## Pruebas manuales PLC y pistones — 2026-10-13

**Estado: comunicación, avance y retroceso implementados; validación física pendiente.**

- [x] Implementar los slots existentes de prueba de comunicación y mando izquierdo.
- [x] Ejecutar operaciones en un hilo y actualizar indicadores de consignas.
- [x] Desactivar el sentido opuesto antes de activar el solicitado y verificar readback.
- [x] Evitar concurrencia entre pruebas manuales e IA.
- [x] Completar 21 pruebas sin hardware, incluyendo cinco de control manual.
- [ ] Validar comunicación, avance y retroceso desde la pantalla con el PLC real.

### Apagado de pistones — pendiente acordado

Solo existen los tags de mando `CMD_ON_Cuchilla_Izquierda` y
`CMD_OFF_Cuchilla_Izquierda`. No existe confirmación física de fin de retroceso.

- [ ] Corroborar el tiempo real necesario para completar el retroceso.
- [ ] Corroborar el comportamiento de la válvula con ambos mandos en False
      y si el pistón permanece retraído.
- [ ] Con esos datos, definir e implementar la secuencia de retroceso y
      posterior apagado; no asumir que el readback confirma posición física.
- [ ] Validar físicamente la secuencia acordada.

Por decisión del responsable, este paso queda pendiente. El camino provisional
exige un sensor sin configurar y no envía órdenes de apagado. No se ha
implementado un retardo temporal ni validado la permanencia en retroceso.
Se conserva la secuencia de mediciones físicas 3B → 3C → calibración.

