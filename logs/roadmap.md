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
