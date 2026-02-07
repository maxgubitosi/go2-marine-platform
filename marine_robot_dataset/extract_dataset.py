#!/usr/bin/env python3
"""
Script para extraer dataset de rosbags de simulación marina.
Genera: frame de video + posición del robot + ángulos de articulaciones
Utiliza mapeo correcto de frames a timestamps del video.
"""

import os
import sys
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import sqlite3
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import JointState, Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_msgs.msg import TFMessage
import yaml
import math
import numpy as np


class RosbagDatasetExtractor:
    def __init__(self, rosbag_path, output_dir):
        self.rosbag_path = Path(rosbag_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectorios
        self.frames_dir = self.output_dir / "frames"
        self.frames_dir.mkdir(exist_ok=True)
        
        self.data = {
            'timestamp': [],
            'frame_path': [],
            'position_x': [],
            'position_y': [],
            'position_z': [],
            'roll': [],
            'pitch': [],
            'yaw': [],
            'joint_names': [],
            'joint_positions': [],
            'joint_velocities': [],
        }
    
    def quaternion_to_euler(self, x, y, z, w):
        """Convierte quaternion a ángulos de Euler (roll, pitch, yaw)"""
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        
        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)  # Use 90 degrees if out of range
        else:
            pitch = math.asin(sinp)
        
        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        return roll, pitch, yaw
    
    def read_metadata(self):
        """Lee metadata del rosbag"""
        metadata_path = self.rosbag_path / "metadata.yaml"
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
        return metadata
    
    def get_video_info(self, video_path):
        """Obtiene información real del video (FPS, frame count, duración)"""
        if not video_path.exists():
            print(f"⚠️  Video no encontrado: {video_path}")
            return None
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"⚠️  No se pudo abrir el video: {video_path}")
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Contar frames reales leyendo el video completo
        frame_count = 0
        while True:
            ret, _ = cap.read()
            if not ret:
                break
            frame_count += 1
        cap.release()
        
        duration = frame_count / fps if fps > 0 else 0
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration
        }
    
    def extract_messages(self, topic_name, message_type):
        """Extrae mensajes de un topic específico del rosbag"""
        db_path = list(self.rosbag_path.glob("*.db3"))[0]
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Obtener topic_id
        cursor.execute("SELECT id FROM topics WHERE name=?", (topic_name,))
        result = cursor.fetchone()
        if not result:
            print(f"⚠️  Topic {topic_name} no encontrado")
            return []
        
        topic_id = result[0]
        
        # Extraer mensajes
        cursor.execute("""
            SELECT timestamp, data 
            FROM messages 
            WHERE topic_id=? 
            ORDER BY timestamp
        """, (topic_id,))
        
        messages = []
        for timestamp, data in cursor.fetchall():
            try:
                msg = deserialize_message(data, message_type)
                messages.append((timestamp, msg))
            except Exception as e:
                print(f"Error deserializando mensaje: {e}")
        
        conn.close()
        return messages
    
    def process_rosbag(self):
        """Procesa el rosbag completo"""
        print(f"📂 Procesando rosbag: {self.rosbag_path}")
        print()
        
        # Obtener información del video
        video_path = self.rosbag_path / "output.avi"
        video_info = None
        
        if video_path.exists():
            video_info = self.get_video_info(video_path)
            if video_info:
                print(f"📹 Video info:")
                print(f"   FPS: {video_info['fps']:.2f}")
                print(f"   Frames totales: {video_info['frame_count']}")
                print(f"   Duración: {video_info['duration']:.2f}s")
                print()
        
        # Extraer datos de topics
        print("📥 Extrayendo datos del rosbag...")
        joint_states = self.extract_messages('/joint_states', JointState)
        odom_messages = self.extract_messages('/odom', Odometry)
        imu_messages = self.extract_messages('/imu/data', Imu)
        tf_messages = self.extract_messages('/tf', TFMessage)
        
        print(f"✅ Extraídos:")
        print(f"   - {len(joint_states)} joint_states")
        print(f"   - {len(odom_messages)} odometry")
        print(f"   - {len(imu_messages)} IMU")
        print(f"   - {len(tf_messages)} TF messages")
        print()
        
        # Sincronizar datos con frames de video
        if video_info:
            self.synchronize_with_video_frames(video_info, joint_states, odom_messages, imu_messages, tf_messages=tf_messages)
            # Guardar mapeo de frames a timestamps
            self.save_frame_mapping()
        else:
            print("⚠️  No se encontró video, sincronizando solo datos del rosbag")
            self.synchronize_data(joint_states, odom_messages, imu_messages, tf_messages=tf_messages)
        
        # Guardar dataset
        self.save_dataset()
    
    def synchronize_data(self, joint_states, odom_messages, imu_messages, tf_messages=None, time_threshold=50000000):
        """
        Sincroniza joint_states con odometry e IMU por timestamp.
        time_threshold en nanosegundos (default: 50ms)
        """
        print("🔄 Sincronizando datos...")
        
        odom_dict = {ts: msg for ts, msg in odom_messages}
        odom_timestamps = sorted(odom_dict.keys())
        
        imu_dict = {ts: msg for ts, msg in imu_messages}
        imu_timestamps = sorted(imu_dict.keys())
        
        frame_count = 0
        for js_timestamp, js_msg in joint_states:
            # Buscar odometry más cercana
            closest_odom_ts = min(odom_timestamps, 
                                 key=lambda x: abs(x - js_timestamp))
            
            if abs(closest_odom_ts - js_timestamp) > time_threshold:
                continue  # Skip si están muy separados
            
            # Buscar IMU más cercana
            closest_imu_ts = min(imu_timestamps,
                                key=lambda x: abs(x - js_timestamp))
            
            if abs(closest_imu_ts - js_timestamp) > time_threshold:
                continue  # Skip si están muy separados
            
            odom_msg = odom_dict[closest_odom_ts]
            imu_msg = imu_dict[closest_imu_ts]
            
            # Guardar datos sincronizados
            self.data['timestamp'].append(js_timestamp / 1e9)  # Convertir a segundos
            self.data['frame_path'].append(f"frame_{frame_count:06d}.png")
            
            # Posición del lomo (trunk)
            # La odometría da la posición de base_footprint (punto de apoyo, z=0)
            # Necesitamos la posición de trunk (lomo) = base_footprint + transformación base_footprint->base_link
            # Como base_link y trunk son el mismo frame, solo necesitamos la transformación base_footprint->base_link
            pos_footprint = odom_msg.pose.pose.position
            
            # Obtener transformación base_footprint -> base_link para obtener altura del lomo
            trunk_pos = (pos_footprint.x, pos_footprint.y, pos_footprint.z)
            if tf_messages:
                tf_result = self.get_tf_transform(tf_messages, js_timestamp, 'base_footprint', 'base_link', time_threshold=100000000)
                if tf_result:
                    translation, rotation = tf_result
                    # Aplicar transformación para obtener posición del lomo
                    trunk_pos = self.apply_transform((pos_footprint.x, pos_footprint.y, pos_footprint.z), translation, rotation)
            
            self.data['position_x'].append(trunk_pos[0])
            self.data['position_y'].append(trunk_pos[1])
            self.data['position_z'].append(trunk_pos[2])
            
            # Orientación (de IMU - más preciso para roll y pitch)
            orient = imu_msg.orientation
            roll, pitch, yaw = self.quaternion_to_euler(orient.x, orient.y, orient.z, orient.w)
            self.data['roll'].append(roll)
            self.data['pitch'].append(pitch)
            self.data['yaw'].append(yaw)
            
            # Articulaciones
            self.data['joint_names'].append(list(js_msg.name))
            self.data['joint_positions'].append(list(js_msg.position))
            self.data['joint_velocities'].append(list(js_msg.velocity))
            
            frame_count += 1
        
        print(f"✅ Sincronizados {frame_count} frames")
    
    def get_tf_transform(self, tf_messages, target_timestamp_ns, parent_frame, child_frame, time_threshold=100000000):
        """
        Obtiene la transformación TF más cercana a un timestamp dado.
        Retorna (translation, rotation) o None si no se encuentra.
        """
        closest_tf = None
        min_diff = float('inf')
        
        for tf_timestamp_ns, tf_msg in tf_messages:
            time_diff = abs(tf_timestamp_ns - target_timestamp_ns)
            if time_diff < min_diff and time_diff < time_threshold:
                for transform in tf_msg.transforms:
                    if transform.header.frame_id == parent_frame and transform.child_frame_id == child_frame:
                        closest_tf = transform.transform
                        min_diff = time_diff
                        break
        
        if closest_tf:
            return (closest_tf.translation, closest_tf.rotation)
        return None
    
    def apply_transform(self, position, translation, rotation):
        """
        Aplica una transformación TF a una posición.
        position: (x, y, z)
        translation: geometry_msgs/Vector3
        rotation: geometry_msgs/Quaternion
        Retorna nueva posición (x, y, z)
        """
        # Convertir quaternion a matriz de rotación
        qx, qy, qz, qw = rotation.x, rotation.y, rotation.z, rotation.w
        
        # Matriz de rotación desde quaternion
        R = np.array([
            [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qz*qw), 2*(qx*qz + qy*qw)],
            [2*(qx*qy + qz*qw), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qx*qw)],
            [2*(qx*qz - qy*qw), 2*(qy*qz + qx*qw), 1 - 2*(qx**2 + qy**2)]
        ])
        
        # Aplicar rotación y luego traslación
        pos_vec = np.array([position[0], position[1], position[2]])
        trans_vec = np.array([translation.x, translation.y, translation.z])
        
        rotated = R @ pos_vec
        transformed = rotated + trans_vec
        
        return (transformed[0], transformed[1], transformed[2])
    
    def synchronize_with_video_frames(self, video_info, joint_states, odom_messages, imu_messages, video_start_delay=3.0, time_threshold=50000000, tf_messages=None):
        """
        Sincroniza datos del rosbag con los frames reales del video.
        Usa timestamps reales del rosbag, no timestamps teóricos calculados.
        video_info: dict con 'fps', 'frame_count', 'duration'
        time_threshold en nanosegundos (default: 50ms)
        """
        print(f"🔄 Sincronizando {video_info['frame_count']} frames de video con datos del rosbag...")
        
        # Obtener timestamp de inicio del rosbag
        metadata = self.read_metadata()
        rosbag_start_ns = metadata['rosbag2_bagfile_information']['starting_time']['nanoseconds_since_epoch']
        
        # El video comienza video_start_delay segundos después del rosbag
        video_start_ns = rosbag_start_ns + int(video_start_delay * 1e9)
        frame_duration_ns = int((1.0 / video_info['fps']) * 1e9)
        
        # Crear diccionarios para búsqueda rápida
        joint_states_dict = {ts: msg for ts, msg in joint_states}
        js_timestamps = sorted(joint_states_dict.keys())
        
        odom_dict = {ts: msg for ts, msg in odom_messages}
        odom_timestamps = sorted(odom_dict.keys())
        
        imu_dict = {ts: msg for ts, msg in imu_messages}
        imu_timestamps = sorted(imu_dict.keys())
        
        synced_count = 0
        skipped_count = 0
        
        # Para cada frame real del video, calcular timestamp teórico y buscar datos reales del rosbag
        for frame_num in range(video_info['frame_count']):
            # Timestamp teórico del frame (basado en FPS)
            theoretical_timestamp_ns = video_start_ns + (frame_num * frame_duration_ns)
            
            # Buscar joint_state más cercano en el rosbag (usar timestamp real del rosbag)
            closest_js_ts = min(js_timestamps, key=lambda x: abs(x - theoretical_timestamp_ns))
            time_diff_js = abs(closest_js_ts - theoretical_timestamp_ns)
            
            if time_diff_js > time_threshold:
                skipped_count += 1
                continue
            
            # Buscar odometry más cercana
            closest_odom_ts = min(odom_timestamps, key=lambda x: abs(x - theoretical_timestamp_ns))
            time_diff_odom = abs(closest_odom_ts - theoretical_timestamp_ns)
            
            if time_diff_odom > time_threshold:
                skipped_count += 1
                continue
            
            # Buscar IMU más cercana
            closest_imu_ts = min(imu_timestamps, key=lambda x: abs(x - theoretical_timestamp_ns))
            time_diff_imu = abs(closest_imu_ts - theoretical_timestamp_ns)
            
            if time_diff_imu > time_threshold:
                skipped_count += 1
                continue
            
            # Usar el timestamp real del rosbag (del joint_state, que es el más representativo)
            # Esto asegura que el timestamp corresponde a datos reales, no teóricos
            real_timestamp_ns = closest_js_ts
            
            # Obtener mensajes
            js_msg = joint_states_dict[closest_js_ts]
            odom_msg = odom_dict[closest_odom_ts]
            imu_msg = imu_dict[closest_imu_ts]
            
            # Guardar datos sincronizados con timestamp REAL del rosbag
            self.data['timestamp'].append(real_timestamp_ns / 1e9)  # Convertir a segundos
            self.data['frame_path'].append(f"frame_{frame_num:06d}.png")
            
            # Posición del lomo (trunk)
            # La odometría da la posición de base_footprint (punto de apoyo, z=0)
            # Necesitamos la posición de trunk (lomo) = base_footprint + transformación base_footprint->base_link
            # Como base_link y trunk son el mismo frame, solo necesitamos la transformación base_footprint->base_link
            pos_footprint = odom_msg.pose.pose.position
            
            # Obtener transformación base_footprint -> base_link para obtener altura del lomo
            trunk_pos = (pos_footprint.x, pos_footprint.y, pos_footprint.z)
            if tf_messages:
                tf_result = self.get_tf_transform(tf_messages, real_timestamp_ns, 'base_footprint', 'base_link', time_threshold=100000000)
                if tf_result:
                    translation, rotation = tf_result
                    # Aplicar transformación para obtener posición del lomo
                    trunk_pos = self.apply_transform((pos_footprint.x, pos_footprint.y, pos_footprint.z), translation, rotation)
            
            self.data['position_x'].append(trunk_pos[0])
            self.data['position_y'].append(trunk_pos[1])
            self.data['position_z'].append(trunk_pos[2])
            
            # Orientación (de IMU - más preciso para roll y pitch)
            orient = imu_msg.orientation
            roll, pitch, yaw = self.quaternion_to_euler(orient.x, orient.y, orient.z, orient.w)
            self.data['roll'].append(roll)
            self.data['pitch'].append(pitch)
            self.data['yaw'].append(yaw)
            
            # Articulaciones
            self.data['joint_names'].append(list(js_msg.name))
            self.data['joint_positions'].append(list(js_msg.position))
            self.data['joint_velocities'].append(list(js_msg.velocity))
            
            synced_count += 1
        
        print(f"✅ Sincronizados {synced_count} frames con datos del rosbag")
        if skipped_count > 0:
            print(f"⚠️  Omitidos {skipped_count} frames (sin datos sincronizados dentro del umbral)")
    
    def save_frame_mapping(self):
        """Guarda el mapeo de frames a timestamps basado en el dataset generado"""
        mapping_path = self.output_dir / "frame_to_timestamp_mapping.csv"
        print(f"💾 Guardando mapeo de frames a timestamps en {mapping_path.name}...")
        
        # Crear DataFrame desde los datos ya sincronizados
        df = pd.DataFrame({
            'frame_path': self.data['frame_path'],
            'timestamp': self.data['timestamp']
        })
        
        # Extraer número de frame del nombre
        df['frame_number'] = df['frame_path'].str.extract(r'frame_(\d+)\.png').astype(int)
        
        # Ordenar por frame number
        df = df.sort_values('frame_number')
        
        # Guardar mapeo
        with open(mapping_path, 'w') as f:
            f.write("frame_number,timestamp_ros_sec,timestamp_ros_nsec,timestamp_formatted\n")
            for _, row in df.iterrows():
                timestamp_sec = row['timestamp']
                ts_sec_part = int(timestamp_sec)
                ts_nsec_part = int((timestamp_sec - ts_sec_part) * 1e9)
                
                # Formatear timestamp para legibilidad
                from datetime import datetime
                dt = datetime.fromtimestamp(timestamp_sec)
                formatted = dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                f.write(f"{int(row['frame_number'])},{ts_sec_part},{ts_nsec_part},{formatted}\n")
        
        print(f"✅ Mapeo guardado: {len(df)} frames")
    
    def save_dataset(self):
        """Guarda el dataset en CSV"""
        print("💾 Guardando dataset...")
        
        # Convertir listas de joints a strings (para CSV)
        df = pd.DataFrame({
            'timestamp': self.data['timestamp'],
            'frame_path': self.data['frame_path'],
            'position_x': self.data['position_x'],
            'position_y': self.data['position_y'],
            'position_z': self.data['position_z'],
            'roll': self.data['roll'],
            'pitch': self.data['pitch'],
            'yaw': self.data['yaw'],
            'joint_names': [str(x) for x in self.data['joint_names']],
            'joint_positions': [str(x) for x in self.data['joint_positions']],
            'joint_velocities': [str(x) for x in self.data['joint_velocities']],
        })
        
        csv_path = self.output_dir / "dataset.csv"
        df.to_csv(csv_path, index=False)
        print(f"✅ Dataset guardado en: {csv_path}")
        
        # Estadísticas
        print("\n📊 Estadísticas del dataset:")
        print(f"  - Total de frames: {len(df)}")
        print(f"  - Duración: {df['timestamp'].max() - df['timestamp'].min():.2f}s")
        print(f"  - Joints detectados: {eval(df['joint_names'].iloc[0])}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 extract_dataset.py <path_to_rosbag>")
        print("Ejemplo: python3 extract_dataset.py ../gazebo-no-seas-malo/rosbags/marine_sim_20260116_172734")
        sys.exit(1)
    
    rosbag_path = sys.argv[1]
    rosbag_name = Path(rosbag_path).name
    output_dir = Path("datasets") / rosbag_name
    
    extractor = RosbagDatasetExtractor(rosbag_path, output_dir)
    extractor.process_rosbag()
    
    print(f"\n🎉 Dataset generado en: {output_dir}")


if __name__ == "__main__":
    main()
