#!/usr/bin/env python3
import csv
from napalm import get_network_driver

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


def conf_ospf(router, ospf_process, ospf_area, loopback, csv_file="sshInfo.csv"):
    devices = ssh_info(csv_file)  
    device_info = next((d for d in devices if d["hostname"] == router), None)

    if not device_info:
        print(f"Error: Router {router} not found in {csv_file}")
        return False

    driver = get_network_driver("ios")

    device = driver(
        hostname=device_info["ip"],
        username=device_info["username"],
        password=device_info["password"]
    )

    routerip = device_info["ip"]

    try:
        print(f"Connecting to {router} ({device_info['ip']})...")
        print("Device Info:", device_info)
        print("Open connection")
        device.open()
        print(f"Connected to {router} ({device_info['ip']}) successfully!")

        config_commands = [
            f"router ospf {ospf_process}",
            f"network {routerip} 0.0.0.0 area {ospf_area}"
            f"network {loopback} 0.0.0.0 area {ospf_area}",
            "auto-cost reference-bandwidth 10000",
            "exit"
        ]

        if router in ["R2-Zhang", "R4-Zhang"]:
            config_commands.append(f"network 172.16.1.0 0.0.0.255 area 0")
            config_commands.append(f"network 198.51.100.0 0.0.0.255 area 0")

        print("ospf configuring...")
        device.load_merge_candidate(config="\n".join(config_commands))

        device.close()

        print(f"OSPF configured on {router} successfully!")
        return True
    except Exception as e:
        print(f"Error configuring OSPF on {router}: {e}")
        return False

if __name__ == "__main__":
    conf_ospf("sshInfo.csv")
