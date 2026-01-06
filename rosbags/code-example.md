# Terminal 1: Lanzar la simulación
cd ~/gazebo-no-seas-malo
source install/setup.bash
ros2 launch go2_config gazebo.launch.py rviz:=true

# Terminal 2: Lanzar simulador marino
cd ~/gazebo-no-seas-malo
source install/setup.bash
ros2 run go2_tools marine_platform_simulator

# Terminal 3: Lanzar dron con cámara
cd ~/gazebo-no-seas-malo
source install/setup.bash
ros2 launch drone drone.launch.py

# Terminal 4: Ver topics activos y grabarlos en bag
ros2 topic list
cd ~/gazebo-no-seas-malo

ros2 bag record \
  /body_pose \
  /go2/pose_rphz_cmd \
  /marine_platform/debug_state \
  /joint_states \
  /odom \
  /tf \
  /tf_static \
  /clock \
  /cmd_vel \
  /robot_description \
  /drone/camera/image_raw \
  /drone/camera/camera_info \
  /drone/pose \
  /drone/robot_description \
  -o rosbags/marine_simulation_$(date +%Y%m%d_%H%M%S)