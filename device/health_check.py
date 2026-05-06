import shutil
import requests

def check_server(api_base_url: str, timeout: int = 5) -> bool:
    try:
        response = requests.get(api_base_url, timeout=timeout)
        return response.status_code < 500
    except requests.RequestException:
        return False

def check_disk_space(min_free_mb: int = 500) -> bool:
    usage = shutil.disk_usage(".")
    free_mb = usage.free / (1024 * 1024)
    return free_mb >= min_free_mb
