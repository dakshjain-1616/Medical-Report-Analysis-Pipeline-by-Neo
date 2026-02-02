import subprocess
import time
import requests
import os
import signal

def run_test():
    # Use a different port to avoid conflicts
    cmd = [
        "uvicorn", "api:app", 
        "--host", "0.0.0.0", 
        "--port", "8008", 
        "--ssl-keyfile", "./key.pem", 
        "--ssl-certfile", "./cert.pem"
    ]
    
    # Start server
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True,
        preexec_fn=os.setsid
    )
    
    print("Waiting for server to start...")
    time.sleep(10) 
    
    stdout_output, stderr_output = "", ""
    try:
        # Check health endpoint
        response = requests.get("https://localhost:8008/health", verify=False, timeout=5)
        print(f"Health Check Status: {response.status_code}")
        print(f"Health Check Response: {response.json()}")
        
        # Kill server
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        stdout_output, stderr_output = process.communicate(timeout=5)
        
    except Exception as e:
        print(f"Error during verification: {e}")
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        stdout_output, stderr_output = process.communicate()

    print("\n--- Server Stdout ---")
    print(stdout_output)
    print("\n--- Server Stderr ---")
    print(stderr_output)
    
    deprecation_msg = "on_event is deprecated"
    if deprecation_msg in stderr_output or deprecation_msg in stdout_output:
        print(f"\nFAILURE: Deprecation warning '{deprecation_msg}' still present.")
        exit(1)
    else:
        print("\nSUCCESS: No on_event deprecation warning found.")

if __name__ == "__main__":
    run_test()