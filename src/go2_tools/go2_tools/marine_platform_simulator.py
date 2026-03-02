#!/usr/bin/env python3
"""
Marine Platform Simulator for Unitree Go2

Simula el movimiento de una plataforma marina (barco) usando el robot Go2.
Controla heave (vertical), pitch (cabeceo) y roll (balanceo).

Modos de ejecución (parámetro 'mode'):
- 'sim':  Publica Pose en /body_pose para Gazebo/champ (default)
- 'real': Envía comandos Euler al Go2 real via unitree_sdk2py

Arquitectura modo real:
- El timer de ROS2 calcula la onda y actualiza variables target (no-bloqueante).
- Un hilo dedicado (_sender_thread) lee los targets y envía Euler() al Go2,
  evitando que la RPC bloqueante del SDK2 interfiera con el executor de ROS2
  (lo que causaba SIGSEGV exit code 139).
"""

import math
import os
import time
import threading
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import Vector3, Pose, Point, Quaternion

# =====================================================================
# Límites de hardware del Go2 (documentación oficial V2.0)
# =====================================================================
GO2_MAX_ROLL_RAD = 0.75       # ±0.75 rad (~43°)
GO2_MAX_PITCH_RAD = 0.75      # ±0.75 rad (~43°)
GO2_MAX_YAW_RAD = 0.6         # ±0.6 rad (~34°)


