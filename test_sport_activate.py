#!/usr/bin/env python3
"""
Test activating sport mode via MotionSwitcherClient,
then sending sport commands.
"""
import os, sys, time
os.environ.pop('CYCLONEDDS_URI', None)

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient
from unitree_sdk2py.go2.sport.sport_client import SportClient

def main():
    iface = sys.argv[1] if len(sys.argv) > 1 else "enp2s0"
    print(f"[INFO] Initializing on {iface}...")
    ChannelFactoryInitialize(0, iface)
    time.sleep(1)

    # === 1. Initialize MotionSwitcherClient ===
    print("\n[STEP 1] Initializing MotionSwitcherClient...")
    msc = MotionSwitcherClient()
    msc.SetTimeout(5.0)
    msc.Init()
    time.sleep(1)

    # === 2. Check current mode ===
    print("\n[STEP 2] Checking current mode...")
    code, result = msc.CheckMode()
    print(f"  CheckMode returned: code={code}, result={result}")
    
    if code != 0:
        print(f"  ERROR: CheckMode failed with code {code}")
        return

    current_mode = result.get('name', '') if result else ''
    print(f"  Current mode: '{current_mode}'")
    
    # === 3. Select sport mode ("normal") ===
    if current_mode != 'normal':
        print(f"\n[STEP 3] Selecting 'normal' (sport) mode...")
        code, _ = msc.SelectMode("normal")
        print(f"  SelectMode('normal') returned: code={code}")
        
        if code != 0:
            print(f"  ERROR: SelectMode failed with code {code}")
            # Try with alternate name
            print("  Trying 'advanced_sport'...")
            code, _ = msc.SelectMode("advanced_sport")
            print(f"  SelectMode('advanced_sport') returned: code={code}")
        
        print("  Waiting 3s for sport mode to start...")
        time.sleep(3)
    else:
        print("\n[STEP 3] Already in 'normal' mode, skipping SelectMode")
    
    # === 4. Verify mode changed ===
    print("\n[STEP 4] Re-checking mode...")
    code, result = msc.CheckMode()
    print(f"  CheckMode returned: code={code}, result={result}")
    
    # === 5. Try sport client ===
    print("\n[STEP 5] Initializing SportClient...")
    sc = SportClient()
    sc.SetTimeout(10.0)
    sc.Init()
    time.sleep(2)
    
    print("\n[STEP 6] Sending RecoveryStand...")
    ret = sc.RecoveryStand()
    print(f"  RecoveryStand returned: {ret}")
    
    if ret == 3102:
        print("  Still error 3102 - sport service is not running")
        print("  The motion_switcher might need to activate sport first")
    else:
        time.sleep(3)
        print("\n[STEP 7] Sending BalanceStand...")
        ret = sc.BalanceStand()
        print(f"  BalanceStand returned: {ret}")
        
        time.sleep(2)
        print("\n[STEP 8] Sending Euler(0.05, 0, 0) - slight roll...")
        ret = sc.Euler(0.05, 0.0, 0.0)
        print(f"  Euler returned: {ret}")
        
        time.sleep(2)
        print("\n[STEP 9] Reset Euler(0, 0, 0)...")
        ret = sc.Euler(0.0, 0.0, 0.0)
        print(f"  Euler returned: {ret}")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()
