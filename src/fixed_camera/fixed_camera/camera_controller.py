#!/usr/bin/env python3
"""
Fixed Camera Controller Node

Publica la pose fija de la cámara y el TF correspondiente.
La cámara NO se mueve — queda estática en la posición configurada.
Esto garantiza coherencia entre lo que se ve en Gazebo y los datos de TF/pose.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped
from tf2_ros import StaticTransformBroadcaster


class FixedCameraController(Node):
    def __init__(self):
        super().__init__('camera_controller')

        # Parámetros de posición fija
        self.declare_parameter('position_x', 0.0)
        self.declare_parameter('position_y', 0.0)
        self.declare_parameter('position_z', 2.0)
        self.declare_parameter('publish_rate', 10.0)  # Hz

        self.pos_x = self.get_parameter('position_x').value
        self.pos_y = self.get_parameter('position_y').value
        self.pos_z = self.get_parameter('position_z').value
        publish_rate = self.get_parameter('publish_rate').value

        # Publicador de pose
        self.pose_pub = self.create_publisher(PoseStamped, '/fixed_camera/pose', 10)

        # TF estático — se publica una sola vez y no cambia
        self.static_tf_broadcaster = StaticTransformBroadcaster(self)
        self._publish_static_tf()

        # Timer para publicar pose periódicamente (para que otros nodos puedan suscribirse)
        self.timer = self.create_timer(1.0 / publish_rate, self._publish_pose)

        self.get_logger().info(
            f'FixedCameraController started – '
            f'position=({self.pos_x}, {self.pos_y}, {self.pos_z})'
        )

    def _publish_static_tf(self):
        """Publica TF estático world → camera_base_link (una sola vez)."""
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'world'
        t.child_frame_id = 'camera_base_link'
        t.transform.translation.x = self.pos_x
        t.transform.translation.y = self.pos_y
        t.transform.translation.z = self.pos_z
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0
        self.static_tf_broadcaster.sendTransform(t)

    def _publish_pose(self):
        """Publica la pose fija como PoseStamped."""
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'world'
        msg.pose.position.x = self.pos_x
        msg.pose.position.y = self.pos_y
        msg.pose.position.z = self.pos_z
        msg.pose.orientation.x = 0.0
        msg.pose.orientation.y = 0.0
        msg.pose.orientation.z = 0.0
        msg.pose.orientation.w = 1.0
        self.pose_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = FixedCameraController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
