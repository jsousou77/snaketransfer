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
  "header": b"UDP_TRANSFER FILE ",
  "done": b"UDP_TRANSFER DONE",
  "success": b"UDP_TRANSFER SUCCESS"
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

  server_socket = socket(AF_INET, SOCK_DGRAM)
  # UDP doesn't need a connection

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
  server_socket.sendto(file_size_msg, (config['serverIP'], config['serverPort']))
  server_socket.sendto(os.path.basename(config['dataFile']).encode(), (config['serverIP'], config['serverPort']))

  file_size = os.path.getsize(config['dataFile'])

  print(f"Sending file {config['dataFile']} to server at {config['serverIP']}:{config['serverPort']}")

  data_file = open(config['dataFile'], mode="rb")
  data = data_file.read()
  bytes_sent = 0
  while bytes_sent < file_size:
    # Only send CHUNK_SIZE bytes at a time - flow control
    # Have to chop up the stream manually for UDP
    bytes_sent += server_socket.sendto(data[bytes_sent : bytes_sent + CHUNK_SIZE], (config['serverIP'], config['serverPort']))

  data_file.close()
  server_socket.sendto(COMMANDS['done'], (config['serverIP'], config['serverPort']))
  print("File sent! Waiting for confirmation from server...")

  server_data, server_addr = server_socket.recvfrom(CHUNK_SIZE)
  if server_data == COMMANDS['success']:
    print("Confirmation received! Closing connection")

  server_socket.close()

if __name__ == "__main__":
  main()
