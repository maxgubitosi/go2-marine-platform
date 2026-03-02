#!/usr/bin/env python3
"""
Test if the Go2 sport RPC service exists by checking
publication_matched on rt/api/sport/request and also
trying to subscribe to rt/api/sport/response.
Also tries alternate topic names.
"""
import os, sys, time
os.environ.pop('CYCLONEDDS_URI', None)

from cyclonedds.domain import DomainParticipant, Domain
from cyclonedds.sub import DataReader
from cyclonedds.pub import DataWriter
from cyclonedds.topic import Topic
from cyclonedds.core import Listener, DDSException
from cyclonedds.internal import dds_c_t
from cyclonedds.util import duration

from unitree_sdk2py.idl.unitree_api.msg.dds_ import Request_ as Request
from unitree_sdk2py.idl.unitree_api.msg.dds_ import Response_ as Response
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_

def main():
    iface = sys.argv[1] if len(sys.argv) > 1 else "enp2s0"
    
    config = f'''<?xml version="1.0" encoding="UTF-8" ?>
    <CycloneDDS>
        <Domain Id="any">
            <General>
                <Interfaces>
                    <NetworkInterface name="{iface}" priority="default" multicast="default"/>
                </Interfaces>
            </General>
        </Domain>
    </CycloneDDS>'''
    
    domain = Domain(0, config)
    dp = DomainParticipant(0)
    
    pub_matched = {}
    
    def on_pub_matched(writer, status):
        pub_matched['count'] = status.current_count
        print(f"  [PubMatched] current_count={status.current_count}, total={status.total_count}")
    
    # === Test writer on rt/api/sport/request ===
    print("=== Testing rt/api/sport/request (writer, 5s) ===")
    pub_matched['count'] = 0
    topic_req = Topic(dp, "rt/api/sport/request", Request)
    writer_req = DataWriter(dp, topic_req, listener=Listener(on_publication_matched=on_pub_matched))
    time.sleep(5)
    print(f"  publication_matched_count = {pub_matched['count']}")
    
    # === Test reader on rt/api/sport/response ===
    print("\n=== Testing rt/api/sport/response (reader, 3s) ===")
    topic_resp = Topic(dp, "rt/api/sport/response", Response)
    reader_resp = DataReader(dp, topic_resp)
    time.sleep(1)
    try:
        sample = reader_resp.take_one(timeout=duration(seconds=3))
        if sample:
            print(f"  ✓ Got response: api_id={sample.header.identity.api_id}")
        else:
            print(f"  ✗ No response data")
    except:
        print(f"  ✗ No response data (timeout)")
    
    # === Try alternate sport topic names ===
    alt_topics = [
        "rt/sportmodestate",
        "rt/lf/sportmodestate",
        "rt/api/sport_mode/request",
        "rt/api/motion/request",
    ]
    print(f"\n=== Testing alternate SportModeState topics (3s each) ===")
    for tname in alt_topics:
        try:
            t = Topic(dp, tname, SportModeState_)
            r = DataReader(dp, t)
            time.sleep(1)
            s = None
            try:
                s = r.take_one(timeout=duration(seconds=2))
            except:
                pass
            status = f"✓ mode={s.mode}" if s else "✗ no data"
            print(f"  {tname}: {status}")
        except Exception as e:
            print(f"  {tname}: error - {e}")
    
    # === Check if Go2 lowcmd is writable (publication matched) ===
    from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_
    print(f"\n=== Testing rt/lowcmd writer (3s) ===")
    pub_matched['count'] = 0
    topic_lowcmd = Topic(dp, "rt/lowcmd", LowCmd_)
    writer_lowcmd = DataWriter(dp, topic_lowcmd, listener=Listener(on_publication_matched=on_pub_matched))
    time.sleep(3)
    print(f"  rt/lowcmd publication_matched_count = {pub_matched['count']}")
    
    pub_matched['count'] = 0
    topic_lowcmd2 = Topic(dp, "rt/lowcmd2", LowCmd_)
    writer_lowcmd2 = DataWriter(dp, topic_lowcmd2, listener=Listener(on_publication_matched=on_pub_matched))
    time.sleep(3)
    print(f"  rt/lowcmd2 publication_matched_count = {pub_matched['count']}")

    print("\n=== DONE ===")

if __name__ == "__main__":
    main()
