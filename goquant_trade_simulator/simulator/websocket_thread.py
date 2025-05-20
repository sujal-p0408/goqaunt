import json
import time
import websocket
import ssl
from PyQt5.QtCore import QThread, pyqtSignal

class WebSocketThread(QThread):
    data_received = pyqtSignal(dict)
    latency_updated = pyqtSignal(float)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True
        self.connection_active = False
        
    def run(self):
        def on_message(ws, message):
            start_time = time.time()
            try:
                data = json.loads(message)
                self.connection_active = True
                self.data_received.emit(data)
                
                # Calculate processing latency
                processing_time = (time.time() - start_time) * 1000  # in ms
                self.latency_updated.emit(processing_time)
            except Exception as e:
                print(f"Error processing message: {e}")
            
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
            self.connection_active = False
        
        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket closed: {close_status_code} - {close_msg}")
            self.connection_active = False
            
            # Attempt to reconnect after a delay if thread is still running
            if self.running:
                time.sleep(5)
                self.connect_websocket()
        
        def on_open(ws):
            print("WebSocket connection opened")
            self.connection_active = True
        
        def connect_websocket():
            wsapp = websocket.WebSocketApp(self.url,
                                          on_open=on_open,
                                          on_message=on_message,
                                          on_error=on_error,
                                          on_close=on_close)
            wsapp.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        self.connect_websocket = connect_websocket
        connect_websocket()
        
    def stop(self):
        self.running = False 