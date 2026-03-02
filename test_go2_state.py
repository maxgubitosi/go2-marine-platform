#!/usr/bin/env python3
"""
Test sport service on multiple DDS domains and also test
if MotionSwitcherClient works.
Also check what the lowstate IMU reports (confirms Go2 state).
"""
import os, sys, time
os.environ.pop('CYCLONEDDS_URI', None)

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_

# Also try motion_switcher 
sys.path.insert(0, '/tmp/unitree_sdk2_python')

def test_lowstate_details():
    """Read lowstate to check robot's current mode/state"""
    print("=== Reading LowState details ===")
    
    sub = ChannelSubscriber("rt/lowstate", LowState_)
    sub.Init()
    time.sleep(1)
    
    sample = sub.Read(timeout=3.0)
    if sample:
        print(f"  tick: {sample.tick}")
        print(f"  IMU quaternion: w={sample.imu_state.quaternion[0]:.3f}, "
              f"x={sample.imu_state.quaternion[1]:.3f}, "
              f"y={sample.imu_state.quaternion[2]:.3f}, "
              f"z={sample.imu_state.quaternion[3]:.3f}")
        print(f"  IMU rpy: roll={sample.imu_state.rpy[0]:.3f}, "
              f"pitch={sample.imu_state.rpy[1]:.3f}, "
              f"yaw={sample.imu_state.rpy[2]:.3f}")
        print(f"  Motor 0 (FR_hip) q={sample.motor_state[0].q:.3f}")
        print(f"  Motor 1 (FR_thigh) q={sample.motor_state[1].q:.3f}")
        print(f"  Motor 2 (FR_calf) q={sample.motor_state[2].q:.3f}")
        print(f"  power_v={sample.power_v:.1f}V, power_a={sample.power_a:.1f}A")
        
        # Check if sport mode is active by looking at motor states
        # If all motors have non-zero q values in standing config, sport is active
        all_q = [sample.motor_state[i].q for i in range(12)]
        print(f"  All joint positions: {[f'{q:.2f}' for q in all_q]}")
    else:
        print("  ✗ Could not read lowstate")
    sub.Close()

def test_motion_switcher_service():
    """Check if motion_switcher service exists"""
    print("\n=== Testing motion_switcher service ===")
    
    from cyclonedds.domain import DomainParticipant
    from cyclonedds.pub import DataWriter
    from cyclonedds.topic import Topic
    from cyclonedds.core import Listener
    from cyclonedds.internal import dds_c_t
    from unitree_sdk2py.idl.unitree_api.msg.dds_ import Request_ as Request
    
    dp = DomainParticipant(0)
    
    matched = {'count': 0}
    def on_match(w, s):
        matched['count'] = s.current_count
    
    topic = Topic(dp, "rt/api/motion_switcher/request", Request)
    writer = DataWriter(dp, topic, listener=Listener(on_publication_matched=on_match))
    time.sleep(3)
    print(f"  rt/api/motion_switcher/request matched: {matched['count']}")

def main():
    iface = sys.argv[1] if len(sys.argv) > 1 else "enp2s0"
    print(f"Initializing on {iface} (domain 0)...")
    ChannelFactoryInitialize(0, iface)
    time.sleep(1)
    
    test_lowstate_details()
    test_motion_switcher_service()
    
    print("\n=== SUMMARY ===")
    print("If motion_switcher matched=0 AND sport service matched=0:")
    print("  → This Go2 is Air/Pro without development board services")
    print("  → Need alternative control method (WebRTC, or lowcmd with mode release)")

if __name__ == "__main__":
    main()
