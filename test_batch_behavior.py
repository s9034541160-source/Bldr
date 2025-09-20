import subprocess
import time

# Test the batch file behavior
print("Testing batch file behavior...")
print("Running start_gui.bat...")

# Run the batch file and capture output
process = subprocess.Popen(["start_gui.bat"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Wait for a few seconds to see if it closes immediately
time.sleep(5)

# Check if the process is still running
if process.poll() is None:
    print("Batch file is still running (as expected)")
    # Terminate the process
    process.terminate()
else:
    print(f"Batch file closed with return code: {process.returncode}")
    stdout, stderr = process.communicate()
    print(f"STDOUT: {stdout.decode()}")
    print(f"STDERR: {stderr.decode()}")

print("Test completed.")