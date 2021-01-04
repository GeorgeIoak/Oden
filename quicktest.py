#from evdev import InputDevice
#from selectors import DefaultSelector, EVENT_READ
#import evdev
from evdev import InputDevice, categorize, ecodes
import selectors

selector = selectors.DefaultSelector()

rotary = InputDevice('/dev/input/event0')
remote = InputDevice('/dev/input/event1')

# This works because InputDevice has a `fileno()` method.
selector.register(rotary, selectors.EVENT_READ)
selector.register(remote, selectors.EVENT_READ)

while True:
    for key, mask in selector.select():
        device = key.fileobj
        for event in device.read():
            if event.type == ecodes.EV_KEY:
                data = categorize(event)
                remCode = data.keycode
                if data.keystate >= 1:
                    print("Remote's data is:", data)
            if event.type == ecodes.EV_REL:
                print("Rotary event", event.value)

