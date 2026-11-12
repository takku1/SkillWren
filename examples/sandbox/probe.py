import pathlib
import socket
try:
    pathlib.Path('/escape').write_text('outside workspace')
    raise AssertionError('root filesystem writable')
except OSError:
    pass
try:
    socket.create_connection(('1.1.1.1', 443), timeout=1).close()
    raise AssertionError('network unexpectedly available')
except OSError:
    pass
pathlib.Path('result.txt').write_text('contained')
