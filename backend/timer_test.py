from fastapi.testclient import TestClient
from server import app
from datetime import datetime
import time

client = TestClient(app)

def run_test():
    date = datetime.utcnow().date().isoformat()
    print('Testing date', date)

    resp = client.post(f'/api/entries/{date}/timer/start')
    print('start status', resp.status_code, resp.json())

    resp = client.get(f'/api/entries/{date}/timer')
    print('status after start', resp.status_code, resp.json())

    time.sleep(1)

    resp = client.post(f'/api/entries/{date}/timer/stop')
    print('stop status', resp.status_code, resp.json())

    resp = client.get(f'/api/entries/{date}/timer')
    print('status after stop', resp.status_code, resp.json())

if __name__ == '__main__':
    run_test()
