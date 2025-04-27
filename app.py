#!/usr/bin/env python3
from flask import Flask, render_template, request
import os
import sqlite3
from ospf_conf import conf_ospf

app = Flask(__name__)

conf_Dir = "getconfig_files"
ospf_DB = "ospf_config.db"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/getconfig')
def get_config():
    os.system("python3 getConf.py")
    if os.path.exists(conf_Dir):
        filename = sorted(os.listdir(conf_Dir), reverse=True)
    else:
        filename = []

    return render_template('config_result.html', filename=filename)

@app.route('/ospf', methods=["GET"])
def ospf_info():
    return render_template('OSPF_conf.html')

@app.route('/ospfconfig', methods=["POST"])
def ospf_config():
    router = request.form["router"]
    ospf_process = request.form["ospf_process"]
    ospf_area = request.form["ospf_area"]
    loopback = request.form["loopback"]

    conn = sqlite3.connect(ospf_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ospf (router, ospf_process, ospf_area, loopback)
        VALUES (?, ?, ?, ?)
    ''', (router, ospf_process, ospf_area, loopback))
    conn.commit()
    conn.close()

    success = conf_ospf(router, ospf_process, ospf_area, loopback)

    if success:
        return "OSPF Configuration Applied Successfully!"
    else:
        return "OSPF Configuration Failed!"



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=4444)