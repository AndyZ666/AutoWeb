#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3
import ospf_conf 
from getConf import get_save_config
from diff_config import generate_all_diffs
import csv
from datetime import datetime
from migration import perform_migration  

app = Flask(__name__)

conf_Dir = "getconfig_files"
ospf_DB = "ospf_config.db"

@app.route('/')
def home():
    return render_template('home.html')

# Get Config Section
@app.route('/getconfig', methods=["GET", "POST"])
def get_config():
    if request.method == "POST":
        selected_routers = request.form.getlist('routers')
        filenames = get_save_config(selected_routers)
        return render_template('config_result.html', filenames=filenames)
    
    # show router selection
    routers = []
    with open("sshInfo.csv", mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            routers.append(row["hostname"])

    return render_template('getconfig.html', routers=routers)

#OSPF home page
@app.route('/ospf', methods=["GET", "POST"])
def select_router():
    if request.method == "POST":
        selected_router = request.form.get("router")
        return redirect(url_for('ospf_ssh', router=selected_router))
    return render_template('ospf_home.html')

# SSH connction information collection page
@app.route('/ospf/<router>/ssh', methods=["GET", "POST"])
def ospf_ssh(router):
    if request.method == "POST":
        hostname = request.form["hostname"]
        mgmt_ip = request.form["mgmt_ip"]
        username = request.form["username"]
        password = request.form["password"]

        success = ospf_conf.test_ssh_connection(mgmt_ip, username, password)
        if success:
            return redirect(url_for('ospf_config', router=router, hostname=hostname, mgmt_ip=mgmt_ip, username=username, password=password))
        else:
            return "SSH Connection Failed. Please check your credentials."

    return render_template('ospf_ssh.html', router=router)

# OSPF configuration information collection and process
@app.route('/ospf/<router>/config', methods=["GET", "POST"])
def ospf_config(router):
    hostname = request.args.get("hostname")
    mgmt_ip = request.args.get("mgmt_ip")
    username = request.args.get("username")
    password = request.args.get("password")

    if request.method == "POST":
        ospf_process = request.form["ospf_process"]
        ospf_area = request.form["ospf_area"]
        loopback = request.form["loopback"]

        ospf_conf.save_ospf_info(router, hostname, mgmt_ip, username, password, ospf_process, ospf_area, loopback)
        ospf_interfaces = ospf_conf.configure_ospf_from_db(router)
        table_output = ospf_conf.get_interfaces_prettytable(router)
        all_loopbacks = ospf_conf.get_all_loopbacks()
        success_ping, failed_ping = ospf_conf.ping_loopbacks_from_r1(all_loopbacks)

        return render_template('ospf_result.html',
                               router=router,
                               table_output=table_output,
                               success_ping=success_ping,
                               failed_ping=failed_ping,
                               ospf_interfaces=ospf_interfaces)

    return render_template('ospf_config.html', router=router, hostname=hostname, mgmt_ip=mgmt_ip, username=username, password=password)

# Auxiliary function collection loopback IP
def get_all_loopbacks():
    conn = sqlite3.connect('ospf_config.db')
    cursor = conn.cursor()
    cursor.execute('SELECT loopback FROM ospf')
    result = cursor.fetchall()
    conn.close()
    return [row[0] for row in result]


#Diff Config Section
@app.route("/diffconfig", methods=["GET", "POST"])
def diff_conf():
    diffs = generate_all_diffs()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template("diffconfig.html", diffs=diffs, timestamp=timestamp)

# Migration function page
@app.route('/migration', methods=['GET', 'POST'])
def migration():
    if request.method == 'POST':
        message = perform_migration()
        return render_template('migration_result.html', message=message)
    return render_template('migration.html')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=4444)
