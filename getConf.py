#!/usr/bin/env python3
import napalm
import csv
import datetime
import os

Save_Dir = "getconfig_files"

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

def get_config(device_info):
    driver = napalm.get_network_driver("ios")

    try:
        device = driver(
            hostname=device_info["ip"],
            username=device_info["username"],
            password=device_info["password"],
            optional_args={"port": 22}
        )

        print(f"Connecting to {device_info['hostname']} ({device_info['ip']}) ...")
        device.open()

        config = device.get_config()
        running_config = config["running"] 

        timestamp = datetime.datetime.utcnow().isoformat(timespec='seconds') + "Z"
        filename = f"{device_info['hostname']}_{timestamp}.txt"

        filepath = os.path.join(Save_Dir, filename)


        with open(filepath, "w") as file:
            file.write(running_config)

        print(f"Configuration saved: {filepath}")

        device.close()  
        return filepath

    except Exception as e:
        print(f"Failed to connect to {device_info['hostname']}: {str(e)}")
        return None

def main():
    csv_file = "sshInfo.csv"
    devices = ssh_info(csv_file)

    saved_files = []
    for device in devices:
        filename = get_config(device)
        if filename:
            saved_files.append(filename)

    
    print("\nFiles saved:")
    for file in saved_files:
        print(file)

if __name__ == "__main__":
    main()

