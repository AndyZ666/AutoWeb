#!/usr/bin/env python3
from napalm import get_network_driver
import sqlite3
import difflib
import os
import glob
from datetime import datetime

# PUll information from ospf database
def get_routers_from_db():
    conn = sqlite3.connect('ospf_config.db')
    cursor = conn.cursor()
    cursor.execute('SELECT hostname, mgmt_ip, username, password FROM ospf GROUP BY router')

    routers = {}
    for hostname, ip, username, password in cursor.fetchall():
        routers[hostname] = {
            "hostname": ip,
            "username": username,
            "password": password
        }
    conn.close()
    return routers

# Obtain the lastest configuration file for each router
def get_latest_saved_config(router_name):
    pattern = f"getconfig_files/{router_name}_*.txt"
    files = glob.glob(pattern)
    if not files:
        return []
    # sort by lastest datetime
    latest_file = max(files, key=os.path.getmtime)
    with open(latest_file, "r") as f:
        return f.readlines()

# Pull configuration file
def get_running_config(router_info):
    driver = get_network_driver("ios")
    device = driver(
        hostname=router_info["hostname"],
        username=router_info["username"],
        password=router_info["password"],
        optional_args={"transport": "ssh"}
    )
    device.open()
    config = device.get_config()["running"]
    device.close()
    return config

# Compare configuration file
def compare_configs(saved_config, running_config_lines):
    diff = difflib.unified_diff(
        saved_config,
        running_config_lines,
        fromfile="Saved Config",
        tofile="Running Config",
        lineterm=""
    )
    return list(diff)

# Generate all different config for every routers
def generate_all_diffs():
    routers = get_routers_from_db()
    diffs = {}

    if not os.path.exists("diff_files"):
        os.makedirs("diff_files")

    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    for router_name, router_info in routers.items():
        try:
            saved_config = get_latest_saved_config(router_name)
            running_config = get_running_config(router_info)
            running_config_lines = running_config.splitlines(keepends=True)

            diff_result = compare_configs(saved_config, running_config_lines)

            diffs[router_name] = diff_result

            # save diff configuration as file and save to diff_files
            diff_filename = f"diff_files/{router_name}_diff_{now}.txt"
            with open(diff_filename, "w") as f:
                f.write(f"Diff generated at: {now}\n\n")
                f.writelines(diff_result)

        except Exception as e:
            diffs[router_name] = [f"Error fetching diff for {router_name}: {e}"]

    return diffs
