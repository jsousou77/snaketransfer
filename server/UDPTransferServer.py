#!/bin/env python3

import os
import sys
import json
from socket import *

CONFIG_FILE = "transfer_server_config.json"
CHUNK_SIZE = 16 * 1024 # 16kB

DEFAULTS = {
  "serverPort": 12000
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
  if (not config['serverPort']) or type(config['serverPort']) != int:
    print(f"Port not specified in config! Defaulting to {DEFAULTS['serverPort']}", file=sys.stderr)
    config['serverPort'] = DEFAULTS['serverPort']

  # Set up socket
  client_socket = socket(AF_INET, SOCK_DGRAM)
  client_socket.bind(("", config['serverPort']))
  print(f"Listening on port {config['serverPort']} (press Ctrl+C to close)")

  while True:
    # Keep looking for new connections until user presses Ctrl+C
    try:
      data, client_addr = client_socket.recvfrom(len(COMMANDS['header']) + 3)
    except KeyboardInterrupt:
      print("Exiting server")
      client_socket.close()
      sys.exit(0)

    print(f"Received data from {client_addr[0]}:{client_addr[1]}")
    if not data.startswith(COMMANDS['header']):
      print("Header was not sent correctly! Ignoring connection", file=sys.stderr)
      continue

    # Header contains length of the filename, read it and only read that many bytes
    name_length = int(data[len(COMMANDS['header']):].decode())
    data, client_addr = client_socket.recvfrom(name_length)
    file_name = data.decode()

    print(f"Receiving file \"{file_name}\"...")
    dest_file = open(file_name, mode="wb")

    print(f"Chunk size is {CHUNK_SIZE} bytes ({CHUNK_SIZE / 1024} kB)")
    chunk_num = 0
    while True:
      # Only read CHUNK_SIZE bytes at a time
      data, client_addr = client_socket.recvfrom(CHUNK_SIZE)
      if len(data) == 0: # If something breaks, this keeps it from getting stuck in an infinite loop
        break

      if not data.endswith(COMMANDS['done']):

        print(f"Writing chunk {chunk_num}")
        dest_file.write(data)
        chunk_num += 1

      else: # Chunk contains the "done" command, check to see if any file data was there as well or if it was just the command (behavior changes depending on machine I think??)
        print(f"Chunk {chunk_num} contains EOF command")
        data_cropped = data[0 : len(data) - len(COMMANDS['done'])]

        if (len(data_cropped) > 0): # Extra file data before the command
          print(f"Writing chunk {chunk_num}")

        break

    dest_file.close()

    print("File received successfully!")
    client_socket.sendto(COMMANDS['success'], client_addr)

if __name__ == "__main__":
  main()
