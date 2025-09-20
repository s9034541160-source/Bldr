import subprocess
import time
import os

print("Testing batch file execution...")

# Run the start_gui.bat file
print("Running start_gui.bat...")
process = subprocess.Popen(['cmd', '/c', 'start_gui.bat'], cwd=os.getcwd(), shell=True)

# Wait for a few seconds to see if it closes immediately
print("Waiting for 10 seconds...")
time.sleep(10)

# Check if the process is still running
if process.poll() is None:
    print("Batch file is still running")
    # Terminate the process
    process.terminate()
else:
    print(f"Batch file closed with return code: {process.returncode}")

print("Test completed")