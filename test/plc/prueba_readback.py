from pycomm3 import LogixDriver

PLC_IP = "192.168.1.10"

TAG_COMANDO = "CMD_Cuchilla_Izquierda"
TAG_SALIDA = "Local:1:O.Data.0"

with LogixDriver(PLC_IP) as plc:

    print("Estado inicial:")
    print("Comando:", plc.read(TAG_COMANDO))
    print("Salida :", plc.read(TAG_SALIDA))

    print("\nActivando...")
    plc.write(TAG_COMANDO, True)

    print("Comando:", plc.read(TAG_COMANDO))
    print("Salida :", plc.read(TAG_SALIDA))

    print("\nDesactivando...")
    plc.write(TAG_COMANDO, False)

    print("Comando:", plc.read(TAG_COMANDO))
    print("Salida :", plc.read(TAG_SALIDA))