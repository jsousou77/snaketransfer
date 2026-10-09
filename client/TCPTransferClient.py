#!/bin/env python3

import os
import sys
import json
from socket import *

CONFIG_FILE = "transfer_client_config.json"
CHUNK_SIZE = 16 * 1024 # 16kB

DEFAULTS = {
  "serverIP": "localhost",
  "serverPort": 12000,
  "dataFile": "data.txt"
}

# Special messages used to communicate between server and client outside of transferring the actual file
COMMANDS = {
  "header": b"TCP_TRANSFER FILE ",
  "done": b"TCP_TRANSFER DONE",
  "success": b"TCP_TRANSFER SUCCESS"
}

def main():
  config_file = open(CONFIG_FILE, mode="r")
  config = json.load(config_file)
  config_file.close()

  # Read values from config and use defaults if not specified
  if not config['serverIP']:
    print(f"IP not specified in config! Defaulting to {DEFAULTS['serverIP']}", file=sys.stderr)
    config['serverIP'] = DEFAULTS['serverIP']

  if (not config['serverPort']) or type(config['serverPort']) != int:
    print(f"Port not specified in config! Defaulting to {DEFAULTS['serverPort']}", file=sys.stderr)
    config['serverPort'] = DEFAULTS['serverPort']

  if not config['dataFile']:
    print(f"Data file not specified in config! Defaulting to {DEFAULTS['dataFile']}", file=sys.stderr)
    config['dataFile'] = DEFAULTS['dataFile']

  server_socket = socket(AF_INET, SOCK_STREAM)
  print(f"Connecting to server at {config['serverIP']}:{config['serverPort']}...")
  server_socket.connect((config['serverIP'], config['serverPort']))
  print(f"Connected to server! Sending file {config['dataFile']}...")

  # Header message: command and then max 3 digits for length of filename
  # Length of filename is sent so the server knows how many bytes to read
  file_size_msg = COMMANDS['header'] + str(len(os.path.basename(config['dataFile']))).encode()
  size_msg_length = len(file_size_msg)
  if (size_msg_length < len(COMMANDS['header']) + 3):
    # Pad message to standard length to avoid chunk issues
    i = len(COMMANDS['header']) + 3 - size_msg_length
    while (i > 0):
      file_size_msg += b" "
      i -= 1

  # Send header and then filename
  server_socket.send(file_size_msg)
  server_socket.send(os.path.basename(config['dataFile']).encode())

  file_size = os.path.getsize(config['dataFile'])

  data = open(config['dataFile'], mode="rb")
  bytes_sent = 0
  while bytes_sent < file_size:
    # Only send CHUNK_SIZE bytes at a time - flow control
    server_socket.sendfile(data, offset=bytes_sent, count=CHUNK_SIZE)
    bytes_sent = data.tell()

  data.close()
  server_socket.send(COMMANDS['done'])
  print("File sent! Waiting for confirmation from server...")

  server_data = server_socket.recv(CHUNK_SIZE)
  if server_data == COMMANDS['success']:
    print("Confirmation received! Closing connection")

  server_socket.close()

if __name__ == "__main__":
  main()
