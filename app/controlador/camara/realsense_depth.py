#controlador/camara/realsense_depth.py
import pyrealsense2 as rs
import numpy as np

class DepthCamera() :
    def __init__(self, no_serial) :
        # Configure depth and color streams
        self.no_serial = no_serial
        self.width_frame_px = 848
        self.height_frame_px = 480
        self.fps_camara = 60
        self.pipeline = rs.pipeline()
        config = rs.config()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))


        config.enable_device(self.no_serial)
        config.enable_stream(rs.stream.depth, self.width_frame_px, self.height_frame_px, rs.format.z16, self.fps_camara)
        config.enable_stream(rs.stream.color, self.width_frame_px, self.height_frame_px, rs.format.bgr8, self.fps_camara)

        config.enable_stream(rs.stream.accel)
        config.enable_stream(rs.stream.gyro)

        # Start streaming
        self.pipeline.start(config)

    def gyro_data(gyro) :
        return np.asarray([gyro.x, gyro.y, gyro.z])

    def accel_data(self) :
        frames = self.pipeline.wait_for_frames()
        accel = frames[2].as_motion_frame().get_motion_data()
        accel = np.array([accel.x, accel.y, accel.z])
        return accel

    def get_frame(self) :
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        accel = frames[2].as_motion_frame().get_motion_data()
        accel = np.array([accel.x, accel.y, accel.z])
        gyro = frames[3].as_motion_frame().get_motion_data()
        gyro = np.array([gyro.x, gyro.y, gyro.z])
        # accel=np.asanyarray(accel.get_data)
        # print(color_frame)
        # print(accel)
        # new=self.accel_data(accel)
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        if not depth_frame or not color_frame :
            return False, None, None, None
        return True, depth_image, color_image, accel

    def release(self) :
        self.pipeline.stop()