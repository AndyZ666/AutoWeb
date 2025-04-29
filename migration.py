#!/usr/bin/env python3
import napalm
import sqlite3
import time
import re
from datetime import datetime
import os

# Define a traffic threshold in bytes
TRAFFIC_THRESHOLD = 1000

# Function to check if there is traffic on a specific interface
def check_traffic(device, interface):
    counters_before = device.get_interfaces_counters()
    time.sleep(3)  # Wait a few seconds to observe traffic changes
    counters_after = device.get_interfaces_counters()

    rx_diff = counters_after[interface]["rx_octets"] - counters_before[interface]["rx_octets"]
    tx_diff = counters_after[interface]["tx_octets"] - counters_before[interface]["tx_octets"]

    if rx_diff > TRAFFIC_THRESHOLD or tx_diff > TRAFFIC_THRESHOLD:
        return True
    else:
        return False

# Main migration function
def perform_migration():
    # Connect to database to get R4 information
    conn = sqlite3.connect('ospf_config.db')
    cursor = conn.cursor()
    cursor.execute('SELECT hostname, mgmt_ip, username, password FROM ospf WHERE router = ?', ("R4",))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return "Router R4-Zhang information not found in database."

    hostname, mgmt_ip, username, password = result

    try:
        driver = napalm.get_network_driver("ios")
        device = driver(
            hostname=mgmt_ip,
            username=username,
            password=password,
            optional_args={"port": 22}
        )
        device.open()

        # Check for traffic on the link to SW2 (assuming it's FastEthernet1/0)
        interface = "FastEthernet1/0"

        if check_traffic(device, interface):
            device.close()
            return "Traffic detected on R4-SW2 link, cannot proceed with migration."

        # If no traffic, proceed to shutdown the interface and configure motd
        commands = [
            f"interface {interface}",
            "shutdown",
            "exit",
            "banner motd ^Change made for migration in Lab 6^"
        ]

        device.load_merge_candidate(config="\n".join(commands))
        device.commit_config()
        device.close()

        return "Migration completed successfully"

    except Exception as e:
        return f"Migration failed due to error: {str(e)}"

# ensure 'diff' folder exists for storing any future differences (if needed)
if not os.path.exists('diff_files'):
    os.makedirs('diff_files')

