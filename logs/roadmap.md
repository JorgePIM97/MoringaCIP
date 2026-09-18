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
