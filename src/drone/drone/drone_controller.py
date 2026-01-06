#!/usr/bin/env python3
"""
Drone Controller Node
Controla la posición del dron con movimiento vertical y ruido realista
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, TransformStamped
from tf2_ros import TransformBroadcaster
import numpy as np
import math


class DroneController(Node):
    def __init__(self):
        super().__init__('drone_controller')
        
        # Declarar parámetros
        self.declare_parameter('initial_height', 3.0)
        self.declare_parameter('vertical_range', 1.0)
        self.declare_parameter('vertical_velocity', 0.2)
        self.declare_parameter('position_x', 0.0)
        self.declare_parameter('position_y', 0.0)
        self.declare_parameter('noise_position_std', 0.05)  # 5cm std
        self.declare_parameter('noise_orientation_std', 0.035)  # ~2° std
        self.declare_parameter('update_rate', 50.0)  # Hz
        
        # Obtener parámetros
        self.initial_height = self.get_parameter('initial_height').value
        self.vertical_range = self.get_parameter('vertical_range').value
        self.vertical_velocity = self.get_parameter('vertical_velocity').value
        self.position_x = self.get_parameter('position_x').value
        self.position_y = self.get_parameter('position_y').value
        self.noise_pos_std = self.get_parameter('noise_position_std').value
        self.noise_ori_std = self.get_parameter('noise_orientation_std').value
        update_rate = self.get_parameter('update_rate').value
        
        # Publicador de pose
        self.pose_pub = self.create_publisher(Pose, '/drone/pose', 10)
        
        # Broadcaster de TF
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Estado interno
        self.time_elapsed = 0.0
        self.current_height = self.initial_height
        
        # Timer para actualización
        self.timer = self.create_timer(1.0 / update_rate, self.update_callback)
        
        self.get_logger().info(f'Drone Controller iniciado')
        self.get_logger().info(f'  Altura inicial: {self.initial_height}m')
        self.get_logger().info(f'  Rango vertical: ±{self.vertical_range}m')
        self.get_logger().info(f'  Velocidad vertical: {self.vertical_velocity}m/s')
        self.get_logger().info(f'  Posición XY: ({self.position_x}, {self.position_y})')
        self.get_logger().info(f'  Ruido posición: {self.noise_pos_std}m std')
        self.get_logger().info(f'  Ruido orientación: {math.degrees(self.noise_ori_std):.1f}° std')
    
    def update_callback(self):
        """Actualiza la posición del dron y publica pose + TF"""
        dt = 1.0 / self.get_parameter('update_rate').value
        self.time_elapsed += dt
        
        # Movimiento vertical sinusoidal
        # Periodo = 2 * pi * vertical_range / vertical_velocity
        period = 2.0 * math.pi * self.vertical_range / self.vertical_velocity
        omega = 2.0 * math.pi / period
        height_ideal = self.initial_height + self.vertical_range * math.sin(omega * self.time_elapsed)
        
        # Ruido en posición
        noise_x = np.random.normal(0, self.noise_pos_std)
        noise_y = np.random.normal(0, self.noise_pos_std)
        noise_z = np.random.normal(0, self.noise_pos_std * 0.5)
        
        position_x = self.position_x + noise_x
        position_y = self.position_y + noise_y
        position_z = height_ideal + noise_z
        
        # Ruido en orientación
        roll = np.random.normal(0, self.noise_ori_std)
        pitch = np.random.normal(0, self.noise_ori_std)
        yaw = 0.0
        
        # Convertir a quaternion
        qx, qy, qz, qw = self.euler_to_quaternion(roll, pitch, yaw)

        
        # Publicar pose
        pose_msg = Pose()
        pose_msg.position.x = position_x
        pose_msg.position.y = position_y
        pose_msg.position.z = position_z
        pose_msg.orientation.x = qx
        pose_msg.orientation.y = qy
        pose_msg.orientation.z = qz
        pose_msg.orientation.w = qw
        self.pose_pub.publish(pose_msg)
        
        # Publicar TF
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'world'
        t.child_frame_id = 'drone_base_link'
        t.transform.translation.x = position_x
        t.transform.translation.y = position_y
        t.transform.translation.z = position_z
        t.transform.rotation.x = qx
        t.transform.rotation.y = qy
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(t)
    
    @staticmethod
    def euler_to_quaternion(roll, pitch, yaw):
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        qw = cr * cp * cy + sr * sp * sy
        qx = sr * cp * cy - cr * sp * sy
        qy = cr * sp * cy + sr * cp * sy
        qz = cr * cp * sy - sr * sp * cy
        
        return qx, qy, qz, qw



def main(args=None):
    rclpy.init(args=args)
    node = DroneController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
