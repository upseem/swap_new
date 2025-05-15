# websocket_manager.py
import threading
import json
import time
import logging
from websocket import create_connection, WebSocketException

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self, server_address, client_id):
        self.url = f"ws://{server_address}/ws?clientId={client_id}"
        self.ws = None
        self.lock = threading.Lock()
        self._heartbeat_running = False

    def connect(self):
        try:
            self.ws = create_connection(self.url, timeout=15)
            self.ws.settimeout(60) 
            logger.info("✅ WebSocket connected to %s", self.url)
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.ws = None

    def ensure_connected(self):
        with self.lock:
            if self.ws is None or not self.ws.connected:
                self.connect()

    def send(self, message):
        try:
            self.ensure_connected()
            self.ws.send(message)
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")
            self.connect()

    def recv(self):
        try:
            return self.ws.recv()
        except Exception as e:
            logger.warning(f"WebSocket recv failed: {e}")
            self.connect()
            return None

    def heartbeat_loop(self, interval=5):
        self._heartbeat_running = True
        while self._heartbeat_running:
            try:
                self.send("ping")
            except Exception:
                pass
            time.sleep(interval)

    def start_heartbeat(self, interval=10):  # 默认 10 秒
        if not self._heartbeat_running:
            thread = threading.Thread(target=self.heartbeat_loop, args=(interval,), daemon=True)
            thread.start()

    def stop_heartbeat(self):
        self._heartbeat_running = False

    def get_images(self, prompt_id):
        output_image = None
        current_node = ""
        while True:
            out = self.recv()
            if out is None:
                continue
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['prompt_id'] == prompt_id:
                        if data['node'] is None:
                            break
                        else:
                            current_node = data['node']
            else:
                if current_node == 'save_image_websocket_node' and output_image is None:
                    output_image = out[8:]
        return output_image
