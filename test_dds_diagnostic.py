#!/usr/bin/env python3
"""
Comprehensive Go2 DDS diagnostic.
Tests:
1. Can we subscribe to Go2's state topics via SDK2?
2. Can we discover what DDS topics the Go2 advertises?
3. Does the sport service exist at all?
"""
import sys
import os
import time

# Ensure no CYCLONEDDS_URI pollution
os.environ.pop('CYCLONEDDS_URI', None)

from cyclonedds.domain import DomainParticipant, Domain
from cyclonedds.sub import DataReader
from cyclonedds.topic import Topic
from cyclonedds.core import Listener, DDSException
from cyclonedds.builtin import DcpsParticipant, DcpsTopic, DcpsEndpoint
from cyclonedds.util import duration

# SDK2 types
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_

def main():
    iface = sys.argv[1] if len(sys.argv) > 1 else "enp2s0"
    
    # Use SDK2's channel config
    config = f'''<?xml version="1.0" encoding="UTF-8" ?>
    <CycloneDDS>
        <Domain Id="any">
            <General>
                <Interfaces>
                    <NetworkInterface name="{iface}" priority="default" multicast="default"/>
                </Interfaces>
            </General>
            <Tracing>
                <Verbosity>warning</Verbosity>
                <OutputFile>/tmp/cdds_diag.LOG</OutputFile>
            </Tracing>
        </Domain>
    </CycloneDDS>'''
    
    print(f"[DIAG] Creating DDS domain on {iface}...")
    domain = Domain(0, config)
    dp = DomainParticipant(0)
    
    # === 1. Try subscribing to known Go2 topics ===
    print("\n=== SUBSCRIBING TO Go2 TOPICS (3s each) ===")
    
    # Try rt/sportmodestate
    print("[DIAG] Trying rt/sportmodestate...")
    try:
        topic_sport = Topic(dp, "rt/sportmodestate", SportModeState_)
        reader_sport = DataReader(dp, topic_sport)
        time.sleep(2)
        sample = None
        try:
            sample = reader_sport.take_one(timeout=duration(seconds=3))
        except TimeoutError:
            pass
        except Exception as e:
            print(f"  Error: {e}")
        if sample:
            print(f"  ✓ Got SportModeState! mode={sample.mode}, gait_type={sample.gait_type}")
        else:
            print(f"  ✗ No data on rt/sportmodestate")
    except Exception as e:
        print(f"  Error creating topic: {e}")
    
    # Try rt/lowstate  
    print("[DIAG] Trying rt/lowstate...")
    try:
        topic_low = Topic(dp, "rt/lowstate", LowState_)
        reader_low = DataReader(dp, topic_low)
        time.sleep(1)
        sample = None
        try:
            sample = reader_low.take_one(timeout=duration(seconds=3))
        except TimeoutError:
            pass
        except Exception as e:
            print(f"  Error: {e}")
        if sample:
            print(f"  ✓ Got LowState! tick={sample.tick}")
        else:
            print(f"  ✗ No data on rt/lowstate")
    except Exception as e:
        print(f"  Error creating topic: {e}")
    
    # Try rt/lf/lowstate (alternate path)
    print("[DIAG] Trying rt/lf/lowstate...")
    try:
        topic_lflow = Topic(dp, "rt/lf/lowstate", LowState_)
        reader_lflow = DataReader(dp, topic_lflow)
        time.sleep(1)
        sample = None
        try:
            sample = reader_lflow.take_one(timeout=duration(seconds=3))
        except TimeoutError:
            pass
        except Exception as e:
            print(f"  Error: {e}")
        if sample:
            print(f"  ✓ Got LowState on rt/lf/lowstate! tick={sample.tick}")
        else:
            print(f"  ✗ No data on rt/lf/lowstate")
    except Exception as e:
        print(f"  Error creating topic: {e}")

    print("\n=== DIAGNOSTIC COMPLETE ===")

if __name__ == "__main__":
    main()
