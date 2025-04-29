#!/usr/bin/env python3
import napalm
import csv
import datetime
import os

Save_Dir = "getconfig_files"

# SSH connection
def ssh_info(csv_file):
    devices = []
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            devices.append({
                "hostname": row["hostname"],
                "ip": row["ip"],
                "username": row["username"],
                "password": row["password"]
            })
    return devices

# Pull configuration file and save to "getconfig_files"
def get_save_config(selected_routers):
    if not os.path.exists(Save_Dir):
        os.makedirs(Save_Dir)

    csv_file = "sshInfo.csv"
    devices = ssh_info(csv_file)

    saved_files = []

    for device in devices:
        hostname = device["hostname"]

        if "All" in selected_routers or hostname in selected_routers:
            driver = napalm.get_network_driver("ios")
            try:
                device_conn = driver(
                    hostname=device["ip"],
                    username=device["username"],
                    password=device["password"],
                    optional_args={"port": 22}
                )

                print(f"Connecting to {hostname} ({device['ip']}) ...")
                device_conn.open()

                config = device_conn.get_config()
                running_config = config["running"]

                timestamp = datetime.datetime.utcnow().isoformat(timespec='seconds') + "Z"
                safe_timestamp = timestamp.replace(':', '-')  
                filename = f"{hostname}_{safe_timestamp}.txt"

                filepath = os.path.join(Save_Dir, filename)

                with open(filepath, "w") as file:
                    file.write(running_config)

                print(f"Configuration saved: {filepath}")
                saved_files.append(filename)

                device_conn.close()

            except Exception as e:
                print(f"Failed to connect to {hostname}: {str(e)}")

    return saved_files

