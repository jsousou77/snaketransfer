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
  "header": b"TCP_TRANSFER FILE ",
  "done": b"TCP_TRANSFER DONE",
  "success": b"TCP_TRANSFER SUCCESS"
}

def main():
  config_file = open(CONFIG_FILE, mode="r")
  config = json.load(config_file)
  config_file.close()

  # Read values from config and use defaults if not specified
  if (not config['serverPort']) or type(config['serverPort']) != int:
    print(f"Port not specified in config! Defaulting to {DEFAULTS['serverPort']}", file=sys.stderr)
    config['serverPort'] = DEFAULTS['serverPort']

  # Set up welcome socket (when a client connects it makes a separate socket)
  welcome_socket = socket(AF_INET, SOCK_STREAM)
  welcome_socket.bind(("", config['serverPort']))
  welcome_socket.listen(1)
  print(f"Listening on port {config['serverPort']} (press Ctrl+C to close)")

  while True:
    # Keep looking for new connections until user presses Ctrl+C
    try:
      client_socket, client_addr = welcome_socket.accept()
    except KeyboardInterrupt:
      print("Exiting server")
      welcome_socket.close()
      sys.exit(0)

    print(f"Incoming connection from IP {client_addr[0]}:{client_addr[1]}")

    # Header message is standard length: command + max 3 digits for file size
    data = client_socket.recv(len(COMMANDS['header']) + 3)
    if not data.startswith(COMMANDS['header']):
      print("Header was not sent correctly! Closing connection", file=sys.stderr)
      client_socket.close()
      continue

    # Header contains length of the filename, read it and only read that many bytes
    name_length = int(data[len(COMMANDS['header']):].decode())
    data = client_socket.recv(name_length)
    file_name = data.decode()

    print(f"Receiving file \"{file_name}\"...")
    dest_file = open(file_name, mode="wb")

    print(f"Chunk size is {CHUNK_SIZE} bytes ({CHUNK_SIZE / 1024} kB)")
    chunk_num = 0
    while True:
      # Only read CHUNK_SIZE bytes at a time
      data = client_socket.recv(CHUNK_SIZE)
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
          dest_file.write(data_cropped)

        break

    dest_file.close()

    print("File received successfully!")
    client_socket.send(COMMANDS['success'])

    client_socket.close()

if __name__ == "__main__":
  main()
