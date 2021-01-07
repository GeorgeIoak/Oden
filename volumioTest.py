# Testing code to check update status on demand
from socketIO_client import SocketIO, LoggingNamespace
from threading import Thread

socketIO = SocketIO('localhost', 3000)
status = 'pause'

def on_push_state(*args):
        print('state', args)
        global status, position, duration, seek
        status = args[0]['status'].encode('ascii', 'ignore')
        seek = args[0]['seek']
        duration = args[0]['duration']
        if duration:
            position = int(seek / 1000)
        else:
            position = 0
        print("status", status, "position", position)

def _receive_thread():
    socketIO.wait()

receive_thread = Thread(target=_receive_thread, daemon=True)
receive_thread.start()

socketIO.on('pushState', on_push_state)

# issue this and the socketIO.wait in the background will push the reply
socketIO.emit('getState', '', on_push_state)