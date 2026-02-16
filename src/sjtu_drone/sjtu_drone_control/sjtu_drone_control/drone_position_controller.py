#!/usr/bin/env python3
"""
Drone Position Controller – controla la posición del sjtu_drone.

Funcionalidades:
  1. Takeoff automático al iniciar
  2. Activa modo position control (posctrl)
  3. Envía posiciones target vía cmd_vel (en modo posctrl)
  4. Re-publica el GT pose como PoseStamped en /drone/pose para compatibilidad

El sjtu_drone tiene dos modos de control:
  - Normal (cmd_vel = velocidades/tilt)
  - Position control (cmd_vel = posición target x,y,z + yaw)

Usamos position control para mantener el dron en una posición fija (hover).

Topics suscritos:
  /<ns>/gt_pose  (geometry_msgs/Pose) – Ground truth del dron desde Gazebo
  /<ns>/state    (std_msgs/Int8)      – Estado del dron (0=LANDED,1=FLYING,2=TAKINGOFF,3=LANDING)

Topics publicados:
  /drone/pose    (geometry_msgs/PoseStamped) – Pose del dron (compatible con pipeline)
  /<ns>/cmd_vel  (geometry_msgs/Twist)       – Comandos de posición
  /<ns>/takeoff  (std_msgs/Empty)            – Takeoff
  /<ns>/posctrl  (std_msgs/Bool)             – Activar position control
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import Pose, PoseStamped, Twist
from std_msgs.msg import Empty, Bool, Int8
import math


class DronePositionController(Node):
    def __init__(self):
        super().__init__('drone_position_controller')

        # ── Parameters ────────────────────────────────────────────────
        self.declare_parameter('drone_namespace', 'drone')
        self.declare_parameter('target_x', 0.0)
        self.declare_parameter('target_y', 0.0)
        self.declare_parameter('target_z', 2.0)
        self.declare_parameter('target_yaw', 0.0)
        self.declare_parameter('hover_delay_sec', 3.0)
        self.declare_parameter('control_rate', 20.0)

        ns = self.get_parameter('drone_namespace').value
        self.target_x = self.get_parameter('target_x').value
        self.target_y = self.get_parameter('target_y').value
        self.target_z = self.get_parameter('target_z').value
        self.target_yaw = self.get_parameter('target_yaw').value
        self.hover_delay = self.get_parameter('hover_delay_sec').value
        control_rate = self.get_parameter('control_rate').value

        # QoS compatible con el plugin de Gazebo del sjtu_drone (best_effort)
        drone_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # ── Publishers ────────────────────────────────────────────────
        self.cmd_pub = self.create_publisher(Twist, f'/{ns}/cmd_vel', drone_qos)
        self.takeoff_pub = self.create_publisher(Empty, f'/{ns}/takeoff', drone_qos)
        self.posctrl_pub = self.create_publisher(Bool, f'/{ns}/posctrl', drone_qos)
        self.pose_pub = self.create_publisher(PoseStamped, '/drone/pose', 10)

        # ── Subscribers ───────────────────────────────────────────────
        self.gt_pose_sub = self.create_subscription(
            Pose, f'/{ns}/gt_pose', self.gt_pose_callback, drone_qos
        )
        self.state_sub = self.create_subscription(
            Int8, f'/{ns}/state', self.state_callback, drone_qos
        )

        # ── State ─────────────────────────────────────────────────────
        self.current_pose = None
        self.taken_off = False
        self.posctrl_active = False
        self.start_time = None
        self.takeoff_sent_time = None
        self.drone_state = 0  # 0=LANDED, 1=FLYING, 2=TAKINGOFF, 3=LANDING

        # Timer
        self.timer = self.create_timer(1.0 / control_rate, self.control_loop)

        self.get_logger().info(
            f'DronePositionController started – namespace=/{ns}  '
            f'target=({self.target_x}, {self.target_y}, {self.target_z})  '
            f'yaw={math.degrees(self.target_yaw):.1f}°  '
            f'hover_delay={self.hover_delay}s'
        )

    def gt_pose_callback(self, msg: Pose):
        self.current_pose = msg
        if self.start_time is None:
            self.start_time = self.get_clock().now()
            self.get_logger().info('First GT pose received, starting control sequence...')

        ps = PoseStamped()
        ps.header.stamp = self.get_clock().now().to_msg()
        ps.header.frame_id = 'world'
        ps.pose = msg
        self.pose_pub.publish(ps)

    def state_callback(self, msg: Int8):
        prev = self.drone_state
        self.drone_state = msg.data
        if prev != self.drone_state:
            state_names = {0: 'LANDED', 1: 'FLYING', 2: 'TAKINGOFF', 3: 'LANDING'}
            self.get_logger().info(
                f'Drone state changed: {state_names.get(prev, prev)} -> '
                f'{state_names.get(self.drone_state, self.drone_state)}'
            )

    def control_loop(self):
        if self.start_time is None:
            return

        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9

        # Paso 1: Takeoff (reenviar mientras siga LANDED)
        if not self.taken_off or self.drone_state == 0:
            if elapsed > 2.0:
                self.get_logger().info(
                    f'Sending TAKEOFF command... (drone_state={self.drone_state})',
                    throttle_duration_sec=2.0
                )
                self.takeoff_pub.publish(Empty())
                if not self.taken_off:
                    self.taken_off = True
                    self.takeoff_sent_time = self.get_clock().now()
            return

        # Paso 2: Activar position control
        if not self.posctrl_active:
            takeoff_elapsed = (self.get_clock().now() - self.takeoff_sent_time).nanoseconds / 1e9
            if takeoff_elapsed > self.hover_delay:
                self.get_logger().info('Activating POSITION CONTROL mode...')
                msg = Bool()
                msg.data = True
                self.posctrl_pub.publish(msg)
                self.posctrl_active = True
            return

        # Paso 3: Enviar posición target continuamente
        cmd = Twist()
        cmd.linear.x = self.target_x
        cmd.linear.y = self.target_y
        cmd.linear.z = self.target_z
        cmd.angular.z = self.target_yaw
        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = DronePositionController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
