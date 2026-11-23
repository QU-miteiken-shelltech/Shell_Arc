import urllib.request
import urllib.error
import socket

class NetworkUtils:
    @staticmethod
    def check_url_connection() -> bool:
        try:
            socket.create_connection(("1.1.1.1", 53))
            return True
        except Exception as e:
            return False


