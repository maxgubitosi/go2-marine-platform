#!/usr/bin/env python3
"""
Script para extraer dataset de rosbags de simulación marina.
Genera: frame de video + posición del robot + ángulos de articulaciones
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
import yaml
import math


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
        
        # Extraer datos de topics
        print("📥 Extrayendo joint_states...")
        joint_states = self.extract_messages('/joint_states', JointState)
        
        print("📥 Extrayendo odometry...")
        odom_messages = self.extract_messages('/odom', Odometry)
        
        print("📥 Extrayendo IMU data...")
        imu_messages = self.extract_messages('/imu/data', Imu)
        
        print(f"✅ Extraídos {len(joint_states)} joint_states, {len(odom_messages)} odom, {len(imu_messages)} imu")
        
        # Sincronizar datos
        self.synchronize_data(joint_states, odom_messages, imu_messages)
        
        # Guardar dataset
        self.save_dataset()
    
    def synchronize_data(self, joint_states, odom_messages, imu_messages, time_threshold=50000000):
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
            
            # Posición (de odometry)
            pos = odom_msg.pose.pose.position
            self.data['position_x'].append(pos.x)
            self.data['position_y'].append(pos.y)
            self.data['position_z'].append(pos.z)
            
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
