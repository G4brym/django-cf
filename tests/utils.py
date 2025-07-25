import os
import signal
import socket
import subprocess
import time

import pytest
import requests


def get_free_port():
    """Find an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


class WorkerFixture:
    def __init__(self):
        self.process = None
        self.port = None
        self.base_url = None

    def start(self, worker_dir):
        """Start the worker in a subprocess."""
        self.port = get_free_port()
        self.base_url = f"http://localhost:{self.port}"

        # Clean up previous wrangler state
        wrangler_state_dir = os.path.join(worker_dir, '.wrangler')
        if os.path.exists(wrangler_state_dir):
            subprocess.run(['rm', '-rf', wrangler_state_dir], cwd=worker_dir, check=True)

        cmd_parts = ["npx", "wrangler", "dev", "--port", str(self.port)]
        self.process = subprocess.Popen(
            cmd_parts,
            cwd=worker_dir, # Run npx from the worker directory
            preexec_fn=os.setsid,  # So we can kill the process group later
        )

        # Wait for server to start
        self._wait_for_server()

        requests.get(f"{self.base_url}/__run_migrations__/")
        requests.get(f"{self.base_url}/__create_admin__/")

        return self

    def _wait_for_server(self, max_retries=10, retry_interval=1):
        """Wait until the server is responding to requests."""
        for _ in range(max_retries):
            try:
                response = requests.get(self.base_url, timeout=20)
                if response.status_code < 500:  # Accept any non-server error response
                    return
            except requests.exceptions.RequestException:
                pass

            time.sleep(retry_interval)

        # If we got here, the server didn't start properly
        self.stop()
        raise Exception(f"worker failed to start on port {self.port}")

    def stop(self):
        """Stop the worker."""
        if self.process:
            # Kill the process group (including any child processes)
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process = None


@pytest.fixture(scope="session")
def durable_objects_web_server():
    """Pytest fixture that starts the worker for the entire test session."""
    worker_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'durable-objects')
    server = WorkerFixture()
    server.start(worker_dir)

    yield server
    server.stop()


@pytest.fixture(scope="session")
def d1_web_server():
    """Pytest fixture that starts the worker for the entire test session."""
    worker_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'd1')
    server = WorkerFixture()
    server.start(worker_dir)

    yield server
    server.stop()
