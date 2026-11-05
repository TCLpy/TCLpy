import tclpy
import time

# Define the server script using TCLpy network commands
server_script = """
# 1. Define a connection handler callback procedure
proc accept_connection {channel client_host client_port} {
    puts "CONNECTED: Client joined from $client_host:$client_port"
    
    # Send a welcoming payload to the client channel
    puts $channel "Welcome to the TCLpy AST-Compiled Network Server!"
    flush $channel
    
    # Gracefully close the connection channel
    close $channel
    puts "DISCONNECTED: Connection with $client_host:$client_port closed cleanly."
}

# 2. Bind and listen on an available port (e.g., 9000) using a background thread
set server_socket [socket -server accept_connection 9000]
puts "STATUS: TCLpy server listening loop active on port 9000..."
"""

# Initialize the critical execution environment frame
env = {}

print("--- Initializing TCLpy Socket Engine ---")
tclpy.eval(server_script, env)

# Connect to the loopback on port 9000 using netcat or something 
# 3. Keep the main Python thread alive so the background server loop can process requests
try:
    print("Server loop is running. Press Ctrl+C to terminate.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n--- Terminating TCLpy Socket Engine ---")

