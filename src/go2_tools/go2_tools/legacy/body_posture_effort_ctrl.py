import math, time, shlex, re
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray
from rcl_interfaces.srv import GetParameters
from std_msgs.msg import Float64MultiArray

def clamp(v, lo, hi): return max(lo, min(hi, v))

def lpf_step(cur, tgt_raw, tau, dt):
    if tau <= 1e-6:
        return tgt_raw
    alpha = 1.0 - math.exp(-dt / tau)
    return cur + alpha * (tgt_raw - cur)

def safe_acos(x):
    return math.acos(clamp(x, -1.0, 1.0))

class BodyPostureEffortCtrl(Node):
    """
    Convierte (roll,pitch,heave) en ángulos por pierna (IK 2D) y publica esfuerzos (PD) a
    /joint_group_effort_controller/commands siguiendo el orden del parámetro 'joints' del controlador.

    Setpoint: /go2/pose_rphz_cmd  => Float64MultiArray [roll_deg, pitch_deg, heave_m]
    Estados:  /joint_states
    Salida:   /joint_group_effort_controller/commands (Float64MultiArray)
    """
    def __init__(self):
        super().__init__('body_posture_effort_ctrl')

        # ===== Parámetros de control / suavizado =====
        self.declare_parameter('rate_hz', 200.0)
        self.declare_parameter('tau_cmd', 0.8)       # s, filtro del setpoint
        self.declare_parameter('max_rate_z', 0.02)   # m/s
        self.declare_parameter('max_rate_deg', 0.5)  # °/s
        self.declare_parameter('Kp', 8.0)            # PD por junta (pos)
        self.declare_parameter('Kd', 0.3)

        # ===== Geometría / cinemática =====
        self.declare_parameter('bx', 0.18)   # semilargo (m)   (+x frente)
        self.declare_parameter('by', 0.11)   # semiancho (m)   (+y izquierda)
        self.declare_parameter('h0', 0.33)   # altura neutra cadera->suelo (m)
        self.declare_parameter('L_thigh', 0.20)
        self.declare_parameter('L_calf', 0.20)
        self.declare_parameter('x_foot_neutral', 0.02)  # avance pie relativo a cadera (m)
        self.declare_parameter('abad_neutral_deg', 0.0) # abducción neutral

        # ===== Juntas / controlador =====
        self.declare_parameter('controller_name', 'joint_group_effort_controller')
        self.declare_parameter('joints_override', [])  # lista explícita si auto no funciona

        # ===== Límites y clamps del objetivo =====
        self.declare_parameter('roll_lim_deg', [-15.0, 15.0])
        self.declare_parameter('pitch_lim_deg', [-15.0, 15.0])
        self.declare_parameter('z_lim_m', [0.45, 0.75])

        # ===== Lectura de parámetros =====
        self.rate_hz   = float(self.get_parameter('rate_hz').value)
        self.tau_cmd   = float(self.get_parameter('tau_cmd').value)
        self.max_rate_z    = float(self.get_parameter('max_rate_z').value)
        self.max_rate_deg  = float(self.get_parameter('max_rate_deg').value)
        self.Kp = float(self.get_parameter('Kp').value)
        self.Kd = float(self.get_parameter('Kd').value)

        self.bx = float(self.get_parameter('bx').value)
        self.by = float(self.get_parameter('by').value)
        self.h0 = float(self.get_parameter('h0').value)
        self.L1 = float(self.get_parameter('L_thigh').value)
        self.L2 = float(self.get_parameter('L_calf').value)
        self.x0 = float(self.get_parameter('x_foot_neutral').value)
        self.abad_neutral = math.radians(float(self.get_parameter('abad_neutral_deg').value))

        self.controller = str(self.get_parameter('controller_name').value)
        self.joints_override = [str(x) for x in self.get_parameter('joints_override').value]

        self.roll_lim = [float(v) for v in self.get_parameter('roll_lim_deg').value]
        self.pitch_lim= [float(v) for v in self.get_parameter('pitch_lim_deg').value]
        self.z_lim    = [float(v) for v in self.get_parameter('z_lim_m').value]

        # ===== Topic I/O =====
        self.pub_effort = self.create_publisher(Float64MultiArray, f'/{self.controller}/commands', 10)
        self.sub_cmd    = self.create_subscription(Float64MultiArray, '/go2/pose_rphz_cmd', self.on_cmd, 10)
        self.sub_js     = self.create_subscription(JointState, '/joint_states', self.on_js, 50)

        # ===== Estado interno =====
        self.dt = 1.0 / max(1.0, self.rate_hz)
        self.last_t = time.monotonic()
        self.last_debug = self.last_t
        self.debug_every = 0.5

        # Setpoint bruto y filtrado
        self.cmd_roll_raw = 0.0; self.cmd_pitch_raw = 0.0; self.cmd_z_raw = 0.60
        self.cmd_roll = 0.0; self.cmd_pitch = 0.0; self.cmd_z = 0.60
        # Para rate limit
        self.cur_roll_for_rate = 0.0; self.cur_pitch_for_rate = 0.0; self.cur_z_for_rate = 0.60

        # joint state
        self.js_pos = {}
        self.js_vel = {}

        # Orden de juntas del controlador
        self.joint_order = []
        self.leg_map = {}  # indices por pierna {'FL': {'abad':i, 'thigh':i, 'calf':i}, ...}

        # Timer principal
        self.timer = self.create_timer(self.dt, self.on_tick)

        # Obtener orden de juntas del controlador
        self.init_joint_order()

        self.get_logger().info(f"Effort PD: Kp={self.Kp} Kd={self.Kd} | rate={self.rate_hz} Hz")
        self.get_logger().info(f"Body dims bx={self.bx} by={self.by} h0={self.h0} | L1={self.L1} L2={self.L2}")

    # ---------- Utils ----------
    def init_joint_order(self):
        if self.joints_override:
            self.joint_order = list(self.joints_override)
            self.get_logger().warn(f"Usando joints_override con {len(self.joint_order)} juntas.")
        else:
            # Query parámetro 'joints' del controlador
            cli = self.create_client(GetParameters, f'/{self.controller}/get_parameters')
            if not cli.wait_for_service(timeout_sec=2.0):
                self.get_logger().warn(f"No pude consultar parámetros de {self.controller}. Usá joints_override.")
            else:
                req = GetParameters.Request()
                req.names = ['joints']
                future = cli.call_async(req)
                rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
                if future.result():
                    try:
                        arr = future.result().values[0].string_array_value
                        self.joint_order = list(arr)
                        self.get_logger().info(f"Orden de juntas del controlador: {self.joint_order}")
                    except Exception:
                        self.get_logger().warn("No pude leer 'joints' como string_array. Usá joints_override.")
                else:
                    self.get_logger().warn("GetParameters falló. Usá joints_override.")

        if not self.joint_order:
            # fallback típico Unitree (ajústalo si no coincide)
            self.joint_order = [
                'FL_hip_joint','FL_thigh_joint','FL_calf_joint',
                'FR_hip_joint','FR_thigh_joint','FR_calf_joint',
                'RL_hip_joint','RL_thigh_joint','RL_calf_joint',
                'RR_hip_joint','RR_thigh_joint','RR_calf_joint',
            ]
            self.get_logger().warn("Usando orden de juntas por defecto (tipo Unitree).")

        # Construir mapa de piernas por heurística de nombres
        self.leg_map = self.build_leg_map(self.joint_order)
        self.get_logger().info(f"leg_map: {self.leg_map}")

    def build_leg_map(self, joint_order):
        # Detecta FL/FR/RL/RR y roles (abad/thigh/calf) según patrones en el nombre
        role_patterns = {
            'abad': re.compile(r'(abad|abduction|hip(_?yaw)?|hip_lateral)', re.I),
            'thigh': re.compile(r'(thigh|hip(_?pitch)?|upper)', re.I),
            'calf': re.compile(r'(calf|knee|lower)', re.I),
        }
        legs = {'FL':{}, 'FR':{}, 'RL':{}, 'RR':{}}
        for i, name in enumerate(joint_order):
            leg = None
            if re.search(r'(^|_)FL|LF(_|$)', name, re.I):
                leg = 'FL'
            elif re.search(r'(^|_)FR|RF(_|$)', name, re.I):
                leg = 'FR'
            elif re.search(r'(^|_)RL|LH|HL(_|$)', name, re.I):
                leg = 'RL'
            elif re.search(r'(^|_)RR|RH|HR(_|$)', name, re.I):
                leg = 'RR'
            if leg is None:
                continue
            for role, pat in role_patterns.items():
                if pat.search(name):
                    legs[leg][role] = i
        return legs

    # ---------- Callbacks ----------
    def on_cmd(self, msg: Float64MultiArray):
        if len(msg.data) < 3:
            self.get_logger().warn("Esperaba [roll_deg, pitch_deg, heave_m]")
            return
        rdeg = clamp(float(msg.data[0]), self.get_parameter('roll_lim_deg').value[0], self.get_parameter('roll_lim_deg').value[1])
        pdeg = clamp(float(msg.data[1]), self.get_parameter('pitch_lim_deg').value[0], self.get_parameter('pitch_lim_deg').value[1])
        h    = clamp(float(msg.data[2]),  self.get_parameter('z_lim_m').value[0],    self.get_parameter('z_lim_m').value[1])
        self.cmd_roll_raw  = rdeg
        self.cmd_pitch_raw = pdeg
        self.cmd_z_raw     = h

    def on_js(self, msg: JointState):
        for n, p in zip(msg.name, msg.position):
            self.js_pos[n] = p
        if msg.velocity:
            for n, v in zip(msg.name, msg.velocity):
                self.js_vel[n] = v

    # ---------- IK y control ----------
    def ik_leg_planar(self, x, z):
        """
        IK 2D para (x,z) del pie respecto a la cadera en el plano sagital.
        Devuelve (q_thigh, q_knee) en rad. Convención: q_knee > 0 = flexión.
        """
        r = math.hypot(x, z)
        # evitar configuraciones imposibles
        r = max(1e-6, r)
        # Ley de cosenos
        cos_knee = (self.L1**2 + self.L2**2 - r**2) / (2*self.L1*self.L2)
        knee = math.pi - safe_acos(cos_knee)
        cos_hip = (self.L1**2 + r**2 - self.L2**2) / (2*self.L1*r)
        hip = math.atan2(z, x) - safe_acos(cos_hip)
        return hip, knee

    def leg_targets_from_body(self, roll_deg, pitch_deg, heave_m):
        """
        Para un roll/pitch/heave deseados, calcula el delta de altura por apoyo
        y convierte a (x,z) de pie por pierna. Mantenemos x≈x0, variamos z.
        Convención de signos:
          - roll>0 eleva lado izquierdo (y>0) y baja derecho.
          - pitch>0 eleva frente (x>0) y baja trasero.
        """
        roll = math.radians(roll_deg)
        pitch = math.radians(pitch_deg)

        # offsets de altura en el centro: heave_m relativo a h0
        base = heave_m

        # contribución por inclinación (aprox. pequeña ángulo)
        # delta_z ≈ roll * y + pitch * x
        dz_FL = ( roll*self.by +  pitch*self.bx)
        dz_FR = (-roll*self.by +  pitch*self.bx)
        dz_RL = ( roll*self.by + -pitch*self.bx)
        dz_RR = (-roll*self.by + -pitch*self.bx)

        # Altura total deseada cadera->suelo por pierna (positiva hacia arriba)
        # h_des = h0 + (base - h0) + dz = base + dz
        # donde 'base' es heave_m (altura cadera al suelo)
        h_FL = base + dz_FL
        h_FR = base + dz_FR
        h_RL = base + dz_RL
        h_RR = base + dz_RR

        # Convertimos a coordenadas del pie respecto a cadera (x,z):
        # cadera en (0,0); suelo hacia -z. Si h es distancia cadera-suelo,
        # el pie está en z = -h (aprox).
        x = self.x0
        legs = {
            'FL': (x, -h_FL),
            'FR': (x, -h_FR),
            'RL': (-x, -h_RL),  # traseras: x negativo
            'RR': (-x, -h_RR),
        }
        return legs

    def build_q_des(self, roll_deg, pitch_deg, heave_m):
        """
        Devuelve un vector de q_des (rad) alineado al orden self.joint_order.
        """
        legs_xz = self.leg_targets_from_body(roll_deg, pitch_deg, heave_m)

        # valores por defecto = posición actual (si no hay JS aún, 0)
        q_des = []
        for name in self.joint_order:
            q_des.append(self.js_pos.get(name, 0.0))

        # Para cada pierna, fijar abad=neutral y resolver IK para thigh/calf
        for leg, mp in self.leg_map.items():
            if not {'abad','thigh','calf'} <= mp.keys():
                self.get_logger().warn(f"Pierna {leg} incompleta en leg_map: {mp}")
                continue
            i_abad  = mp['abad'];  i_thigh = mp['thigh'];  i_calf = mp['calf']
            x,z = legs_xz[leg]
            q_thigh, q_knee = self.ik_leg_planar(x, z)
            q_des[i_abad]  = self.abad_neutral
            q_des[i_thigh] = q_thigh
            q_des[i_calf]  = q_knee
        return q_des

    def pd_efforts(self, q_des):
        """
        Construye el vector de esfuerzos siguiendo el mismo orden que 'joints'.
        τ = Kp*(q_des - q) - Kd*qdot
        """
        tau = []
        for name in self.joint_order:
            q = self.js_pos.get(name, 0.0)
            dq = self.js_vel.get(name, 0.0)
            e = (q_des[self.joint_order.index(name)] - q)
            tau.append(self.Kp * e - self.Kd * dq)
        return tau

    def on_tick(self):
        now = time.monotonic()
        dt = now - self.last_t
        self.last_t = now
        if dt <= 0.0: dt = self.dt

        # 1) Suavizar y rate-limit del setpoint
        self.cmd_roll  = lpf_step(self.cmd_roll,  self.cmd_roll_raw,  self.tau_cmd, dt)
        self.cmd_pitch = lpf_step(self.cmd_pitch, self.cmd_pitch_raw, self.tau_cmd, dt)
        self.cmd_z     = lpf_step(self.cmd_z,     self.cmd_z_raw,     self.tau_cmd, dt)

        max_dang = self.max_rate_deg * dt
        max_dz   = self.max_rate_z   * dt
        self.cur_roll_for_rate  += clamp(self.cmd_roll  - self.cur_roll_for_rate,  -max_dang, max_dang)
        self.cur_pitch_for_rate += clamp(self.cmd_pitch - self.cur_pitch_for_rate, -max_dang, max_dang)
        self.cur_z_for_rate     += clamp(self.cmd_z     - self.cur_z_for_rate,     -max_dz,   max_dz)

        # 2) IK -> q_des
        q_des = self.build_q_des(self.cur_roll_for_rate, self.cur_pitch_for_rate, self.cur_z_for_rate)

        # 3) PD -> esfuerzos
        tau = self.pd_efforts(q_des)

        # 4) Publicar
        msg = Float64MultiArray()
        msg.data = tau
        self.pub_effort.publish(msg)

        # 5) Debug
        if now - self.last_debug >= self.debug_every:
            self.last_debug = now
            self.get_logger().info(
                f"SP(raw) r={self.cmd_roll_raw:.2f} p={self.cmd_pitch_raw:.2f} z={self.cmd_z_raw:.3f} | "
                f"SP(smooth) r={self.cur_roll_for_rate:.2f} p={self.cur_pitch_for_rate:.2f} z={self.cur_z_for_rate:.3f}"
            )

def main():
    rclpy.init()
    node = BodyPostureEffortCtrl()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
