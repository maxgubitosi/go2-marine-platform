#!/usr/bin/env python3
"""
Marine Platform Simulator v2 for Unitree Go2

Simula el movimiento de una plataforma marina (barco) usando el robot Go2.
Controla heave (vertical), pitch (cabeceo) y roll (balanceo).

Modos de ejecución (parámetro 'mode'):
- 'sim':  Publica Pose en /body_pose para Gazebo/champ (default)
- 'real': Envía comandos Euler al Go2 real via unitree_sdk2py

Arquitectura modo real (v2 — movimiento fluido):
- Un hilo dedicado (_sender_thread) genera la onda basada en time.time()
  y envía Euler() al Go2 a ~50 Hz de forma continua.
- El timer de ROS2 solo publica debug y logea (2 Hz).
- Smoothing temporal con constante tau (rate-independent).
- Esto elimina la desincronización entre hilos y los saltos discretos
  que causaban el movimiento "trabado" en v1.

Cambios principales v1 → v2:
- Sender: 10 Hz → 50 Hz (configurable via sender_rate_hz)
- Onda generada directamente en el sender (sin shared vars intermedias)
- Smoothing: EMA por frame → exponential temporal (1 - exp(-dt/tau))
- Timer ROS2 en modo real: solo debug a 2 Hz (no calcula onda)
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
        self.declare_parameter('wave_frequency', 0.15)
        self.declare_parameter('max_roll_deg', 15.0)
        self.declare_parameter('max_pitch_deg', 10.0)
        self.declare_parameter('max_heave_m', 0.1)
        self.declare_parameter('enable_manual', False)
        self.declare_parameter('wave_pattern', 'irregular')
        self.declare_parameter('phase_offset_pitch', 1.0)
        self.declare_parameter('phase_offset_heave', 1.5)
        self.declare_parameter('motion_model', 'second_order')
        self.declare_parameter('damping_ratio', 0.82)
        self.declare_parameter('natural_frequency_hz', 0.9)
        self.declare_parameter('max_roll_rate_deg_s', 45.0)
        self.declare_parameter('max_pitch_rate_deg_s', 35.0)
        self.declare_parameter('max_heave_rate_m_s', 0.18)

        # Smoothing temporal: tau = constante de tiempo en segundos.
        # tau=0.08s → 95% del target en ~0.24s (3*tau). Rate-independent.
        # Más bajo = más reactivo a cambios rápidos de onda.
        self.declare_parameter('smoothing_tau', 0.08)

        # Parámetros modo real
        self.declare_parameter('real_max_roll_deg', 20.0)
        self.declare_parameter('real_max_pitch_deg', 15.0)
        self.declare_parameter('real_max_heave_m', 0.04)
        self.declare_parameter('startup_ramp_seconds', 3.0)
        self.declare_parameter('network_interface', 'enp2s0')
        # Frecuencia del sender thread. 50 Hz = buen balance fluidez/carga.
        self.declare_parameter('sender_rate_hz', 50.0)

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
        self.real_initialized = False

        # Smoothing state para modo sim (el sender tiene su propio state)
        self.smooth_roll = 0.0
        self.smooth_pitch = 0.0
        self.smooth_heave = 0.0
        self.roll_velocity = 0.0
        self.pitch_velocity = 0.0
        self.heave_velocity = 0.0
        self._last_smooth_time = time.monotonic()

        # --- Variables compartidas con sender thread (modo real) ---
        self._target_lock = threading.Lock()
        # Debug: escritas por sender, leídas por timer para publicar
        self._debug_roll_deg = 0.0
        self._debug_pitch_deg = 0.0
        self._debug_heave_m = 0.0
        self._sender_actual_hz = 0.0
        self._sender_rpc_ms = 0.0
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
        if self.is_real:
            # Modo real: timer solo para debug/logging a 2 Hz
            self.dt = 0.5
            self.timer = self.create_timer(self.dt, self._debug_timer_callback)
        else:
            # Modo sim: timer genera onda y publica Pose
            rate_hz = self.get_parameter('rate_hz').get_parameter_value().double_value
            self.dt = 1.0 / max(1.0, rate_hz)
            self.timer = self.create_timer(self.dt, self.simulate_marine_motion)

        # ===== Logs iniciales =====
        manual = self.get_parameter('enable_manual').value
        self.get_logger().info(f"Marine Platform Simulator v2 — modo: {self.mode.upper()}")
        self.get_logger().info(f"Control: {'Manual' if manual else 'Automático'}, "
                               f"Rate: {1.0/self.dt:.0f} Hz")
        if self.is_real:
            mr = self.get_parameter('real_max_roll_deg').value
            mp = self.get_parameter('real_max_pitch_deg').value
            mh = self.get_parameter('real_max_heave_m').value
            ramp = self.get_parameter('startup_ramp_seconds').value
            sr = self.get_parameter('sender_rate_hz').value
            tau = self.get_parameter('smoothing_tau').value
            motion_model = self.get_parameter('motion_model').value
            damping = self.get_parameter('damping_ratio').value
            natural_hz = self.get_parameter('natural_frequency_hz').value
            self.get_logger().info(f"Límites REAL — Roll: ±{mr}°, Pitch: ±{mp}°, "
                                   f"Heave: ±{mh}m, Rampa: {ramp}s")
            self.get_logger().info(f"Sender: {sr} Hz target, Smoothing tau: {tau}s")
            self.get_logger().info(
                f"Motion model: {motion_model}, zeta={damping}, fn={natural_hz}Hz")

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
        sender_hz = self.get_parameter('sender_rate_hz').get_parameter_value().double_value
        self._sender_stop.clear()
        self._sender_thread = threading.Thread(
            target=self._sender_loop, daemon=True, name="go2_sender")
        self._sender_thread.start()
        self.get_logger().info(f"Hilo sender Go2 arrancado ({sender_hz:.0f} Hz target)")

        self.real_initialized = True
        self.start_time = time.time()
        self._last_smooth_time = time.monotonic()
        self.get_logger().info("=== GO2 LISTO — Iniciando wave motion ===")

    # =================================================================
    #  Sender thread — genera onda + envía Euler() a ~50 Hz
    # =================================================================
    def _sender_loop(self):
        """
        Hilo dedicado que:
        1. Genera la posición de onda basada en time.time() (continuo)
        2. Aplica smoothing temporal (rate-independent)
        3. Envía Euler() al Go2

        Corre a ~50 Hz (configurable). Si la RPC tarda más que el
        intervalo, el loop se adapta automáticamente sin acumular delay.
        """
        sender_hz = self.get_parameter('sender_rate_hz').get_parameter_value().double_value
        interval = 1.0 / max(1.0, sender_hz)
        tau = self.get_parameter('smoothing_tau').get_parameter_value().double_value
        motion_model = self.get_parameter('motion_model').get_parameter_value().string_value
        damping_ratio = self.get_parameter('damping_ratio').get_parameter_value().double_value
        natural_frequency_hz = self.get_parameter(
            'natural_frequency_hz').get_parameter_value().double_value
        max_roll_rate = self.get_parameter('max_roll_rate_deg_s').get_parameter_value().double_value
        max_pitch_rate = self.get_parameter(
            'max_pitch_rate_deg_s').get_parameter_value().double_value

        # Smoothing state local al sender (no compartido)
        smooth_roll = 0.0
        smooth_pitch = 0.0
        roll_velocity = 0.0
        pitch_velocity = 0.0
        last_time = time.monotonic()

        # Tracking de frame rate y latencia
        frame_count = 0
        fps_timer = time.monotonic()
        rpc_latency_sum = 0.0
        rpc_latency_count = 0

        while not self._sender_stop.is_set():
            t0 = time.monotonic()

            try:
                # --- 1. Check emergency stop ---
                if self.emergency_stop:
                    time.sleep(0.05)
                    continue

                # --- 2. Generar onda / leer manual ---
                if self.get_parameter('enable_manual').get_parameter_value().bool_value:
                    target_roll_deg = self.manual_roll
                    target_pitch_deg = self.manual_pitch
                else:
                    target_roll_deg, target_pitch_deg, _ = self._generate_wave()

                # --- 3. Startup ramp ---
                ramp = self._get_startup_ramp_factor()
                target_roll_deg *= ramp
                target_pitch_deg *= ramp

                # --- 4. Smoothing temporal (rate-independent) ---
                now = time.monotonic()
                dt = now - last_time
                last_time = now

                if motion_model == 'second_order':
                    smooth_roll, roll_velocity = self._advance_second_order(
                        smooth_roll, roll_velocity, target_roll_deg, dt,
                        natural_frequency_hz, damping_ratio, max_roll_rate)
                    smooth_pitch, pitch_velocity = self._advance_second_order(
                        smooth_pitch, pitch_velocity, target_pitch_deg, dt,
                        natural_frequency_hz, damping_ratio, max_pitch_rate)
                else:
                    if tau > 0.0 and dt > 0.0:
                        alpha = 1.0 - math.exp(-dt / tau)
                    else:
                        alpha = 1.0

                    smooth_roll += alpha * (target_roll_deg - smooth_roll)
                    smooth_pitch += alpha * (target_pitch_deg - smooth_pitch)

                # --- 5. Convertir y clampear ---
                roll_rad = math.radians(smooth_roll)
                pitch_rad = math.radians(smooth_pitch)
                roll_rad = max(-GO2_MAX_ROLL_RAD, min(GO2_MAX_ROLL_RAD, roll_rad))
                pitch_rad = max(-GO2_MAX_PITCH_RAD, min(GO2_MAX_PITCH_RAD, pitch_rad))

                # --- 6. Enviar al Go2 ---
                rpc_t0 = time.monotonic()
                self.sport_client.Euler(float(roll_rad), float(pitch_rad), 0.0)
                rpc_elapsed_ms = (time.monotonic() - rpc_t0) * 1000.0

                rpc_latency_sum += rpc_elapsed_ms
                rpc_latency_count += 1

                # --- 7. Actualizar debug values (bajo lock) ---
                with self._target_lock:
                    self._debug_roll_deg = smooth_roll
                    self._debug_pitch_deg = smooth_pitch
                    self._debug_heave_m = 0.0
                    self._sender_rpc_ms = rpc_elapsed_ms

                # --- 8. FPS tracking (cada 2s) ---
                frame_count += 1
                fps_elapsed = time.monotonic() - fps_timer
                if fps_elapsed >= 2.0:
                    actual_hz = frame_count / fps_elapsed
                    avg_rpc = rpc_latency_sum / max(1, rpc_latency_count)
                    with self._target_lock:
                        self._sender_actual_hz = actual_hz
                    if avg_rpc > 30.0:
                        self.get_logger().warn(
                            f"[sender] RPC Euler() lenta: {avg_rpc:.1f}ms avg "
                            f"({actual_hz:.0f} Hz efectivos)")
                    frame_count = 0
                    fps_timer = time.monotonic()
                    rpc_latency_sum = 0.0
                    rpc_latency_count = 0

            except Exception as e:
                self.get_logger().warn(f"[sender] Error: {e}")

            # --- Sleep adaptativo ---
            elapsed = time.monotonic() - t0
            remaining = interval - elapsed
            if remaining > 0:
                self._sender_stop.wait(remaining)

    # =================================================================
    #  Generación de ondas (thread-safe, basada en tiempo real)
    # =================================================================
    def _generate_wave(self):
        """Genera posición de onda basada en time.time(). Thread-safe."""
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
        omega = 2.0 * math.pi * freq

        wave_pattern = self.get_parameter('wave_pattern').value
        if wave_pattern == 'marine':
            # Mezcla no estacionaria: swell lento + componentes cruzadas + modulación
            # de amplitud para evitar una trayectoria periódica "de servo".
            envelope = (
                0.82
                + 0.14 * math.sin(omega * current_time * 0.11 + 0.4)
                + 0.08 * math.sin(omega * current_time * 0.037 + 1.7)
            )
            roll_primary = math.sin(omega * current_time + 0.35 * math.sin(omega * current_time * 0.13))
            roll_secondary = math.sin(omega * current_time * 1.62 + 0.8)
            roll_detail = math.sin(omega * current_time * 2.45 + 0.3 * math.sin(omega * current_time * 0.41))
            pitch_primary = math.sin(
                omega * current_time * 0.91 * phase_pitch
                + math.pi / 5
                + 0.28 * math.sin(omega * current_time * 0.09 + 0.6)
            )
            pitch_secondary = math.sin(omega * current_time * 1.38 + 1.4)
            heave_primary = math.sin(
                omega * current_time * 0.74 * phase_heave
                + 0.22 * math.sin(omega * current_time * 0.07 + 0.9)
            )
            heave_secondary = math.sin(omega * current_time * 1.16 + math.pi / 7)

            roll_deg = max_roll * envelope * (
                0.62 * roll_primary +
                0.26 * roll_secondary +
                0.12 * roll_detail
            )
            pitch_deg = max_pitch * envelope * (
                0.54 * pitch_primary +
                0.24 * pitch_secondary +
                0.14 * roll_primary +
                0.08 * heave_primary
            )
            heave_m = max_heave * (
                0.68 * heave_primary +
                0.22 * heave_secondary +
                0.10 * roll_secondary
            )
        elif wave_pattern == 'irregular':
            roll_deg = (max_roll * 0.6 * math.sin(omega * current_time) +
                        max_roll * 0.3 * math.sin(omega * current_time * 1.3 + math.pi / 4) +
                        max_roll * 0.1 * math.sin(omega * current_time * 2.1 + math.pi / 2))
            pitch_deg = (max_pitch * 0.7 * math.sin(omega * current_time * phase_pitch + math.pi / 3) +
                         max_pitch * 0.2 * math.sin(omega * current_time * 0.8 + math.pi) +
                         max_pitch * 0.1 * math.sin(omega * current_time * 1.7))
            heave_m = (max_heave * 0.8 * math.sin(omega * current_time * phase_heave) +
                       max_heave * 0.2 * math.sin(omega * current_time * 1.4 + math.pi / 6))
        else:
            roll_deg = max_roll * math.sin(omega * current_time)
            pitch_deg = max_pitch * math.sin(omega * current_time * phase_pitch + math.pi / 3)
            heave_m = max_heave * math.sin(omega * current_time * phase_heave)

        return roll_deg, pitch_deg, heave_m

    def _apply_temporal_smoothing(self, target_roll, target_pitch, target_heave):
        """Filtro temporal para modo sim."""
        now = time.monotonic()
        dt = now - self._last_smooth_time
        self._last_smooth_time = now

        motion_model = self.get_parameter('motion_model').get_parameter_value().string_value
        if motion_model == 'second_order':
            damping_ratio = self.get_parameter('damping_ratio').get_parameter_value().double_value
            natural_frequency_hz = self.get_parameter(
                'natural_frequency_hz').get_parameter_value().double_value
            max_roll_rate = self.get_parameter('max_roll_rate_deg_s').get_parameter_value().double_value
            max_pitch_rate = self.get_parameter(
                'max_pitch_rate_deg_s').get_parameter_value().double_value
            max_heave_rate = self.get_parameter(
                'max_heave_rate_m_s').get_parameter_value().double_value

            self.smooth_roll, self.roll_velocity = self._advance_second_order(
                self.smooth_roll, self.roll_velocity, target_roll, dt,
                natural_frequency_hz, damping_ratio, max_roll_rate)
            self.smooth_pitch, self.pitch_velocity = self._advance_second_order(
                self.smooth_pitch, self.pitch_velocity, target_pitch, dt,
                natural_frequency_hz, damping_ratio, max_pitch_rate)
            self.smooth_heave, self.heave_velocity = self._advance_second_order(
                self.smooth_heave, self.heave_velocity, target_heave, dt,
                natural_frequency_hz, damping_ratio, max_heave_rate)
        else:
            tau = self.get_parameter('smoothing_tau').get_parameter_value().double_value
            if tau > 0.0 and dt > 0.0:
                alpha = 1.0 - math.exp(-dt / tau)
            else:
                alpha = 1.0

            self.smooth_roll += alpha * (target_roll - self.smooth_roll)
            self.smooth_pitch += alpha * (target_pitch - self.smooth_pitch)
            self.smooth_heave += alpha * (target_heave - self.smooth_heave)
        return self.smooth_roll, self.smooth_pitch, self.smooth_heave

    def _advance_second_order(
            self, current, velocity, target, dt,
            natural_frequency_hz, damping_ratio, max_rate):
        """Dinámica 2º orden para dar sensación de masa e inercia."""
        if dt <= 0.0:
            return current, velocity

        omega_n = max(0.01, 2.0 * math.pi * natural_frequency_hz)
        damping = max(0.05, damping_ratio)
        acceleration = (
            (omega_n * omega_n) * (target - current) -
            (2.0 * damping * omega_n) * velocity
        )
        velocity += acceleration * dt

        if max_rate > 0.0:
            velocity = max(-max_rate, min(max_rate, velocity))

        current += velocity * dt
        return current, velocity

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
        return [sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy,
                cr * cp * sy - sr * sp * cy, cr * cp * cy + sr * sp * sy]

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
    #  Timer: modo sim — genera onda + publica Pose
    # =================================================================
    def simulate_marine_motion(self):
        """Timer callback para modo sim. Genera onda y publica Pose."""
        if self.emergency_stop:
            return

        if self.get_parameter('enable_manual').get_parameter_value().bool_value:
            target_roll = self.manual_roll
            target_pitch = self.manual_pitch
            target_heave = self.manual_heave
        else:
            target_roll, target_pitch, target_heave = self._generate_wave()

        smooth_roll, smooth_pitch, smooth_heave = self._apply_temporal_smoothing(
            target_roll, target_pitch, target_heave)

        roll_rad = math.radians(smooth_roll)
        pitch_rad = math.radians(smooth_pitch)

        cmd = Pose()
        cmd.position = Point(x=0.0, y=0.0, z=float(smooth_heave))
        q = self.euler_to_quaternion(roll_rad, pitch_rad, 0.0)
        cmd.orientation = Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])
        self.pose_cmd_pub.publish(cmd)

        # Debug topic
        debug_state = Vector3(x=smooth_roll, y=smooth_pitch, z=smooth_heave)
        self.debug_pub.publish(debug_state)

    # =================================================================
    #  Timer: modo real — solo debug/logging (2 Hz)
    # =================================================================
    def _debug_timer_callback(self):
        """Timer para modo real: publica debug y logea. No toca SDK2."""
        if self.emergency_stop or not self.real_initialized:
            return

        with self._target_lock:
            roll_deg = self._debug_roll_deg
            pitch_deg = self._debug_pitch_deg
            heave_m = self._debug_heave_m
            actual_hz = self._sender_actual_hz
            rpc_ms = self._sender_rpc_ms

        # Publicar debug
        debug_state = Vector3(x=roll_deg, y=pitch_deg, z=heave_m)
        self.debug_pub.publish(debug_state)

        # Log
        ramp = self._get_startup_ramp_factor()
        manual = self.get_parameter('enable_manual').value
        mode_str = f"{'Manual' if manual else 'Auto'}/REAL"
        ramp_str = f" ramp={ramp:.0%}" if ramp < 1.0 else ""
        hz_str = f" sender={actual_hz:.0f}Hz" if actual_hz > 0 else ""
        rpc_str = f" rpc={rpc_ms:.0f}ms" if rpc_ms > 0 else ""
        self.get_logger().info(
            f"[{mode_str}] Roll={roll_deg:.1f}°, Pitch={pitch_deg:.1f}°"
            f"{ramp_str}{hz_str}{rpc_str}")

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