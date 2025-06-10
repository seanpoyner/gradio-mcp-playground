"""Test script to check if an agent is running properly"""
import subprocess
import time
import sys
import os

# Test the conversational agent
agent_file = "agents/conversational.py"

if os.path.exists(agent_file):
    print(f"Testing {agent_file}...")
    
    # Set environment
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    env['AGENT_PORT'] = '7861'  # Different port for testing
    
    # Run the agent
    process = subprocess.Popen(
        [sys.executable, agent_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        bufsize=1
    )
    
    print(f"Started process with PID: {process.pid}")
    print("Waiting for output...")
    
    # Read output for 10 seconds
    start_time = time.time()
    while time.time() - start_time < 10:
        # Check stdout
        try:
            line = process.stdout.readline()
            if line:
                print(f"STDOUT: {line.strip()}")
        except:
            pass
            
        # Check stderr  
        try:
            line = process.stderr.readline()
            if line:
                print(f"STDERR: {line.strip()}")
        except:
            pass
            
        # Check if process is still running
        if process.poll() is not None:
            print(f"Process exited with code: {process.poll()}")
            # Get remaining output
            stdout, stderr = process.communicate()
            if stdout:
                print(f"Final STDOUT:\n{stdout}")
            if stderr:
                print(f"Final STDERR:\n{stderr}")
            break
            
        time.sleep(0.1)
    
    # Kill if still running
    if process.poll() is None:
        print("Terminating process...")
        process.terminate()
        process.wait()
else:
    print(f"Agent file not found: {agent_file}")