class MarinePlatformSimulator(Node):
    def __init__(self):
        super().__init__('marine_platform_simulator')

        # ===== Parámetros de configuración =====
        self.declare_parameter('mode', 'sim')
        self.declare_parameter('rate_hz', 20.0)
        self.declare_parameter('wave_frequency', 0.1)
        self.declare_parameter('max_roll_deg', 15.0)
        self.declare_parameter('max_pitch_deg', 10.0)
        self.declare_parameter('max_heave_m', 0.1)
        self.declare_parameter('enable_manual', False)
        self.declare_parameter('wave_pattern', 'sinusoidal')
        self.declare_parameter('phase_offset_pitch', 1.0)
        self.declare_parameter('phase_offset_heave', 1.5)
        self.declare_parameter('smoothing_factor', 0.3)

        # Parámetros modo real
        self.declare_parameter('real_max_roll_deg', 15.0)
        self.declare_parameter('real_max_pitch_deg', 10.0)
        self.declare_parameter('real_max_heave_m', 0.02)
        self.declare_parameter('startup_ramp_seconds', 3.0)
        self.declare_parameter('network_interface', 'enp2s0')

        # Detectar modo
        self.mode = self.get_parameter('mode').get_parameter_value().string_value
        assert self.mode in ('sim', 'real'), f"Modo inválido: '{self.mode}'."
        self.is_real = (self.mode == 'real')
        self._real_shutdown_done = False

        # ===== Variables de estado =====
        self.start_time = time.time()
        self.manual_roll = 0.0
        self.manual_pitch = 0.0
        self.manual_heave = 0.0
        self.emergency_stop = False
        self.smooth_roll = 0.0
        self.smooth_pitch = 0.0
        self.smooth_heave = 0.0
        self.real_initialized = False

        # --- Variables compartidas con sender thread (modo real) ---
        self._target_lock = threading.Lock()
        self._target_roll_rad = 0.0
        self._target_pitch_rad = 0.0
        self._sender_stop = threading.Event()
        self._sender_thread = None

        # ===== Setup modo-específico =====
        if self.is_real:
            self._setup_real_mode()
        else:
            self._setup_sim_mode()

        # ===== Subscribers comunes =====
        self.manual_cmd_sub = self.create_subscription(
            Float64MultiArray, '/marine_platform/manual_cmd',
            self.manual_cmd_callback, 10)

        self.debug_pub = self.create_publisher(
            Vector3, '/marine_platform/debug_state', 10)

        # ===== Timer principal =====
        rate_hz = self.get_parameter('rate_hz').get_parameter_value().double_value
        if self.is_real:
            rate_hz = min(rate_hz, 10.0)
        self.dt = 1.0 / max(1.0, rate_hz)
        self.timer = self.create_timer(self.dt, self.simulate_marine_motion)

        # ===== Logs iniciales =====
        manual = self.get_parameter('enable_manual').value
        self.get_logger().info(f"Marine Platform Simulator — modo: {self.mode.upper()}")
        self.get_logger().info(f"Control: {'Manual' if manual else 'Automático'}, "
                               f"Rate: {1.0/self.dt:.0f} Hz")
        if self.is_real:
            mr = self.get_parameter('real_max_roll_deg').value
            mp = self.get_parameter('real_max_pitch_deg').value
            mh = self.get_parameter('real_max_heave_m').value
            ramp = self.get_parameter('startup_ramp_seconds').value
            self.get_logger().info(f"Límites REAL — Roll: ±{mr}°, Pitch: ±{mp}°, "
                                   f"Heave: ±{mh}m, Rampa: {ramp}s")

    # =================================================================
    #  SETUP: modo sim
    # =================================================================
    def _setup_sim_mode(self):
        self.pose_cmd_pub = self.create_publisher(Pose, '/body_pose', 10)
        self.get_logger().info("Modo SIM: publicando Pose en /body_pose")

    # =================================================================
    #  SETUP: modo real
    # =================================================================
    def _setup_real_mode(self):
        try:
            from unitree_sdk2py.core.channel import ChannelFactoryInitialize
            from unitree_sdk2py.go2.sport.sport_client import SportClient
            from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient
        except ImportError as e:
            self.get_logger().fatal(f"unitree_sdk2py no encontrado: {e}")
            raise SystemExit(1)

        iface = self.get_parameter('network_interface').get_parameter_value().string_value
        self.get_logger().info(f"Modo REAL: DDS en interfaz '{iface}'...")

        if 'CYCLONEDDS_URI' in os.environ:
            del os.environ['CYCLONEDDS_URI']

        ChannelFactoryInitialize(0, iface)
        time.sleep(1.0)

        # Activar sport mode
        self.get_logger().info("Verificando modo del Go2 via MotionSwitcher...")
        self.motion_switcher = MotionSwitcherClient()
        self.motion_switcher.SetTimeout(5.0)
        self.motion_switcher.Init()
        time.sleep(1.0)

        code, result = self.motion_switcher.CheckMode()
        current_mode = result.get('name', '') if (code == 0 and result) else '?'
        self.get_logger().info(f"Modo actual: '{current_mode}' (code={code})")

        if current_mode != 'normal':
            self.get_logger().info("Activando sport mode ('normal')...")
            code, _ = self.motion_switcher.SelectMode('normal')
            if code != 0:
                self.get_logger().error(f"Error activando sport mode: {code}")
                raise SystemExit(1)
            self.get_logger().info("Esperando 3s para sport service...")
            time.sleep(3.0)
            code, result = self.motion_switcher.CheckMode()
            new_mode = result.get('name', '') if (code == 0 and result) else '?'
            if new_mode != 'normal':
                self.get_logger().error("No se pudo activar sport mode.")
                raise SystemExit(1)
        else:
            self.get_logger().info("Sport mode ya activo.")

        self.sport_client = SportClient()
        self.sport_client.SetTimeout(10.0)
        self.sport_client.Init()
        time.sleep(2.0)
        self.get_logger().info("SportClient SDK2 listo")

        self._init_timer = self.create_timer(2.0, self._initialize_real_robot)

    def _initialize_real_robot(self):
        """Inicialización one-shot del Go2 real."""
        self._init_timer.cancel()
        self.get_logger().info("=== INICIALIZANDO GO2 REAL ===")

        self.get_logger().info("RecoveryStand...")
        ret = self.sport_client.RecoveryStand()
        self.get_logger().info(f"  retornó: {ret}")
        if ret != 0:
            self.get_logger().error("RecoveryStand falló")
            return
        time.sleep(3.0)

        self.get_logger().info("BalanceStand...")
        ret = self.sport_client.BalanceStand()
        self.get_logger().info(f"  retornó: {ret}")
        time.sleep(1.0)

        # Arrancar hilo sender
        self._sender_stop.clear()
        self._sender_thread = threading.Thread(
            target=self._sender_loop, daemon=True, name="go2_sender")
        self._sender_thread.start()
        self.get_logger().info("Hilo sender Go2 arrancado (10 Hz)")

        self.real_initialized = True
        self.start_time = time.time()
        self.get_logger().info("=== GO2 LISTO — Iniciando wave motion ===")

    # =================================================================
    #  Sender thread — envía Euler() sin bloquear ROS2
    # =================================================================
    def _sender_loop(self):
        """
        Hilo dedicado: lee _target_roll/pitch_rad y envía Euler() a ~10 Hz.
        Desacoplado del timer de ROS2 para evitar SIGSEGV por RPC bloqueante.
        """
        interval = 0.1  # 10 Hz
        while not self._sender_stop.is_set():
            t0 = time.monotonic()
            try:
                with self._target_lock:
                    roll = self._target_roll_rad
                    pitch = self._target_pitch_rad

                roll = max(-GO2_MAX_ROLL_RAD, min(GO2_MAX_ROLL_RAD, roll))
                pitch = max(-GO2_MAX_PITCH_RAD, min(GO2_MAX_PITCH_RAD, pitch))
                self.sport_client.Euler(float(roll), float(pitch), 0.0)
            except Exception as e:
                self.get_logger().warn(f"[sender] Euler error: {e}")

            elapsed = time.monotonic() - t0
            remaining = interval - elapsed
            if remaining > 0:
                self._sender_stop.wait(remaining)

    # =================================================================
    #  Callbacks
    # =================================================================
    def manual_cmd_callback(self, msg):
        if len(msg.data) >= 3:
            if (abs(msg.data[0] - 999.0) < 0.1 and
                abs(msg.data[1] - 999.0) < 0.1 and
                abs(msg.data[2] - 999.0) < 0.1):
                self.emergency_stop = True
                if self.is_real:
                    self._sender_stop.set()
                    try:
                        self.sport_client.Damp()
                    except Exception:
                        pass
                self.get_logger().warn("EMERGENCY STOP!")
                return

            self.manual_roll = float(msg.data[0])
            self.manual_pitch = float(msg.data[1])
            self.manual_heave = float(msg.data[2])

            if self.is_real:
                mr = self.get_parameter('real_max_roll_deg').get_parameter_value().double_value
                mp = self.get_parameter('real_max_pitch_deg').get_parameter_value().double_value
                mh = self.get_parameter('real_max_heave_m').get_parameter_value().double_value
            else:
                mr = self.get_parameter('max_roll_deg').get_parameter_value().double_value
                mp = self.get_parameter('max_pitch_deg').get_parameter_value().double_value
                mh = self.get_parameter('max_heave_m').get_parameter_value().double_value

            self.manual_roll = max(-mr, min(mr, self.manual_roll))
            self.manual_pitch = max(-mp, min(mp, self.manual_pitch))
            self.manual_heave = max(-mh, min(mh, self.manual_heave))

    # =================================================================
    #  Generación de ondas
    # =================================================================
    def generate_wave_motion(self):
        current_time = time.time() - self.start_time
        freq = self.get_parameter('wave_frequency').get_parameter_value().double_value
        if self.is_real:
            max_roll = self.get_parameter('real_max_roll_deg').get_parameter_value().double_value
            max_pitch = self.get_parameter('real_max_pitch_deg').get_parameter_value().double_value
            max_heave = self.get_parameter('real_max_heave_m').get_parameter_value().double_value
        else:
            max_roll = self.get_parameter('max_roll_deg').get_parameter_value().double_value
            max_pitch = self.get_parameter('max_pitch_deg').get_parameter_value().double_value
            max_heave = self.get_parameter('max_heave_m').get_parameter_value().double_value

        phase_pitch = self.get_parameter('phase_offset_pitch').get_parameter_value().double_value
        phase_heave = self.get_parameter('phase_offset_heave').get_parameter_value().double_value
        omega = 2 * math.pi * freq

        if self.get_parameter('wave_pattern').value == 'irregular':
            roll_deg = (max_roll * 0.6 * math.sin(omega * current_time) +
                        max_roll * 0.3 * math.sin(omega * current_time * 1.3 + math.pi/4) +
                        max_roll * 0.1 * math.sin(omega * current_time * 2.1 + math.pi/2))
            pitch_deg = (max_pitch * 0.7 * math.sin(omega * current_time * phase_pitch + math.pi/3) +
                         max_pitch * 0.2 * math.sin(omega * current_time * 0.8 + math.pi) +
                         max_pitch * 0.1 * math.sin(omega * current_time * 1.7))
            heave_m = (max_heave * 0.8 * math.sin(omega * current_time * phase_heave) +
                       max_heave * 0.2 * math.sin(omega * current_time * 1.4 + math.pi/6))
        else:
            roll_deg = max_roll * math.sin(omega * current_time)
            pitch_deg = max_pitch * math.sin(omega * current_time * phase_pitch + math.pi/3)
            heave_m = max_heave * math.sin(omega * current_time * phase_heave)

        return roll_deg, pitch_deg, heave_m

    def apply_smoothing(self, target_roll, target_pitch, target_heave):
        sf = self.get_parameter('smoothing_factor').get_parameter_value().double_value
        self.smooth_roll = sf * self.smooth_roll + (1 - sf) * target_roll
        self.smooth_pitch = sf * self.smooth_pitch + (1 - sf) * target_pitch
        self.smooth_heave = sf * self.smooth_heave + (1 - sf) * target_heave
        return self.smooth_roll, self.smooth_pitch, self.smooth_heave

    def _get_startup_ramp_factor(self):
        if not self.is_real:
            return 1.0
        ramp_s = self.get_parameter('startup_ramp_seconds').get_parameter_value().double_value
        if ramp_s <= 0.0:
            return 1.0
        elapsed = time.time() - self.start_time
        return min(1.0, elapsed / ramp_s)

    def euler_to_quaternion(self, roll, pitch, yaw):
        cy, sy = math.cos(yaw * 0.5), math.sin(yaw * 0.5)
        cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
        cr, sr = math.cos(roll * 0.5), math.sin(roll * 0.5)
        return [sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy,
                cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy]

    # =================================================================
    #  Loop principal (timer callback)
    # =================================================================
    def simulate_marine_motion(self):
        """Calcula la onda y actualiza targets. No-bloqueante."""
        if self.emergency_stop:
            return
        if self.is_real and not self.real_initialized:
            return

        if self.get_parameter('enable_manual').get_parameter_value().bool_value:
            target_roll = self.manual_roll
            target_pitch = self.manual_pitch
            target_heave = self.manual_heave
        else:
            target_roll, target_pitch, target_heave = self.generate_wave_motion()

        smooth_roll, smooth_pitch, smooth_heave = self.apply_smoothing(
            target_roll, target_pitch, target_heave)

        ramp = self._get_startup_ramp_factor()
        smooth_roll *= ramp
        smooth_pitch *= ramp
        smooth_heave *= ramp

        roll_rad = math.radians(smooth_roll)
        pitch_rad = math.radians(smooth_pitch)

        if self.is_real:
            # Solo actualizar targets; el sender thread envía al Go2
            with self._target_lock:
                self._target_roll_rad = roll_rad
                self._target_pitch_rad = pitch_rad
        else:
            cmd = Pose()
            cmd.position = Point(x=0.0, y=0.0, z=float(smooth_heave))
            q = self.euler_to_quaternion(roll_rad, pitch_rad, 0.0)
            cmd.orientation = Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])
            self.pose_cmd_pub.publish(cmd)

        # Debug topic
        debug_state = Vector3(x=smooth_roll, y=smooth_pitch, z=smooth_heave)
        self.debug_pub.publish(debug_state)

        # Log cada 2s
        now = time.time()
        if not hasattr(self, '_last_log_time'):
            self._last_log_time = now
        if now - self._last_log_time > 2.0:
            manual = self.get_parameter('enable_manual').value
            mode_str = f"{'Manual' if manual else 'Auto'}/{self.mode.upper()}"
            ramp_str = f" ramp={ramp:.0%}" if self.is_real and ramp < 1.0 else ""
            self.get_logger().info(f"[{mode_str}] Roll={smooth_roll:.1f}°, "
                                   f"Pitch={smooth_pitch:.1f}°, "
                                   f"Heave={smooth_heave:.3f}m{ramp_str}")
            self._last_log_time = now

    # =================================================================
    #  Shutdown
    # =================================================================
    def _shutdown_real(self):
        if not self.is_real or self._real_shutdown_done:
            return
        self._real_shutdown_done = True
        self.get_logger().info("=== APAGANDO MODO REAL ===")

        # Detener sender thread
        self._sender_stop.set()
        if self._sender_thread and self._sender_thread.is_alive():
            self._sender_thread.join(timeout=2.0)

        try:
            self.sport_client.Euler(0.0, 0.0, 0.0)
            time.sleep(0.5)
            self.sport_client.BalanceStand()
            time.sleep(0.5)
            self.get_logger().info("=== GO2 APAGADO CORRECTAMENTE ===")
        except Exception:
            pass

    def destroy_node(self):
        self._shutdown_real()
        super().destroy_node()


def main():
    rclpy.init()
    node = None
    try:
        node = MarinePlatformSimulator()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except ExternalShutdownException:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()