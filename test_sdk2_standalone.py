#!/usr/bin/env python3
"""
Standalone test: NO ROS2, ONLY unitree_sdk2py.
Tests if we can reach the Go2 sport service via DDS.
Run: python3 test_sdk2_standalone.py enp2s0
"""
import sys
import os
import time

# CRITICAL: unset CYCLONEDDS_URI to prevent conflicts
if 'CYCLONEDDS_URI' in os.environ:
    print(f"[WARN] Unsetting CYCLONEDDS_URI: {os.environ['CYCLONEDDS_URI'][:60]}...")
    del os.environ['CYCLONEDDS_URI']

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient

def main():
    iface = sys.argv[1] if len(sys.argv) > 1 else "enp2s0"
    print(f"[INFO] Initializing SDK2 on interface: {iface}")
    print(f"[INFO] CYCLONEDDS_URI in env: {'CYCLONEDDS_URI' in os.environ}")
    
    ChannelFactoryInitialize(0, iface)
    print("[INFO] ChannelFactory initialized")
    
    client = SportClient()
    client.SetTimeout(10.0)
    client.Init()
    print("[INFO] SportClient initialized, waiting 2s for DDS discovery...")
    time.sleep(2)
    
    print("[TEST] Sending RecoveryStand...")
    ret = client.RecoveryStand()
    print(f"[TEST] RecoveryStand returned: {ret}")
    
    time.sleep(2)
    
    print("[TEST] Sending BalanceStand...")
    ret = client.BalanceStand()
    print(f"[TEST] BalanceStand returned: {ret}")
    
    time.sleep(2)
    
    print("[TEST] Sending Euler(0, 0, 0)...")
    ret = client.Euler(0.0, 0.0, 0.0)
    print(f"[TEST] Euler returned: {ret}")
    
    print("[DONE] Test complete.")

if __name__ == "__main__":
    main()
