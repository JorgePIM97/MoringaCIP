import pyrealsense2 as rs


class PosicionCamaras():

    def __init__(self):
        # self.ctx = rs.context()
        # self.devices = self.ctx.query_devices()
        pass

    def posicion_camaras(self):

        while True:
            ctx = rs.context()
            devices = ctx.query_devices()

            seriales = []

            if len(devices) < 2:
                print("Conectar ambas cámaras RealSense.")
                continue
        
            for i, dev in enumerate(devices):
                serial = dev.get_info(rs.camera_info.serial_number)
                name = dev.get_info(rs.camera_info.name)

                seriales.append(int(serial))

                # print(f"Cámara {i}: {name} | Serial: {serial}")

            serial_menor = min(seriales)
            serial_mayor = max(seriales)

        # # print("\n==========================")
        # # print(f"Serial MENOR: {serial_menor}")
        # # print(f"Serial MAYOR: {serial_mayor}")
        # # print("==========================")
        
            # break
            return serial_menor, serial_mayor    


posicion = PosicionCamaras()
izq, der = posicion.posicion_camaras()
print(izq)
print(der)