# snaketransfer
I just came up with the name right now

A small, terrible, proof-of-concept file transfer utility using the Python [socket API](https://docs.python.org/3/library/socket.html). Written for a [networks course](https://catalog.binghamton.edu/preview_course_nopop.php?catoid=7&coid=67575) assignment.

This utility has two versions, one using TCP (`TCPTransferServer.py` and `TCPTransferClient.py`) and one using UDP (`UDPTransferServer.py` and `UDPTransferClient.py`). Usage is very simple: The server stays open and listens for connecting clients, and the client runs once and sends a file to the server. That's it

The server and client both have config files, they're pretty self-explanatory.

Since UDP has no guarantee of reliability, the UDP file transfer implementation is very broken and usually doesn't get all the data to the other end. But that's just how UDP is; if you want reliability, use TCP.
