import subprocess
import os
import signal
import sys
import time
import threading
import socket

def pre_flight_cleanup():
    """Kills any orphaned uvicorn or next.js processes on default ports."""
    ports = [8000, 3000]
    print("🧹 Cleaning up stale processes...")
    for port in ports:
        try:
            if sys.platform == "win32":
                # Find PID on port
                result = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
                for line in result.splitlines():
                    if "LISTENING" in line:
                        pid = line.strip().split()[-1]
                        print(f"   Stopping process {pid} on port {port}...")
                        subprocess.call(['taskkill', '/F', '/PID', pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def start_process(command, cwd, name, env=None):
    print(f"🚀 Starting {name}...")
    # Use venv python if available
    python_exe = os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = "python"
    
    cmd = command.replace("python", f'"{python_exe}"')
    
    uvicorn_exe = os.path.join(os.getcwd(), ".venv", "Scripts", "uvicorn.exe")
    if os.path.exists(uvicorn_exe):
        cmd = cmd.replace("uvicorn", f'"{uvicorn_exe}"')
    
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        env=process_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

def monitor_process(process, name):
    try:
        for line in iter(process.stdout.readline, ''):
            print(f"[{name}] {line.strip()}")
    except Exception:
        pass
    finally:
        process.stdout.close()

if __name__ == "__main__":
    pre_flight_cleanup()
    processes = []
    
    # Ensure temporal is running
    print("Ensuring Temporal server is up...")
    temporal_path = "temporal"
    if os.path.exists("temporal.exe"):
        temporal_path = os.path.abspath("temporal.exe")
    
    # Try to start it in background if not running
    try:
        # Check if already running on port 7233
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', 7233)) == 0:
                print("Temporal server is already running.")
            else:
                subprocess.run(["powershell", "-Command", f"Start-Process -NoNewWindow -FilePath '{temporal_path}' -ArgumentList 'server start-dev'"], check=True)
                print("Temporal start-dev signal sent.")
                time.sleep(5)
    except Exception as e:
        print(f"Warning: Could not ensure Temporal start: {e}")

    try:
        backend_env = {"PYTHONPATH": os.path.abspath("backend")}
        
        # 1. Backend Worker
        p_worker = start_process("python worker.py", "backend", "Temporal Worker", env=backend_env)
        processes.append({"name": "WORKER", "proc": p_worker})
        threading.Thread(target=monitor_process, args=(p_worker, "WORKER"), daemon=True).start()
        
        # 2. Backend API
        p_api = start_process("uvicorn main:app --reload --port 8000", "backend", "FastAPI Server", env=backend_env)
        processes.append({"name": "API", "proc": p_api})
        threading.Thread(target=monitor_process, args=(p_api, "API"), daemon=True).start()
        
        # 3. Frontend UI
        p_ui = start_process("npm run dev", "frontend", "Next.js UI")
        processes.append({"name": "UI", "proc": p_ui})
        threading.Thread(target=monitor_process, args=(p_ui, "UI"), daemon=True).start()

        print("\n✅ All systems launched. Press Ctrl+C to terminate all.\n")
        
        while True:
            for p in processes:
                # Check for unexpected exits
                status = p["proc"].poll()
                if status is not None:
                    if status == 0 or status == -1 or status == 255: # Common clean exits or ctrl+c
                        pass 
                    else:
                        print(f"⚠️  {p['name']} has encountered a transient error (Code {status}).")
                        print(f"   The platform is remaining active. Check the {p['name']} logs above.")
                        # Remove from monitoring to avoid spamming
                        processes.remove(p)
            
            if not processes:
                print("🏁 All processes have completed.")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down systems...")
        for p in processes:
            try:
                if sys.platform == "win32":
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(p["proc"].pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    os.killpg(os.getpgid(p["proc"].pid), signal.SIGTERM)
            except:
                pass
        print("👋 Goodbye!")
