#!/usr/bin/env python3
import sqlite3
import napalm
import re
import subprocess
from prettytable import PrettyTable

# IP address testing
def is_valid_ip(ip):
    pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if pattern.match(ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    return False

# Test SSH connection
def test_ssh_connection(mgmt_ip, username, password):
    try:
        driver = napalm.get_network_driver("ios")
        device = driver(
            hostname=mgmt_ip,
            username=username,
            password=password,
            optional_args={"port": 22}
        )
        device.open()
        device.close()
        return True
    except:
        return False

# Save OSPF configuration information
def save_ospf_info(router, hostname, mgmt_ip, username, password, ospf_process, ospf_area, loopback):
    conn = sqlite3.connect('ospf_config.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ospf (
            router TEXT,
            hostname TEXT,
            mgmt_ip TEXT,
            username TEXT,
            password TEXT,
            ospf_process TEXT,
            ospf_area TEXT,
            loopback TEXT
        )
    ''')
    cursor.execute('''
        INSERT INTO ospf (router, hostname, mgmt_ip, username, password, ospf_process, ospf_area, loopback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (router, hostname, mgmt_ip, username, password, ospf_process, ospf_area, loopback))
    conn.commit()
    conn.close()

# Define OSPF area number
def get_area_for_ip(ip):
    if ip.startswith('172.16.1.'):
        return '0'
    elif ip.startswith('198.51.'):
        return '1'
    elif ip.startswith('10.0.0.') or ip.startswith('20.0.0.') or ip.startswith('30.0.0.') or ip.startswith('40.0.0.'):
        return '0'
    else:
        return '0'

# OSPF configuration process
def configure_ospf_from_db(router):
    conn = sqlite3.connect('ospf_config.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ospf WHERE router = ?', (router,))
    result = cursor.fetchone()
    conn.close()

    interface_list = []

    if result:
        _, hostname, mgmt_ip, username, password, ospf_process, ospf_area, loopback = result

        driver = napalm.get_network_driver("ios")
        device = driver(
            hostname=mgmt_ip,
            username=username,
            password=password,
            optional_args={"port": 22}
        )
        device.open()

        interfaces = device.get_interfaces_ip()

        commands = [f"router ospf {ospf_process}"]

        if loopback:
            loopback_area = get_area_for_ip(loopback)
            commands.append(f"network {loopback} 0.0.0.0 area {loopback_area}")
            interface_list.append({
                "interface": "Loopback0",
                "ip": loopback,
                "area": loopback_area
            })

        for iface, data in interfaces.items():
            if "Loopback" not in iface and "ipv4" in data:
                for ip in data["ipv4"]:
                    area = get_area_for_ip(ip)
                    commands.append(f"network {ip} 0.0.0.0 area {area}")
                    interface_list.append({
                        "interface": iface,
                        "ip": ip,
                        "area": area
                    })
                    
            if router in ["R2-Zhang", "R4-Zhang"] and "Loopback" not in iface:
                        commands.append(f"interface {iface}")
                        commands.append("ip ospf cost 10")
                        commands.append("exit")
                    

        device.load_merge_candidate(config="\n".join(commands))
        device.commit_config()
        device.close()

    return interface_list

# Interfaces and IP table by PrettyTable
def get_interfaces_prettytable(router):
    conn = sqlite3.connect('ospf_config.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ospf WHERE router = ?', (router,))
    result = cursor.fetchone()
    conn.close()

    if result:
        _, _, mgmt_ip, username, password, _, _, _ = result
        driver = napalm.get_network_driver("ios")
        device = driver(
            hostname=mgmt_ip,
            username=username,
            password=password,
            optional_args={"port": 22}
        )
        device.open()
        interfaces = device.get_interfaces_ip()
        device.close()

        table = PrettyTable()
        table.field_names = ["Interface", "IP Address", "Valid Format?"]

        for iface, data in interfaces.items():
            if "ipv4" in data:
                for ip in data["ipv4"]:
                    valid = "Yes" if is_valid_ip(ip) else "No"
                    table.add_row([iface, ip, valid])

        return table.get_string()
    else:
        return "No Interface Info Found."

# Exclude Loopback0 for R1
def get_all_loopbacks(exclude_router="R1"):
    conn = sqlite3.connect('ospf_config.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT router, loopback FROM ospf')
    records = cursor.fetchall()
    conn.close()

    loopbacks = []
    for router, ip in records:
        if router != exclude_router and ip:
            loopbacks.append(ip)
    return loopbacks

# Ping loopback IPs from
def ping_loopbacks_from_r1(loopbacks):
    conn = sqlite3.connect('ospf_config.db')
    cursor = conn.cursor()
    cursor.execute('SELECT mgmt_ip, username, password FROM ospf WHERE router = "R1"')
    result = cursor.fetchone()
    conn.close()

    if not result:
        return [], []

    mgmt_ip, username, password = result

    driver = napalm.get_network_driver("ios")
    device = driver(
        hostname=mgmt_ip,
        username=username,
        password=password,
        optional_args={"port": 22}
    )

    device.open()

    success_ping = []
    failed_ping = []

    for ip in loopbacks:
        try:
            ping_result = device.cli([f"ping {ip}"])
            output = ping_result[f"ping {ip}"]
            if "Success rate is 100 percent" in output:
                success_ping.append(ip)
            else:
                failed_ping.append(ip)
        except Exception:
            failed_ping.append(ip)

    device.close()

    return success_ping, failed_ping

