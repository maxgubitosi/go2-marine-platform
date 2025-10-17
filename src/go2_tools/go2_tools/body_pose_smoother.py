import math, time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import Pose, TransformStamped

from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, TimeoutException, ConnectivityException

def clamp(v, lo, hi): return max(lo, min(hi, v))

def quat_from_rpy(r, p, y=0.0):
    cr, sr = math.cos(r/2), math.sin(r/2)
    cp, sp = math.cos(p/2), math.sin(p/2)
    cy, sy = math.cos(y/2), math.sin(y/2)
    return (
        sr*cp*cy - cr*sp*sy,  # x
        cr*sp*cy + sr*cp*sy,  # y
        cr*cp*sy - sr*sp*cy,  # z
        cr*cp*cy + sr*sp*sy   # w
    )

def rpy_from_quat(x, y, z, w):
    # roll
    sinr_cosp = 2*(w*x + y*z)
    cosr_cosp = 1 - 2*(x*x + y*y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    # pitch
    sinp = 2*(w*y - z*x)
    sinp = max(-1.0, min(1.0, sinp))
    pitch = math.asin(sinp)
    # yaw
    siny_cosp = 2*(w*z + x*y)
    cosy_cosp = 1 - 2*(y*y + z*z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    return roll, pitch, yaw

class BodyPoseSmoother(Node):
    """
    /go2/pose_rphz_cmd -> Float64MultiArray [roll_deg, pitch_deg, heave_m]

    - Lee TF (world->base_link) en cada ciclo para conocer la pose real (roll,pitch,yaw,z).
    - LPF exponencial (tau_cmd) del setpoint + limitador de velocidad (max_rate_z, max_rate_deg).
    - Publica /body_pose (geometry_msgs/Pose) con z + orientación (x/y no se tocan aquí).

    Parámetros clave:
      rate_hz:         Hz de publicación
      world_frame:     'world' (o 'odom' si tu pipeline usa odom)
      base_frame:      'base_link'
      yaw_mode:        'fixed' | 'track_tf'    (si usar yaw fijo o seguir el de TF)
      yaw_deg:         yaw fijo (si yaw_mode='fixed')
      tau_cmd:         s del filtro de setpoint (más grande = más suave)
      max_rate_z:      m/s  límite de velocidad en z
      max_rate_deg:    °/s  límite de velocidad angular (roll y pitch)
      z_init:          m  z de fallback si TF no llega
      debug_every_s:   cada cuántos segundos imprimir log
      roll_lim_deg:    [min,max] para clamp del objetivo
      pitch_lim_deg:   [min,max] para clamp del objetivo
      z_lim_m:         [min,max] para clamp del objetivo
    """
    def __init__(self):
        super().__init__('body_pose_smoother')

        # ==== Parámetros ====
        self.declare_parameter('rate_hz', 100.0)
        self.declare_parameter('world_frame', 'world')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('yaw_mode', 'fixed')   # 'fixed' | 'track_tf'
        self.declare_parameter('yaw_deg', 0.0)
        self.declare_parameter('tau_cmd', 0.8)
        self.declare_parameter('max_rate_z', 0.02)    # m/s
        self.declare_parameter('max_rate_deg', 0.5)   # °/s
        self.declare_parameter('z_init', 0.5)         # fallback si TF no llega
        self.declare_parameter('debug_every_s', 0.5)
        self.declare_parameter('roll_lim_deg', [-45.0, 45.0])
        self.declare_parameter('pitch_lim_deg', [-45.0, 45.0])
        self.declare_parameter('z_lim_m', [0.0, 1.5])

        self.rate_hz       = float(self.get_parameter('rate_hz').value)
        self.world_frame   = str(self.get_parameter('world_frame').value)
        self.base_frame    = str(self.get_parameter('base_frame').value)
        self.yaw_mode      = str(self.get_parameter('yaw_mode').value)
        self.yaw_deg_fixed = float(self.get_parameter('yaw_deg').value)
        self.tau_cmd       = float(self.get_parameter('tau_cmd').value)
        self.max_rate_z    = float(self.get_parameter('max_rate_z').value)
        self.max_rate_deg  = float(self.get_parameter('max_rate_deg').value)
        self.debug_every_s = float(self.get_parameter('debug_every_s').value)

        self.roll_lim_deg  = [float(v) for v in self.get_parameter('roll_lim_deg').value]
        self.pitch_lim_deg = [float(v) for v in self.get_parameter('pitch_lim_deg').value]
        self.z_lim_m       = [float(v) for v in self.get_parameter('z_lim_m').value]

        # ==== TF ====
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self, spin_thread=True)

        # Leer pose inicial desde TF (evita salto)
        roll0, pitch0, yaw0, z0 = self.read_tf_once(
            self.world_frame, self.base_frame, fallback_z=float(self.get_parameter('z_init').value)
        )

        # ==== Estado ====
        # Estado actual publicado
        self.cur_roll_deg  = math.degrees(roll0)
        self.cur_pitch_deg = math.degrees(pitch0)
        self.cur_yaw_deg   = math.degrees(yaw0)
        self.cur_z         = z0

        # Setpoint bruto y suavizado (inician iguales a la pose real)
        self.cmd_roll_raw  = self.cur_roll_deg
        self.cmd_pitch_raw = self.cur_pitch_deg
        self.cmd_z_raw     = self.cur_z

        self.cmd_roll  = self.cur_roll_deg
        self.cmd_pitch = self.cur_pitch_deg
        self.cmd_z     = self.cur_z

        # IO ROS
        self.pub = self.create_publisher(Pose, '/body_pose', 10)
        self.sub = self.create_subscription(Float64MultiArray, '/go2/pose_rphz_cmd', self.on_cmd, 10)

        # timing & debug
        self.dt = 1.0 / max(1e-3, self.rate_hz)
        self.last_t = time.monotonic()
        self.last_debug_t = self.last_t
        self.timer = self.create_timer(self.dt, self.on_tick)

        self.get_logger().info(
            f"Init TF pose: z={self.cur_z:.3f} m, roll={self.cur_roll_deg:.2f}°, "
            f"pitch={self.cur_pitch_deg:.2f}°, yaw={self.cur_yaw_deg:.2f}° | "
            f"frames: {self.world_frame}->{self.base_frame}"
        )

    # ---- Helpers ----
    def read_tf_once(self, world, base, timeout=1.0, fallback_z=0.5):
        try:
            ts: TransformStamped = self.tf_buffer.lookup_transform(
                world, base, rclpy.time.Time(), rclpy.duration.Duration(seconds=timeout)
            )
            z = float(ts.transform.translation.z)
            q = ts.transform.rotation
            roll, pitch, yaw = rpy_from_quat(q.x, q.y, q.z, q.w)
            return roll, pitch, yaw, z
        except (LookupException, TimeoutException, ConnectivityException):
            self.get_logger().warn(
                f"TF init no disponible ({world}->{base}); uso fallback z={fallback_z:.3f}, r=p=y=0"
            )
            return 0.0, 0.0, 0.0, float(fallback_z)

    def read_tf_now(self):
        """Lee TF actual; devuelve (roll_deg, pitch_deg, yaw_deg, z). Si falla, retorna None."""
        try:
            ts: TransformStamped = self.tf_buffer.lookup_transform(
                self.world_frame, self.base_frame, rclpy.time.Time()
            )
            z = float(ts.transform.translation.z)
            q = ts.transform.rotation
            roll, pitch, yaw = rpy_from_quat(q.x, q.y, q.z, q.w)
            return math.degrees(roll), math.degrees(pitch), math.degrees(yaw), z
        except Exception:
            return None

    # ---- Callbacks ----
    def on_cmd(self, msg: Float64MultiArray):
        if len(msg.data) < 3:
            self.get_logger().warn('Esperaba [roll_deg, pitch_deg, heave_m]')
            return
        rdeg = float(msg.data[0])
        pdeg = float(msg.data[1])
        h    = float(msg.data[2])

        # clamp del objetivo
        rdeg = clamp(rdeg, self.roll_lim_deg[0],  self.roll_lim_deg[1])
        pdeg = clamp(pdeg, self.pitch_lim_deg[0], self.pitch_lim_deg[1])
        h    = clamp(h,    self.z_lim_m[0],       self.z_lim_m[1])

        self.cmd_roll_raw  = rdeg
        self.cmd_pitch_raw = pdeg
        self.cmd_z_raw     = h

    def on_tick(self):
        # dt real
        now = time.monotonic()
        dt = now - self.last_t
        self.last_t = now
        if dt <= 0.0: dt = self.dt

        # ===== Leer TF actual para debug/seguimiento =====
        tf_now = self.read_tf_now()
        if tf_now is not None:
            self.cur_roll_deg, self.cur_pitch_deg, self.cur_yaw_deg, self.cur_z = tf_now

        # ===== Capa 1: LPF del setpoint =====
        alpha = 1.0 if self.tau_cmd <= 1e-6 else (1.0 - math.exp(-dt / self.tau_cmd))
        self.cmd_roll  += alpha * (self.cmd_roll_raw  - self.cmd_roll)
        self.cmd_pitch += alpha * (self.cmd_pitch_raw - self.cmd_pitch)
        self.cmd_z     += alpha * (self.cmd_z_raw     - self.cmd_z)

        # ===== Capa 2: limitador de velocidad =====
        max_dz   = self.max_rate_z   * dt         # m por tick
        max_dang = self.max_rate_deg * dt         # ° por tick

        # Usamos la "cur_*" proveniente de TF para cerrar en la medición real
        droll  = clamp(self.cmd_roll  - self.cur_roll_deg,  -max_dang, max_dang)
        dpitch = clamp(self.cmd_pitch - self.cur_pitch_deg, -max_dang, max_dang)
        dz     = clamp(self.cmd_z     - self.cur_z,         -max_dz,   max_dz)

        out_roll_deg  = self.cur_roll_deg  + droll
        out_pitch_deg = self.cur_pitch_deg + dpitch
        out_z         = self.cur_z         + dz

        # Yaw: fijo o seguir TF
        if self.yaw_mode == 'track_tf':
            yaw_deg = self.cur_yaw_deg
        else:
            yaw_deg = self.yaw_deg_fixed

        # Publicar Pose (z + orientación)
        r = math.radians(out_roll_deg)
        p = math.radians(out_pitch_deg)
        y = math.radians(yaw_deg)
        qx,qy,qz,qw = quat_from_rpy(r,p,y)

        pose = Pose()
        pose.position.z = float(out_z)
        pose.orientation.x = qx
        pose.orientation.y = qy
        pose.orientation.z = qz
        pose.orientation.w = qw
        self.pub.publish(pose)

        # ===== Debug cada N segundos =====
        if (now - self.last_debug_t) >= self.debug_every_s:
            self.last_debug_t = now
            self.get_logger().info(
                f"[MEAS] z={self.cur_z:.3f} m | roll={self.cur_roll_deg:.2f}° pitch={self.cur_pitch_deg:.2f}° yaw={self.cur_yaw_deg:.2f}°  || "
                f"[CMD(raw)] r={self.cmd_roll_raw:.2f}° p={self.cmd_pitch_raw:.2f}° z={self.cmd_z_raw:.3f}  || "
                f"[CMD(filt)] r={self.cmd_roll:.2f}° p={self.cmd_pitch:.2f}° z={self.cmd_z:.3f}  || "
                f"[OUT(step)] r→{out_roll_deg:.2f}° p→{out_pitch_deg:.2f}° z→{out_z:.3f}"
            )

def main():
    rclpy.init()
    node = BodyPoseSmoother()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
