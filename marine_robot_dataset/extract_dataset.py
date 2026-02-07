#!/usr/bin/env python3
"""
Extrae un dataset sincronizado desde un rosbag de simulación marina.
Cada fila del dataset corresponde a una imagen de la cámara del drone
con su timestamp ROS exacto, emparejada con los datos de pose, IMU y
articulaciones más cercanos temporalmente.

Genera:
  - dataset.csv con timestamps, poses, orientación y joints
  - frames/ con las imágenes extraídas del rosbag
  - frame_to_timestamp_mapping.csv

Uso: python3 extract_dataset.py <path_to_rosbag>
"""

import sys
import math
import sqlite3
from bisect import bisect_left
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import JointState, Imu, Image
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from tf2_msgs.msg import TFMessage


class RosbagDatasetExtractor:
    def __init__(self, rosbag_path, output_dir):
        self.rosbag_path = Path(rosbag_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.frames_dir = self.output_dir / "frames"
        self.frames_dir.mkdir(exist_ok=True)

        self.data = {
            'timestamp': [],
            'frame_path': [],
            'position_x': [],
            'position_y': [],
            'heave': [],
            'heave_dt_ms': [],
            'roll': [],
            'pitch': [],
            'yaw': [],
            'joint_names': [],
            'joint_positions': [],
            'joint_velocities': [],
        }
    
    # ------------------------------------------------------------------
    # Rosbag reading
    # ------------------------------------------------------------------

    def extract_messages(self, topic_name, message_type):
        """Extrae todos los mensajes de un topic del rosbag (SQLite3)."""
        db_path = list(self.rosbag_path.glob("*.db3"))[0]
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM topics WHERE name=?", (topic_name,))
        result = cursor.fetchone()
        if not result:
            print(f"  Topic {topic_name} no encontrado")
            conn.close()
            return []

        topic_id = result[0]
        cursor.execute(
            "SELECT timestamp, data FROM messages WHERE topic_id=? ORDER BY timestamp",
            (topic_id,),
        )

        messages = []
        for timestamp, data in cursor.fetchall():
            try:
                msg = deserialize_message(data, message_type)
                messages.append((timestamp, msg))
            except Exception as e:
                print(f"  Error deserializando mensaje: {e}")

        conn.close()
        return messages

    # ------------------------------------------------------------------
    # Math helpers
    # ------------------------------------------------------------------

    @staticmethod
    def quaternion_to_euler(x, y, z, w):
        """Quaternion a ángulos de Euler (roll, pitch, yaw)."""
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (w * y - z * x)
        pitch = math.copysign(math.pi / 2, sinp) if abs(sinp) >= 1 else math.asin(sinp)

        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return roll, pitch, yaw

    # ------------------------------------------------------------------
    # Nearest-neighbor search (binary search)
    # ------------------------------------------------------------------

    @staticmethod
    def find_closest(sorted_timestamps, target_ns, threshold_ns):
        """
        Busca el timestamp más cercano a target_ns en una lista ordenada.
        Retorna el índice o None si la diferencia supera threshold_ns.
        Complejidad: O(log N).
        """
        idx = bisect_left(sorted_timestamps, target_ns)
        candidates = []
        if idx > 0:
            candidates.append(idx - 1)
        if idx < len(sorted_timestamps):
            candidates.append(idx)

        best_idx = None
        best_diff = float('inf')
        for c in candidates:
            diff = abs(sorted_timestamps[c] - target_ns)
            if diff < best_diff:
                best_diff = diff
                best_idx = c

        if best_diff <= threshold_ns:
            return best_idx
        return None

    def find_tf_translation_z(self, tf_index, target_ns, parent_frame, child_frame):
        """
        Obtiene translation.z interpolando linealmente entre las dos TFs
        más cercanas al timestamp dado.
        Retorna (z_interpolado, dt_ms) donde dt_ms es la distancia temporal
        al dato TF más cercano en milisegundos.
        Retorna (None, None) solo si no hay datos.
        """
        key = (parent_frame, child_frame)
        if key not in tf_index:
            return None, None

        entries = tf_index[key]
        if not entries:
            return None, None

        timestamps = [e[0] for e in entries]
        idx = bisect_left(timestamps, target_ns)

        if idx == 0:
            dt_ms = abs(target_ns - timestamps[0]) / 1e6
            return entries[0][1].translation.z, dt_ms
        if idx >= len(entries):
            dt_ms = abs(target_ns - timestamps[-1]) / 1e6
            return entries[-1][1].translation.z, dt_ms

        # Interpolar linealmente entre entries[idx-1] y entries[idx]
        t0, tf0 = entries[idx - 1]
        t1, tf1 = entries[idx]
        alpha = (target_ns - t0) / (t1 - t0) if t1 != t0 else 0.0
        z0 = tf0.translation.z
        z1 = tf1.translation.z
        z_interp = z0 + alpha * (z1 - z0)

        # dt_ms = distancia al dato real más cercano
        dt_ms = min(abs(target_ns - t0), abs(target_ns - t1)) / 1e6
        return z_interp, dt_ms

    # ------------------------------------------------------------------
    # Image conversion
    # ------------------------------------------------------------------

    @staticmethod
    def image_msg_to_cv2(msg):
        """Convierte un sensor_msgs/Image a numpy array BGR (para cv2.imwrite)."""
        if msg.encoding == 'rgb8':
            img = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        elif msg.encoding == 'bgr8':
            return np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
        elif msg.encoding == 'mono8':
            return np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width)
        else:
            img = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    # ------------------------------------------------------------------
    # Main processing
    # ------------------------------------------------------------------

    def process_rosbag(self):
        """Procesa el rosbag completo y genera el dataset."""
        print(f"Procesando rosbag: {self.rosbag_path}")
        print()

        print("Extrayendo mensajes del rosbag...")
        image_messages = self.extract_messages('/drone/camera/image_raw', Image)
        joint_states = self.extract_messages('/joint_states', JointState)
        odom_messages = self.extract_messages('/odom', Odometry)
        imu_messages = self.extract_messages('/imu/data', Imu)
        tf_messages = self.extract_messages('/tf', TFMessage)
        base_pose_messages = self.extract_messages(
            '/base_to_footprint_pose', PoseWithCovarianceStamped
        )

        print(f"  {len(image_messages)} imagenes de camara")
        print(f"  {len(joint_states)} joint_states")
        print(f"  {len(odom_messages)} odometry")
        print(f"  {len(imu_messages)} IMU")
        print(f"  {len(tf_messages)} TF")
        if base_pose_messages:
            print(f"  {len(base_pose_messages)} base_to_footprint_pose (heave @ 50Hz)")
        print()

        if not image_messages:
            print("ERROR: No se encontraron imagenes en el rosbag.")
            print("Asegurate de grabar /drone/camera/image_raw en el rosbag.")
            sys.exit(1)

        # Indexar datos para búsqueda rápida
        js_dict = {ts: msg for ts, msg in joint_states}
        js_timestamps = sorted(js_dict.keys())

        odom_dict = {ts: msg for ts, msg in odom_messages}
        odom_timestamps = sorted(odom_dict.keys())

        imu_dict = {ts: msg for ts, msg in imu_messages}
        imu_timestamps = sorted(imu_dict.keys())

        # Heave: usar base_to_footprint_pose (50 Hz) si está disponible,
        # sino fallback a TF base_footprint->base_link (~2 Hz, interpolado)
        use_pose_for_heave = len(base_pose_messages) > 0
        if use_pose_for_heave:
            heave_dict = {ts: msg.pose.pose.position.z for ts, msg in base_pose_messages}
            heave_timestamps = sorted(heave_dict.keys())
            print(f"Usando base_to_footprint_pose para heave ({len(heave_timestamps)} muestras, ~50Hz)")
        else:
            print("base_to_footprint_pose no disponible, usando TF (interpolado, ~2Hz)")
            # Indexar TFs por par (parent, child) para búsqueda eficiente
            tf_index = {}
            for tf_ts, tf_msg in tf_messages:
                for transform in tf_msg.transforms:
                    key = (transform.header.frame_id, transform.child_frame_id)
                    if key not in tf_index:
                        tf_index[key] = []
                    tf_index[key].append((tf_ts, transform.transform))

        # Sincronizar: para cada imagen, buscar los datos más cercanos
        time_threshold_ns = 50_000_000  # 50ms
        synced_count = 0
        skipped_count = 0

        print(f"Sincronizando {len(image_messages)} imagenes con datos del rosbag...")
        for frame_num, (img_ts, img_msg) in enumerate(image_messages):

            js_idx = self.find_closest(js_timestamps, img_ts, time_threshold_ns)
            if js_idx is None:
                skipped_count += 1
                continue

            odom_idx = self.find_closest(odom_timestamps, img_ts, time_threshold_ns)
            if odom_idx is None:
                skipped_count += 1
                continue

            imu_idx = self.find_closest(imu_timestamps, img_ts, time_threshold_ns)
            if imu_idx is None:
                skipped_count += 1
                continue

            js_msg = js_dict[js_timestamps[js_idx]]
            odom_msg = odom_dict[odom_timestamps[odom_idx]]
            imu_msg = imu_dict[imu_timestamps[imu_idx]]

            # Heave: buscar dato de altura del trunk
            pos = odom_msg.pose.pose.position

            if use_pose_for_heave:
                heave_idx = self.find_closest(heave_timestamps, img_ts, time_threshold_ns)
                if heave_idx is not None:
                    trunk_z = heave_dict[heave_timestamps[heave_idx]]
                    dt_ms = abs(img_ts - heave_timestamps[heave_idx]) / 1e6
                else:
                    skipped_count += 1
                    continue
            else:
                trunk_z, dt_ms = self.find_tf_translation_z(
                    tf_index, img_ts, 'base_footprint', 'base_link'
                )
                if trunk_z is None:
                    skipped_count += 1
                    continue

            # Guardar imagen
            frame_filename = f"frame_{frame_num:06d}.png"
            frame_path = self.frames_dir / frame_filename
            img_cv2 = self.image_msg_to_cv2(img_msg)
            cv2.imwrite(str(frame_path), img_cv2)

            # Timestamp exacto de la imagen (nanosegundos ROS -> segundos)
            self.data['timestamp'].append(img_ts / 1e9)
            self.data['frame_path'].append(frame_filename)

            self.data['position_x'].append(pos.x)
            self.data['position_y'].append(pos.y)
            self.data['heave'].append(trunk_z)
            self.data['heave_dt_ms'].append(round(dt_ms, 1))

            # Orientación desde IMU
            orient = imu_msg.orientation
            roll, pitch, yaw = self.quaternion_to_euler(
                orient.x, orient.y, orient.z, orient.w
            )
            self.data['roll'].append(roll)
            self.data['pitch'].append(pitch)
            self.data['yaw'].append(yaw)

            # Articulaciones
            self.data['joint_names'].append(list(js_msg.name))
            self.data['joint_positions'].append(list(js_msg.position))
            self.data['joint_velocities'].append(list(js_msg.velocity))

            synced_count += 1
            if synced_count % 100 == 0:
                print(f"  {synced_count} frames procesados...")

        print(f"Sincronizados {synced_count} frames")
        if skipped_count > 0:
            print(f"Omitidos {skipped_count} frames (sin datos dentro del umbral de {time_threshold_ns/1e6:.0f}ms)")
        print()

        self.save_frame_mapping()
        self.save_dataset()

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def save_frame_mapping(self):
        """Guarda el mapeo de frames a timestamps."""
        mapping_path = self.output_dir / "frame_to_timestamp_mapping.csv"

        df = pd.DataFrame({
            'frame_path': self.data['frame_path'],
            'timestamp': self.data['timestamp'],
        })
        df['frame_number'] = df['frame_path'].str.extract(r'frame_(\d+)\.png').astype(int)
        df = df.sort_values('frame_number')

        with open(mapping_path, 'w') as f:
            f.write("frame_number,timestamp_ros_sec,timestamp_ros_nsec,timestamp_formatted\n")
            for _, row in df.iterrows():
                ts = row['timestamp']
                sec = int(ts)
                nsec = int((ts - sec) * 1e9)
                formatted = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                f.write(f"{int(row['frame_number'])},{sec},{nsec},{formatted}\n")

        print(f"Mapeo guardado: {len(df)} frames -> {mapping_path.name}")

    def save_dataset(self):
        """Guarda el dataset en CSV."""
        df = pd.DataFrame({
            'timestamp': self.data['timestamp'],
            'frame_path': self.data['frame_path'],
            'position_x': self.data['position_x'],
            'position_y': self.data['position_y'],
            'heave': self.data['heave'],
            'heave_dt_ms': self.data['heave_dt_ms'],
            'roll': self.data['roll'],
            'pitch': self.data['pitch'],
            'yaw': self.data['yaw'],
            'joint_names': [str(x) for x in self.data['joint_names']],
            'joint_positions': [str(x) for x in self.data['joint_positions']],
            'joint_velocities': [str(x) for x in self.data['joint_velocities']],
        })

        csv_path = self.output_dir / "dataset.csv"
        df.to_csv(csv_path, index=False)

        duration = df['timestamp'].max() - df['timestamp'].min()
        print(f"Dataset guardado: {len(df)} frames, {duration:.2f}s -> {csv_path}")

        # Estadísticas de calidad del heave
        valid = df['heave_dt_ms'].notna()
        if valid.any():
            dt = df.loc[valid, 'heave_dt_ms']
            precise = (dt <= 100).sum()
            interpolated = ((dt > 100) & (dt <= 500)).sum()
            extrapolated = (dt > 500).sum()
            print(f"  heave: {precise} precisos (<100ms), "
                  f"{interpolated} interpolados (100-500ms), "
                  f"{extrapolated} extrapolados (>500ms)")
            print(f"  heave dt_ms: min={dt.min():.1f}, "
                  f"median={dt.median():.1f}, max={dt.max():.1f}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 extract_dataset.py <path_to_rosbag>")
        print("Ejemplo: python3 extract_dataset.py ../rosbags/marine_sim_20260207_143824")
        sys.exit(1)

    rosbag_path = sys.argv[1]
    rosbag_name = Path(rosbag_path).name
    output_dir = Path("datasets") / rosbag_name

    extractor = RosbagDatasetExtractor(rosbag_path, output_dir)
    extractor.process_rosbag()

    print(f"\nDataset generado en: {output_dir}")


if __name__ == "__main__":
    main()
