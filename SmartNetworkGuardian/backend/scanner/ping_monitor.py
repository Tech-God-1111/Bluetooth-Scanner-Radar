import platform
import subprocess
import time

def ping_host(host, count=1, timeout_seconds=2):
    if count < 1 or count > 5:
        raise ValueError("count must be between 1 and 5")
    flag = "-n" if platform.system() == "Windows" else "-c"
    wait_flag = "-w" if platform.system() == "Windows" else "-W"
    wait_value = str(int(timeout_seconds * 1000)) if platform.system() == "Windows" else str(timeout_seconds)
    start = time.perf_counter()
    result = subprocess.run(["ping", flag, str(count), wait_flag, wait_value, host],
                            capture_output=True, text=True, timeout=timeout_seconds * count + 3)
    elapsed = (time.perf_counter() - start) * 1000
    return {"reachable": result.returncode == 0, "elapsed_ms": round(elapsed, 2),
            "output": result.stdout[-1200:]}
