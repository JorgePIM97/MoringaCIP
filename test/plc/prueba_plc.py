from pycomm3 import LogixDriver

# IP del PLC Allen-Bradley
PLC_IP = "192.168.1.10"

with LogixDriver(PLC_IP) as plc:

    print("Conectado al PLC")

    # Escribir TRUE
    respuesta = plc.write("CMD_Cuchilla_Izquierda", True)

    print("Respuesta:", respuesta)