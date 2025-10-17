#!/usr/bin/env python3
"""
Marine Platform Simulator for Unitree Go2

Este nodo simula el movimiento de una plataforma marina (barco) usando
el robot Go2. Permite controlar heave (movimiento vertical), pitch 
(cabeceo) y roll (balanceo) para simular el efecto de las olas.

Modos de operación:
- Automático: Simula ondas sinusoidales
- Manual: Control directo mediante comandos

Topics:
- Publica: /body_pose (Pose)
- Suscribe: /marine_platform/manual_cmd (Float64MultiArray) 
"""

import math
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import Vector3, Pose, Point, Quaternion


class MarinePlatformSimulator(Node):
    def __init__(self):
        super().__init__('marine_platform_simulator')
        
        # ===== Parámetros de configuración =====
        self.declare_parameter('rate_hz', 20.0)               # Frecuencia de publicación
        self.declare_parameter('wave_frequency', 0.1)         # Frecuencia de las olas en Hz
        self.declare_parameter('max_roll_deg', 15.0)          # Máximo balanceo en grados
        self.declare_parameter('max_pitch_deg', 10.0)         # Máximo cabeceo en grados  
        self.declare_parameter('max_heave_m', 0.1)            # Máximo heave en metros
        self.declare_parameter('enable_manual', False)        # Modo manual vs automático
        self.declare_parameter('wave_pattern', 'sinusoidal')  # Tipo de patrón: 'sinusoidal', 'irregular'
        self.declare_parameter('phase_offset_pitch', 1.0)     # Desfase entre roll y pitch
        self.declare_parameter('phase_offset_heave', 1.5)     # Desfase entre roll y heave
        self.declare_parameter('smoothing_factor', 0.95)     # Factor de suavizado (0-1)
        
        # ===== Variables de estado =====
        self.start_time = time.time()
        self.manual_roll = 0.0
        self.manual_pitch = 0.0
        self.manual_heave = 0.0
        
        # Variables para suavizado
        self.smooth_roll = 0.0
        self.smooth_pitch = 0.0
        self.smooth_heave = 0.0
        
        # ===== Publishers y Subscribers =====
        self.pose_cmd_pub = self.create_publisher(
            Pose, 
            '/body_pose', 
            10
        )
        
        self.manual_cmd_sub = self.create_subscription(
            Float64MultiArray,
            '/marine_platform/manual_cmd',
            self.manual_cmd_callback,
            10
        )
        
        # Publisher para debug/visualización
        self.debug_pub = self.create_publisher(
            Vector3,
            '/marine_platform/debug_state',
            10
        )
        
        # ===== Timer principal =====
        rate_hz = self.get_parameter('rate_hz').get_parameter_value().double_value
        self.dt = 1.0 / max(1.0, rate_hz)
        self.timer = self.create_timer(self.dt, self.simulate_marine_motion)
        
        # ===== Logs iniciales =====
        self.get_logger().info("Marine Platform Simulator iniciado")
        self.get_logger().info(f"Modo: {'Manual' if self.get_parameter('enable_manual').value else 'Automático'}")
        self.get_logger().info(f"Límites - Roll: ±{self.get_parameter('max_roll_deg').value}°, "
                              f"Pitch: ±{self.get_parameter('max_pitch_deg').value}°, "
                              f"Heave: ±{self.get_parameter('max_heave_m').value}m")

    def manual_cmd_callback(self, msg):
        """
        Callback para comandos manuales.
        Formato: [roll_deg, pitch_deg, heave_m]
        """
        if len(msg.data) >= 3:
            self.manual_roll = float(msg.data[0])
            self.manual_pitch = float(msg.data[1])
            self.manual_heave = float(msg.data[2])
            
            # Aplicar límites de seguridad
            max_roll = self.get_parameter('max_roll_deg').get_parameter_value().double_value
            max_pitch = self.get_parameter('max_pitch_deg').get_parameter_value().double_value
            max_heave = self.get_parameter('max_heave_m').get_parameter_value().double_value
            
            self.manual_roll = max(-max_roll, min(max_roll, self.manual_roll))
            self.manual_pitch = max(-max_pitch, min(max_pitch, self.manual_pitch))
            self.manual_heave = max(-max_heave, min(max_heave, self.manual_heave))
            
            self.get_logger().info(f"Comando manual recibido: "
                                  f"Roll={self.manual_roll:.1f}°, "
                                  f"Pitch={self.manual_pitch:.1f}°, "
                                  f"Heave={self.manual_heave:.3f}m")

    def generate_wave_motion(self):
        """
        Genera movimiento de olas basado en patrones sinusoidales.
        """
        current_time = time.time() - self.start_time
        
        # Obtener parámetros
        freq = self.get_parameter('wave_frequency').get_parameter_value().double_value
        max_roll = self.get_parameter('max_roll_deg').get_parameter_value().double_value
        max_pitch = self.get_parameter('max_pitch_deg').get_parameter_value().double_value
        max_heave = self.get_parameter('max_heave_m').get_parameter_value().double_value
        
        phase_pitch = self.get_parameter('phase_offset_pitch').get_parameter_value().double_value
        phase_heave = self.get_parameter('phase_offset_heave').get_parameter_value().double_value
        
        # Generar movimientos sinusoidales con diferentes fases para mayor realismo
        omega = 2 * math.pi * freq
        
        if self.get_parameter('wave_pattern').value == 'irregular':
            # Patrón irregular: suma de múltiples frecuencias
            roll_deg = (max_roll * 0.6 * math.sin(omega * current_time) +
                       max_roll * 0.3 * math.sin(omega * current_time * 1.3 + math.pi/4) +
                       max_roll * 0.1 * math.sin(omega * current_time * 2.1 + math.pi/2))
            
            pitch_deg = (max_pitch * 0.7 * math.sin(omega * current_time * phase_pitch + math.pi/3) +
                        max_pitch * 0.2 * math.sin(omega * current_time * 0.8 + math.pi) +
                        max_pitch * 0.1 * math.sin(omega * current_time * 1.7))
            
            heave_m = (max_heave * 0.8 * math.sin(omega * current_time * phase_heave) +
                      max_heave * 0.2 * math.sin(omega * current_time * 1.4 + math.pi/6))
        else:
            # Patrón sinusoidal simple
            roll_deg = max_roll * math.sin(omega * current_time)
            pitch_deg = max_pitch * math.sin(omega * current_time * phase_pitch + math.pi/3)
            heave_m = max_heave * math.sin(omega * current_time * phase_heave)
        
        return roll_deg, pitch_deg, heave_m

    def apply_smoothing(self, target_roll, target_pitch, target_heave):
        """
        Aplica suavizado exponencial para evitar movimientos bruscos.
        """
        smooth_factor = self.get_parameter('smoothing_factor').get_parameter_value().double_value
        
        # Filtro pasa-bajos exponencial
        self.smooth_roll = smooth_factor * self.smooth_roll + (1 - smooth_factor) * target_roll
        self.smooth_pitch = smooth_factor * self.smooth_pitch + (1 - smooth_factor) * target_pitch  
        self.smooth_heave = smooth_factor * self.smooth_heave + (1 - smooth_factor) * target_heave
        
        return self.smooth_roll, self.smooth_pitch, self.smooth_heave

    def euler_to_quaternion(self, roll, pitch, yaw):
        """
        Convierte ángulos de Euler a quaternion
        """
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        return [x, y, z, w]

    def simulate_marine_motion(self):
        """
        Función principal que se ejecuta periódicamente para simular el movimiento marino.
        """
        if self.get_parameter('enable_manual').get_parameter_value().bool_value:
            # Modo manual: usar comandos del usuario
            target_roll = self.manual_roll
            target_pitch = self.manual_pitch
            target_heave = self.manual_heave
        else:
            # Modo automático: generar movimiento de olas
            target_roll, target_pitch, target_heave = self.generate_wave_motion()
        
        # Aplicar suavizado para evitar saltos bruscos
        smooth_roll, smooth_pitch, smooth_heave = self.apply_smoothing(
            target_roll, target_pitch, target_heave
        )
        
        # Crear y publicar comando
        cmd = Pose()
        
        # Posición (heave es movimiento vertical)
        cmd.position = Point()
        cmd.position.x = 0.0
        cmd.position.y = 0.0
        cmd.position.z = float(smooth_heave)
        
        # Orientación (roll, pitch, yaw=0)
        roll_rad = math.radians(smooth_roll)
        pitch_rad = math.radians(smooth_pitch)
        yaw_rad = 0.0
        
        # Convertir ángulos de Euler a quaternion
        quat = self.euler_to_quaternion(roll_rad, pitch_rad, yaw_rad)
        cmd.orientation = Quaternion()
        cmd.orientation.x = quat[0]
        cmd.orientation.y = quat[1] 
        cmd.orientation.z = quat[2]
        cmd.orientation.w = quat[3]
        
        self.pose_cmd_pub.publish(cmd)
        
        # Publicar estado para debug/visualización
        debug_state = Vector3()
        debug_state.x = smooth_roll
        debug_state.y = smooth_pitch  
        debug_state.z = smooth_heave
        self.debug_pub.publish(debug_state)
        
        # Log cada 2 segundos para no saturar
        current_time = time.time()
        if not hasattr(self, '_last_log_time'):
            self._last_log_time = current_time
        
        if current_time - self._last_log_time > 2.0:
            mode = "Manual" if self.get_parameter('enable_manual').value else "Auto"
            self.get_logger().info(f"[{mode}] Roll={smooth_roll:.1f}°, "
                                  f"Pitch={smooth_pitch:.1f}°, "
                                  f"Heave={smooth_heave:.3f}m")
            self._last_log_time = current_time


def main():
    rclpy.init()
    
    try:
        node = MarinePlatformSimulator()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
