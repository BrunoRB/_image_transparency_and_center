import pytest
from app.main import app
import multiprocessing
import time
import logging
import os

logging.basicConfig(level=logging.INFO)


@pytest.fixture(scope="session")
def start_flask_server():
    def run_server():
        app.run(host="127.0.0.1", port=5000)

    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    time.sleep(1)  # Give the server time to start

    yield

    server_process.terminate()
    server_process.join()


@pytest.fixture
def client(start_flask_server):
    app.config["TESTING"] = True
    app.config[
        "SERVER_NAME"
    ] = "127.0.0.1:5000"  # Set the server name to include the port
    # app.config["UPLOAD_FOLDER"] = f"{os.path.dirname(os.path.abspath(__file__))}/static/tests/"
    with app.test_client() as client:
        yield client
