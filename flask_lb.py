from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

# Define the addresses and ports of your Flask servers
FLASK_SERVERS = [
    "http://localhost:5000",
    "http://localhost:5001",
    "http://localhost:5002",
    "http://localhost:5003"
    # Add more servers if needed
]

# Dictionary to track the load on each server
SERVER_LOAD = {server: 0 for server in FLASK_SERVERS}

class LoadBalancerHandler(BaseHTTPRequestHandler):
    def get_server_load(self, server):
        try:
            # Fetch the current load from the Flask server's /load endpoint
            response = requests.get(f"{server}/load", timeout=2)  # Add a timeout to avoid hanging
            if response.status_code == 200:
                return int(response.text)  # Return the load as an integer
        except requests.RequestException as e:
            print(f"Error fetching load from {server}: {e}")
            return float('inf')  # If the server is down or not responding, return a large value
        
        return float('inf')  # Default return value if the load fetch fails


    def do_GET(self):
        # Choose the server with the lowest load by checking the /load endpoint
        chosen_server = min(FLASK_SERVERS, key=self.get_server_load)
        print(chosen_server)
        # Forward the request to the chosen Flask server
        response = requests.get(chosen_server + self.path, stream=True)
        print(response)
        # Send the response back to the client
        self.send_response(response.status_code)
        for header, value in response.headers.items():
            self.send_header(header, value)
        self.end_headers()
        
        # Send the file content to the client
        for chunk in response.iter_content(chunk_size=1024):
            self.wfile.write(chunk)

    def do_POST(self):
        # Choose the server with the lowest load by checking the /load endpoint
        chosen_server = min(FLASK_SERVERS, key=self.get_server_load)
        
        # Read the request body as bytes
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Forward the request to the chosen Flask server
        response = requests.post(chosen_server + self.path, data=post_data, headers=self.headers)
        
        # Send the response back to the client
        self.send_response(response.status_code)
        for header, value in response.headers.items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(response.content)

def run_load_balancer(server_class=HTTPServer, handler_class=LoadBalancerHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Load balancer running on port http://127.0.0.1:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_load_balancer()
