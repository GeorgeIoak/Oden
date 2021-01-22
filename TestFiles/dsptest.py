import os
import sys
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
from luma.core.render import canvas
from time import*

interface = spi(device=0, port=0)
oled = ssd1322(interface, rotate=0)
oled.WIDTH = 256
oled.HEIGHT = 64

image = Image.new('RGB', (oled.WIDTH, oled.HEIGHT))  #for Pixelshift: (oled.WIDTH + 4, oled.HEIGHT + 4))

def load_font(filename, font_size):
    #font_path = os.path.dirname(os.path.realpath(__file__)) # + '/../fonts/'
    font_path = '/home/volumio/luma.examples/examples/fonts/'
    print(font_path + filename)
    try:
        font = ImageFont.truetype(font_path + filename, font_size)
    except IOError:
        print('font file not found -> using default font')
        font = ImageFont.load_default()
    return font

font = load_font('FreePixel.ttf', 24)

volume = 35
bar = 152 * volume / 100
with canvas(oled) as draw:
    draw.rectangle(oled.bounding_box, outline="white", fill="black")
    draw.rectangle((40, 50, 202, 60), outline='white', fill='white')
    draw.rectangle((bar+50-2, 57, 50+bar+2, 61), outline='white', fill='black')
    draw.text((20, 10), "Hello World", fill="white", font=font)
sleep(8)