import requests
import time
import threading
import uvicorn
import os
import json
import sqlite3
from api import app
from utils.db import init_db

# Ensure database is initialized before starting server
init_db()
print("Database re-initialized successfully.")

def run_server():
    # Run with SSL
    uvicorn.run(
        app, 
        host='127.0.0.1', 
        port=8002, 
        ssl_keyfile="/root/MedicalReportAnalysis/key.pem",
        ssl_certfile="/root/MedicalReportAnalysis/cert.pem"
    )

thread = threading.Thread(target=run_server, daemon=True)
thread.start()
time.sleep(7)

# 1. Login with HTTPS
try:
    # verify=False for self-signed cert
    login_res = requests.post('https://127.0.0.1:8002/token', data={'username': 'radiologist_user', 'password': 'secure_pass123'}, verify=False)
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        exit(1)
        
    token = login_res.json()['access_token']
    print(f'Login successful via HTTPS. Token acquired.')

    # 2. Call Diagnose via HTTPS
    headers = {'Authorization': f'Bearer {token}'}
    data = {'history': 'Patient Name: John Doe, DOB: 1980-05-12. Reports chest pain.'}
    files = {'file': ('test.dcm', b'fake_dicom_content')}
    diag_res = requests.post('https://127.0.0.1:8002/diagnose', headers=headers, data=data, files=files, verify=False)
    print(f'Diagnosis results: {json.dumps(diag_res.json(), indent=2)}')

    # 3. Verify Privacy: Check Audit Logs for PHI masking in actions
    print('\nVerifying Audit Logs for PHI Redaction...')
    with open('/root/MedicalReportAnalysis/logs/audit.log', 'r') as f:
        logs = f.readlines()
        
    # Check if clinical data entered logs (it shouldn't, but masking is there as a safety)
    phi_found = False
    for line in logs:
        if "John Doe" in line or "1980-05-12" in line:
            phi_found = True
            print(f"CRITICAL ERROR: PHI leaked into logs: {line}")
            break
            
    if not phi_found:
        print("SUCCESS: No PHI found in audit logs.")

except Exception as e:
    print(f'Verification Failed: {e}')