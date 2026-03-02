#!/usr/bin/env python3
"""
Control manual para la simulación de plataforma marina

Este script permite controlar manualmente el robot mediante comandos de teclado.
Útil para testing y demostración.

Controles:
  w/s: Aumentar/disminuir pitch
  a/d: Aumentar/disminuir roll  
  q/e: Aumentar/disminuir heave
  r: Reset a posición neutral
  SPACE: Emergency stop (modo real — DAMP)
  ESC/Ctrl+C: Salir

Uso:
  ros2 run go2_tools marine_manual_control
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import sys
import termios
import tty
import select


class MarineManualControl(Node):
    def __init__(self):
        super().__init__('marine_manual_control')
        
        # Estado actual
        self.roll = 0.0
        self.pitch = 0.0  
        self.heave = 0.0
        
        # Límites de seguridad
        self.max_roll = 20.0
        self.max_pitch = 15.0
        self.max_heave = 0.15
        
        # Incrementos por tecla
        self.angle_step = 2.0  # grados
        self.heave_step = 0.02  # metros
        
        # Publisher
        self.cmd_pub = self.create_publisher(
            Float64MultiArray,
            '/marine_platform/manual_cmd',
            10
        )
        
        # Configurar terminal para entrada sin buffer
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        
        self.get_logger().info("Control manual iniciado")
        self.print_instructions()
        self.publish_state()
        
        # Timer para check de teclas
        self.timer = self.create_timer(0.1, self.check_keyboard)
    
    def print_instructions(self):
        print("\n" + "="*50)
        print("   CONTROL MANUAL - PLATAFORMA MARINA")
        print("="*50)
        print("Controles:")
        print("  w/s: Pitch +/- (cabeceo)")
        print("  a/d: Roll +/- (balanceo)")  
        print("  q/e: Heave +/- (vertical)")
        print("  r:   Reset a posición neutral")
        print("  SPACE: EMERGENCY STOP (modo real)")
        print("  ESC: Salir")
        print("="*50)
        self.print_state()
    
    def print_state(self):
        print(f"\rRoll: {self.roll:+6.1f}° | "
              f"Pitch: {self.pitch:+6.1f}° | "
              f"Heave: {self.heave:+6.3f}m", end='', flush=True)
    
    def clamp_values(self):
        """Aplica límites de seguridad"""
        self.roll = max(-self.max_roll, min(self.max_roll, self.roll))
        self.pitch = max(-self.max_pitch, min(self.max_pitch, self.pitch))
        self.heave = max(-self.max_heave, min(self.max_heave, self.heave))
    
    def publish_state(self):
        """Publica el estado actual"""
        msg = Float64MultiArray()
        msg.data = [float(self.roll), float(self.pitch), float(self.heave)]
        self.cmd_pub.publish(msg)
        self.print_state()
    
    def check_keyboard(self):
        """Revisa si hay teclas presionadas"""
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            key = sys.stdin.read(1)
            
            # Procesar comando
            if key.lower() == 'w':
                self.pitch += self.angle_step
            elif key.lower() == 's':
                self.pitch -= self.angle_step
            elif key.lower() == 'a':
                self.roll -= self.angle_step
            elif key.lower() == 'd':
                self.roll += self.angle_step
            elif key.lower() == 'q':
                self.heave += self.heave_step
            elif key.lower() == 'e':
                self.heave -= self.heave_step
            elif key.lower() == 'r':
                self.roll = 0.0
                self.pitch = 0.0
                self.heave = 0.0
                print("\n[RESET] Posición neutral")
            elif key == ' ':  # SPACE = Emergency stop
                self.roll = 0.0
                self.pitch = 0.0
                self.heave = 0.0
                # Enviar señal de emergencia (999, 999, 999)
                msg = Float64MultiArray()
                msg.data = [999.0, 999.0, 999.0]
                self.cmd_pub.publish(msg)
                print("\n!!! EMERGENCY STOP ENVIADO !!!")
                return
            elif ord(key) == 27:  # ESC
                self.shutdown()
                return
            elif key == '\x03':  # Ctrl+C
                self.shutdown()
                return
            else:
                return  # Tecla no reconocida
            
            # Aplicar límites y publicar
            self.clamp_values()
            self.publish_state()
    
    def shutdown(self):
        """Restaura configuración del terminal y sale"""
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        print("\n\nSaliendo del control manual...")
        
        # Enviar comando neutral antes de salir
        msg = Float64MultiArray()
        msg.data = [0.0, 0.0, 0.0]
        self.cmd_pub.publish(msg)
        
        rclpy.shutdown()
        sys.exit(0)


def main():
    rclpy.init()
    
    try:
        node = MarineManualControl()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Restaurar terminal
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, node.old_settings)
        except:
            pass
        print("\nControl manual finalizado")


if __name__ == '__main__':
    main()
