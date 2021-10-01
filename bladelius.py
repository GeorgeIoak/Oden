#!/usr/bin/python3
#    ____                           __           
#   /  _/___ ___  ____  ____  _____/ /______   _ 
#   / // __ `__ \/ __ \/ __ \/ ___/ __/ ___/  (_)
# _/ // / / / / / /_/ / /_/ / /  / /_(__  )  _   
#/___/_/ /_/ /_/ .___/\____/_/   \__/____/  (_)  
#             /_/                                
from __future__ import unicode_literals
import requests
import os
import sys
import threading
import signal
import json
import pycurl
import pprint
import subprocess
import RPi.GPIO as GPIO
import spidev
import smbus
from time import*
from datetime import timedelta as timedelta
from threading import Thread
from evdev import InputDevice, categorize, ecodes
from queue import Queue
from socketIO_client import SocketIO
from datetime import datetime as datetime
from io import BytesIO 
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from modules.pushbutton import PushButton
from modules.rotaryencoder import RotaryEncoder
import modules.bdgremote as bladelius
import uuid
#import numpy as np
from ConfigurationFiles.PreConfiguration import*
from ConfigurationFiles.config import*
import urllib.request
from urllib.parse import* #from urllib import*
from urllib.parse import urlparse
from urllib.parse import urlencode
import ssl
import re
import fnmatch
#sleep(3.0)
#________________________________________________________________________________________
#	
#   ______            _____                        __  _                 
#  / ____/___  ____  / __(_)___ ___  ___________ _/ /_(_)___  ____     _ 
# / /   / __ \/ __ \/ /_/ / __ `/ / / / ___/ __ `/ __/ / __ \/ __ \   (_)
#/ /___/ /_/ / / / / __/ / /_/ / /_/ / /  / /_/ / /_/ / /_/ / / / /  _   
#\____/\____/_/ /_/_/ /_/\__, /\__,_/_/   \__,_/\__/_/\____/_/ /_/  (_)  
#                       /____/
#
ScreenList = ['No-Spectrum']

NowPlayingLayoutSave=open('/home/volumio/bladelius/ConfigurationFiles/LayoutSet.txt').readline().rstrip()
print('Layout selected during setup: ', NowPlayingLayout)
print('Last manually selected Layout: ', NowPlayingLayoutSave)

if NowPlayingLayout not in ScreenList:
    WriteScreen1 = open('/home/volumio/bladelius/ConfigurationFiles/LayoutSet.txt', 'w')
    WriteScreen1.write('No-Spectrum')
    WriteScreen1.close
    NowPlayingLayout = 'No-Spectrum'

if NowPlayingLayoutSave != NowPlayingLayout:
    if NowPlayingLayoutSave not in ScreenList and not SpectrumActive:
        WriteScreen1 = open('/home/volumio/bladelius/ConfigurationFiles/LayoutSet.txt', 'w')
        WriteScreen1.write('No-Spectrum')
        WriteScreen1.close
        NowPlayingLayout = 'No-Spectrum'
    else:
        NowPlayingLayout = NowPlayingLayoutSave

#config for timers:
oledPlayFormatRefreshTime = 1.5
oledPlayFormatRefreshLoopCount = 3
#________________________________________________________________________________________
#________________________________________________________________________________________
#   _____ __             __            __     _____       _ __  _                      
#  / ___// /_____ ______/ /_      ____/ /__  / __(_)___  (_) /_(_)___  ____  _____   _ 
#  \__ \/ __/ __ `/ ___/ __/_____/ __  / _ \/ /_/ / __ \/ / __/ / __ \/ __ \/ ___/  (_)
# ___/ / /_/ /_/ / /  / /_/_____/ /_/ /  __/ __/ / / / / / /_/ / /_/ / / / (__  )  _   
#/____/\__/\__,_/_/   \__/      \__,_/\___/_/ /_/_/ /_/_/\__/_/\____/_/ /_/____/  (_)  
#     
GPIO.setmode(GPIO.BCM) 
GPIO.setwarnings(False)

firstStart = True

from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
from modules.display1322 import*
from ConfigurationFiles.ScreenConfig1322 import*

volumio_host = 'localhost'
volumio_port = 3000
volumioIO = SocketIO(volumio_host, volumio_port)

if StandbyActive:
    GPIO.setup(13, GPIO.OUT)
    GPIO.setup(26, GPIO.IN)
    GPIO.output(13, GPIO.HIGH)

b_obj = BytesIO() 
crl = pycurl.Curl() 

STATE_NONE = -1
STATE_PLAYER = 0
STATE_QUEUE_MENU = 1
STATE_LIBRARY_INFO = 2
STATE_SCREEN_MENU = 3
STATE_OTHER_INPUT = 4

UPDATE_INTERVAL = 0.034

interface = spi(device=0, port=0)
oled = ssd1322(interface, rotate=oledrotation) 
oled.WIDTH = 256
oled.HEIGHT = 64

oled.state = 'stop'
oled.stateTimeout = 0
oled.playstateIcon = ''
oled.timeOutRunning = False
oled.activeSong = ''
oled.activeArtist = 'VOLuMIO'
oled.playState = 'unknown'
oled.playPosition = 0
oled.seek = 1000
oled.duration = 1.0
oled.modal = False
oled.playlistoptions = []
oled.queue = []
oled.libraryFull = []
oled.libraryNames = []
oled.volumeControlDisabled = True
oled.volume = 100
now = datetime.now()                       #current date and time
oled.time = now.strftime("%H:%M:%S")       #resolves time as HH:MM:SS eg. 14:33:15
oled.date = ""   #resolves time as dd.mm.YYYY eg. 17.04.2020
oled.IP = ''
emit_track = False
newStatus = 0              				   #makes newStatus usable outside of onPushState
oled.activeFormat = ''      			   #makes oled.activeFormat globaly usable
oled.activeSamplerate = ''  			   #makes oled.activeSamplerate globaly usable
oled.activeBitdepth = ''                   #makes oled.activeBitdepth globaly usable
oled.activeArtists = ''                    #makes oled.activeArtists globaly usable
oled.activeAlbums = ''                     #makes oled.activeAlbums globaly usable
oled.activeAlbum = ''
oled.activeAlbumart = ''
oled.activeSongs = ''                      #makes oled.activeSongs globaly usable
oled.activePlaytime = ''                   #makes oled.activePlaytime globaly usable
oled.randomTag = False                     #helper to detect if "Random/shuffle" is set
oled.repeatTag = False                     #helper to detect if "repeat" is set
oled.ShutdownFlag = False                  #helper to detect if "shutdown" is running. Prevents artifacts from Standby-Screen during shutdown
varcanc = True                      #helper for pause -> stop timeout counter
secvar = 0.0
oled.volume = 100
oled.SelectedScreen = NowPlayingLayout
oled.fallingL = False
oled.fallingR = False
oled.prevFallingTimerL = 0
oled.prevFallingTimerR = 0
ScrollArtistTag = 0
ScrollArtistNext = 0
ScrollArtistFirstRound = True
ScrollArtistNextRound = False
ScrollSongTag = 0
ScrollSongNext = 0
ScrollSongFirstRound = True
ScrollSongNextRound = False
oled.selQueue = ''
oled.repeat = False
oled.bitrate = ''
oled.repeatonce = False
oled.shuffle = False
oled.mute = False
oled.dimLevel = 1

# Declare files to save status varialbe
file_mute = mute
file_vol = vol
file_input = theinput
file_power = power
selectedInput = 0
dimLevels = [0, 75, 150, 255]  #use oled.contrast(level) range of 0-255

image = Image.new('RGB', (oled.WIDTH, oled.HEIGHT))  #for Pixelshift: (oled.WIDTH + 4, oled.HEIGHT + 4)) 
oled.clear()
#________________________________________________________________________________________
#________________________________________________________________________________________
#	
#    ______            __           
#   / ____/___  ____  / /______   _ 
#  / /_  / __ \/ __ \/ __/ ___/  (_)
# / __/ / /_/ / / / / /_(__  )  _   
#/_/    \____/_/ /_/\__/____/  (_)  
#
font = load_font('Oxanium-Bold.ttf', 18)                       #used for Artist ('Oxanium-Bold.ttf', 20)  
font2 = load_font('Oxanium-Light.ttf', 12)                     #used for all menus
font3 = load_font('Oxanium-Regular.ttf', 16)                   #used for Song ('Oxanium-Regular.ttf', 18) 
font4 = load_font('Oxanium-Medium.ttf', 12)                    #used for Format/Smplerate/Bitdepth
font5 = load_font('Oxanium-Medium.ttf', 12)                    #used for Artist / Screen5
font6 = load_font('Oxanium-Regular.ttf', 12)                   #used for Song / Screen5
font7 = load_font('Oxanium-Light.ttf', 10)                     #used for all other / Screen5
font8 = load_font('Oxanium-Regular.ttf', 10)                   #used for Song / Screen5
font9 = load_font('Oxanium-Bold.ttf', 16)                       #used for Artist ('Oxanium-Bold.ttf', 20)  
font10 = load_font('Oxanium-Regular.ttf', 14)                       #used for Artist ('Oxanium-Bold.ttf', 20)  
mediaicon = load_font('fa-solid-900.ttf', 10)    	           #used for icon in Media-library info
#iconfont = load_font('entypo.ttf', oled.HEIGHT)                #used for play/pause/stop/shuffle/repeat... icons
labelfont = load_font('entypo.ttf', 12)                        #used for Menu-icons
iconfontBottom = load_font('entypo.ttf', 10)                   #used for icons under the screen / button layout
labelfontfa = load_font('fa-solid-900.ttf', 12)                   #used for icons under the screen / button layout
labelfontfa2 = load_font('fa-solid-900.ttf', 14)
fontClock = load_font('DSG.ttf', 30)                           #used for clock
fontDate = load_font('Oxanium-Light.ttf', 12)           #used for Date 'DSEG7Classic-Regular.ttf'
fontIP = load_font('Oxanium-Light.ttf', 12)             #used for IP 'DSEG7Classic-Regular.ttf'
#above are the "imports" for the fonts. 
#After the name of the font comes a number, this defines the Size (height) of the letters. 
#Just put .ttf file in the 'Volumio-OledUI/fonts' directory and make an import like above. 
#________________________________________________________________________________________
#________________________________________________________________________________________
#
#   _____ __                  ____                __                _          
#  / ___// /_____ _____  ____/ / /_  __  __      / /   ____  ____ _(_)____   _ 
#  \__ \/ __/ __ `/ __ \/ __  / __ \/ / / /_____/ /   / __ \/ __ `/ / ___/  (_)
# ___/ / /_/ /_/ / / / / /_/ / /_/ / /_/ /_____/ /___/ /_/ / /_/ / / /__   _   
#/____/\__/\__,_/_/ /_/\__,_/_.___/\__, /     /_____/\____/\__, /_/\___/  (_)  
#                                 /____/                  /____/               
#
def StandByWatcher():
# listens to GPIO 26. If Signal is High, everything is fine, raspberry will keep doing it's shit.
# If GPIO 26 is Low, Raspberry will shutdown.
    StandbySignal = GPIO.input(26)
    while True:
        StandbySignal = GPIO.input(26)
        if StandbySignal == 0:
            oled.ShutdownFlag = True
            volumioIO.emit('stop')
            GPIO.output(13, GPIO.LOW)
            sleep(1)
            oled.clear()
            show_logo(oledShutdownLogo, oled)
            volumioIO.emit('shutdown')
        elif StandbySignal == 1:
            sleep(1)

def sigterm_handler(signal, frame):
    oled.clear()
    image.paste(('black'), [0, 0, oled.WIDTH, oled.HEIGHT])
    oled.display(image)
    print("Made it into sigterm_handler")
    show_logo("ShutdownScreen1322.bmp", oled)
    oled.ShutdownFlag = True
    volumioIO.emit('stop')
    # GPIO.output(13, GPIO.LOW) # Not using standby circuit for now
    bladelius.cleanup()
    sleep(1)
    sys.exit()
#________________________________________________________________________________________
#________________________________________________________________________________________
#
#    ________        ___       __                        
#   /  _/ __ \      /   | ____/ /_______  __________   _ 
#   / // /_/ /_____/ /| |/ __  / ___/ _ \/ ___/ ___/  (_)
# _/ // ____/_____/ ___ / /_/ / /  /  __(__  |__  )  _   
#/___/_/         /_/  |_\__,_/_/   \___/____/____/  (_)  
#   
def GetIP():
    lanip = GetLANIP()
    LANip = str(lanip.decode('ascii'))
    print('LAN IP: ', LANip)
    wanip = GetWLANIP()
    WLANip = str(wanip.decode('ascii'))
    print('Wifi IP: ', WLANip)
    if LANip != '':
       ip = LANip
    elif WLANip != '':
       ip = WLANip
    else:
       ip = "no ip"
    oled.IP = ip

def GetLANIP():
    cmd = \
        "ip addr show eth0 | grep inet  | grep -v inet6 | awk '{print $2}' | cut -d '/' -f 1"
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = p.communicate()[0]
    return output[:-1]

def GetWLANIP():
    cmd = \
        "ip addr show wlan0 | grep inet  | grep -v inet6 | awk '{print $2}' | cut -d '/' -f 1"
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = p.communicate()[0]
    return output[:-1]
#________________________________________________________________________________________
#________________________________________________________________________________________
#    ____              __        __  __          
#   / __ )____  ____  / /_      / / / /___     _ 
#  / __  / __ \/ __ \/ __/_____/ / / / __ \   (_)
# / /_/ / /_/ / /_/ / /_/_____/ /_/ / /_/ /  _   
#/_____/\____/\____/\__/      \____/ .___/  (_)  
#                                 /_/            
#
signal.signal(signal.SIGTERM, sigterm_handler)
if StandbyActive and firstStart:
    StandByListen = threading.Thread(target=StandByWatcher, daemon=True)
    StandByListen.start()
    if ledActive != True:
       firstStart = False

GetIP()
#________________________________________________________________________________________
#________________________________________________________________________________________
#
#    ____  _            __                  __  __          __      __           
#   / __ \(_)________  / /___ ___  __      / / / /___  ____/ /___ _/ /____     _ 
#  / / / / / ___/ __ \/ / __ `/ / / /_____/ / / / __ \/ __  / __ `/ __/ _ \   (_)
# / /_/ / (__  ) /_/ / / /_/ / /_/ /_____/ /_/ / /_/ / /_/ / /_/ / /_/  __/  _   
#/_____/_/____/ .___/_/\__,_/\__, /      \____/ .___/\__,_/\__,_/\__/\___/  (_)  
#            /_/            /____/           /_/                                 
#
def display_update_service():
    while UPDATE_INTERVAL > 0 and not oled.ShutdownFlag:
        prevTime = time()
        dt = time() - prevTime
        if oled.stateTimeout > 0:
            oled.timeOutRunning = True
            oled.stateTimeout -= dt
        elif oled.stateTimeout <= 0 and oled.timeOutRunning:
            oled.timeOutRunning = False
            oled.stateTimeout = 0
            SetState(STATE_PLAYER)
        image.paste("black", [0, 0, image.size[0], image.size[1]])
        try:
            oled.modal.DrawOn(image)
        except AttributeError as error:
            print("render error:", error)
            sleep(1) 
        cimg = image.crop((0, 0, oled.WIDTH, oled.HEIGHT)) 
        oled.display(cimg)
        sleep(UPDATE_INTERVAL)
#________________________________________________________________________________________
#________________________________________________________________________________________
#
#   ____  __      _           __ _           
#  / __ \/ /_    (_)__  _____/ /( )_____   _ 
# / / / / __ \  / / _ \/ ___/ __/// ___/  (_)
#/ /_/ / /_/ / / /  __/ /__/ /_  (__  )  _   
#\____/_.___/_/ /\___/\___/\__/ /____/  (_)  
#          /___/                             
#
def SetState(status):
    oled.state = status
    if oled.state == STATE_PLAYER:
        oled.modal = NowPlayingScreen(oled.HEIGHT, oled.WIDTH) 
    elif oled.state == STATE_QUEUE_MENU:
        oled.modal = MenuScreen(oled.HEIGHT, oled.WIDTH)
    elif oled.state == STATE_LIBRARY_INFO:
        oled.modal = MediaLibrarayInfo(oled.HEIGHT, oled.WIDTH)
    elif oled.state == STATE_SCREEN_MENU:
        oled.modal = ScreenSelectMenu(oled.HEIGHT, oled.WIDTH)
    elif oled.state == STATE_OTHER_INPUT:
        oled.modal = OtherInputScreen(oled.HEIGHT, oled.WIDTH)

#________________________________________________________________________________________
#________________________________________________________________________________________
#        
#    ____        __              __  __                ____              
#   / __ \____ _/ /_____ _      / / / /___ _____  ____/ / /__  _____   _ 
#  / / / / __ `/ __/ __ `/_____/ /_/ / __ `/ __ \/ __  / / _ \/ ___/  (_)
# / /_/ / /_/ / /_/ /_/ /_____/ __  / /_/ / / / / /_/ / /  __/ /     _   
#/_____/\__,_/\__/\__,_/     /_/ /_/\__,_/_/ /_/\__,_/_/\___/_/     (_)  
#   
def JPGPathfinder(String):
    print('JPGPathfinder')
    albumstring = String
    global FullJPGPath
    try:
        p1 = 'path=(.+?)&metadata'
        result = re.search(p1, albumstring)
        URL = result.group(1)
        URLPath = "/mnt" + URL + '/'
        accepted_extensions = ['jpg', 'jpeg', 'gif', 'png', 'bmp']
        filenames = [fn for fn in os.listdir(URLPath) if fn.split(".")[-1] in accepted_extensions]
        JPGName = filenames[0]
        FullJPGPath = URLPath + JPGName
    except:
        FullJPGPath = '/home/volumio/bladelius/NoCover.bmp'
    JPGSave(FullJPGPath)
    print('FullJPGPath: ', FullJPGPath)

def JPGSave(Path):
    print('JPGSave')
    FullJPGPath = Path
    img = Image.open(FullJPGPath)     # puts our image to the buffer of the PIL.Image object
    width, height = img.size
    asp_rat = width/height
    new_width = 90
    new_height = 90
    new_rat = new_width/new_height
    img = img.resize((new_width, new_height), Image.ANTIALIAS)
    img.save('/home/volumio/album.bmp') 

def JPGSaveURL(link):
    print('JPGSaveURL')
    try:
        httpLink = urllib.parse.quote(link).replace('%3A',':')
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(httpLink, context=ctx) as url:
            with open('temp.jpg', 'wb') as f:
                f.write(url.read())
        img = Image.open('temp.jpg')
    except:
        img = Image.open('/home/volumio/bladelius/NoCover.bmp')    
    width, height = img.size
    asp_rat = width/height
    new_width = 90
    new_height = 90
    new_rat = new_width/new_height
    img = img.resize((new_width, new_height), Image.ANTIALIAS)
    img.save('/home/volumio/album.bmp') 

def onPushState(data):
    if oled.state != 3:
        global OPDsave	
        global newStatus #global definition for newStatus, used at the end-loop to update standby
        global newSong
        global newArtist
        global newFormat
        global varcanc
        global secvar
        global ScrollArtistTag
        global ScrollArtistNext
        global ScrollArtistFirstRound
        global ScrollArtistNextRound
        global ScrollSongTag
        global ScrollSongNext
        global ScrollSongFirstRound
        global ScrollSongNextRound
        OPDsave = data
        #print('status:', data['status'].encode('utf-8'))
        #print('position:', int(data['seek'] / 1000))
    
        if 'title' in data:
            newSong = data['title']
        else:
            newSong = ''
        if newSong is None:
            newSong = ''
        if newSong == 'HiFiBerry ADC':
            newSong = 'Bluetooth-Audio'
            
        if 'artist' in data:
            newArtist = data['artist']
        else:
            newArtist = ''
        if newArtist is None and newSong != 'HiFiBerry ADC':   #volumio can push NoneType
            newArtist = ''
        if newArtist == '' and newSong == 'HiFiBerry ADC':
            newArtist = 'Line-Input:'

        if 'trackType' in data:
            newFormat = data['trackType']
        else:
            newFormat = ''
        if newFormat is None:
            newFormat = ''
        oled.activeFormat = newFormat

#        if 'stream' in data:
#            newFormat = data['stream']
#            if not newFormat:
#                newFormat = newTrackType
#                oled.activeFormat = newFormat
#            if newFormat is None:
#                newFormat = ''
#                oled.activeFormat = newFormat
#            if newFormat and newSong != 'HiFiBerry ADC':
#                newFormat = 'WebRadio'
#                oled.activeFormat = newFormat
#            if newFormat and newSong == 'HiFiBerry ADC':
#                newFormat = 'Live-Stream'
#                oled.activeFormat = newFormat
                
        #If a stream (like webradio) is playing, the data set for 'stream'/newFormat is a boolian (True)
        #drawOn can't handle that and gives an error. 
        #therefore we use "if newFormat:" and define a placeholder Word, you can change it.
    
        if 'samplerate' in data:
            newSamplerate = data['samplerate']
            oled.activeSamplerate = newSamplerate
        else:
            newSamplerate = ' '
            oled.activeSamplerate = newSamplerate
        if newSamplerate is None:
            newSamplerate = ' '
            oled.activeSamplerate = newSamplerate
        
        if 'bitrate' in data:
            oled.bitrate = data['bitrate']
        else:
            bitrate = ''
        if oled.bitrate is None:
            oled.bitrate = ''
        
        if 'bitdepth' in data:
            newBitdepth = data['bitdepth']
            oled.activeBitdepth = newBitdepth
        else:
            newBitdepth = ' '
            oled.activeBitdepth = newBitdepth
        if newBitdepth is None:
            newBitdepth = ' '
            oled.activeBitdepth = newBitdepth  
            
        if 'position' in data:                      # current position in queue
            oled.playPosition = data['position']    # didn't work well with volumio ver. < 2.5
        else:
            oled.playPosition = None
            
        if 'status' in data:
            newStatus = data['status']

        if 'volume' in data:            #get volume on startup and remote control
            oled.volume = int(data['volume'])
        else:
            oled.volume = 100

        if 'repeat' in data:
            oled.repeat = data['repeat']
        
        if 'repeatSingle' in data:
            oled.repeatonce = data['repeatSingle']

        if 'random' in data:
            oled.shuffle = data['random']

        if 'mute' in data:
            oled.mute = data['mute']

        if ledActive and 'channels' in data:
            channels = data['channels']
            if newStatus != 'stop':
                if channels == 2:
                   StereoLEDon()
                else:
                    StereoLEDoff()
            if newStatus == 'stop':
                StereoLEDoff()
    
        if 'duration' in data:
            oled.duration = data['duration']
        else:
            oled.duration = None
        if oled.duration == int(0):
            oled.duration = None
    
        if 'seek' in data:
            oled.seek = data['seek']
        else:
            oled.seek = None
        if NR1UIRemoteActive:
            if 'albumart' in data:
                newAlbumart = data['albumart']
            else:
                newAlbumart = None
            if newAlbumart is None:
                newAlbumart = 'nothing'
            AlbumArtHTTP = newAlbumart.startswith('http')

        if 'album' in data:
            newAlbum = data['album']
        else: 
            newAlbum = None
            if newAlbum is None:
                newAlbum = 'No Album'
            if newAlbum == '':
                newAlbum = 'No Album'

        if (newSong != oled.activeSong) or (newArtist != oled.activeArtist) or (newAlbum != oled.activeAlbum):                                # new song and artist
            oled.activeSong = newSong
            oled.activeArtist = newArtist
            oled.activeAlbum = newAlbum
            varcanc = True                      #helper for pause -> stop timeout counter
            secvar = 0.0
            ScrollArtistTag = 0
            ScrollArtistNext = 0
            ScrollArtistFirstRound = True
            ScrollArtistNextRound = False                  
            ScrollSongTag = 0
            ScrollSongNext = 0
            ScrollSongFirstRound = True
            ScrollSongNextRound = False
            if oled.state == STATE_PLAYER and newStatus != 'stop':                                          #this is the "NowPlayingScreen"
                if ledActive:
                   PlayLEDon()
                oled.modal.UpdatePlayingInfo()     #here is defined which "data" should be displayed in the class
            if oled.state == STATE_PLAYER and newStatus == 'stop':                                          #this is the "Standby-Screen"
                if ledActive:
                   PlayLEDoff()
                   StereoLEDoff()
            
        if newStatus != oled.playState:
            varcanc = True                      #helper for pause -> stop timeout counter
            secvar = 0.0
            oled.playState = newStatus
            if oled.state == STATE_PLAYER:
                if oled.playState != 'stop':
                    if newStatus == 'pause':
                        if ledActive:
                            PlayLEDoff()
                        oled.playstateIcon = oledpauseIcon
                    if newStatus == 'play':
                        if ledActive:
                            PlayLEDon()
                        oled.playstateIcon = oledplayIcon
                    oled.modal.UpdatePlayingInfo()
                else:
                    if ledActive:
                        PlayLEDoff()
                        StereoLEDoff()
                    ScrollArtistTag = 0
                    ScrollArtistNext = 0
                    ScrollArtistFirstRound = True
                    ScrollArtistNextRound = False                  
                    ScrollSongTag = 0
                    ScrollSongNext = 0
                    ScrollSongFirstRound = True
                    ScrollSongNextRound = False
                    SetState(STATE_PLAYER)
                    oled.modal.UpdateStandbyInfo()
        
        if NR1UIRemoteActive:
            if newAlbumart != oled.activeAlbumart:
                oled.activeAlbumart = newAlbumart
                if AlbumArtHTTP and newFormat == 'WebRadio':
                    JPGSaveURL(newAlbumart)
                else:
                    albumdecode = urllib.parse.unquote(newAlbumart, encoding='utf-8', errors='replace')
                    JPGPathfinder(albumdecode)

def onPushCollectionStats(data):
    data = json.loads(data.decode("utf-8"))             #data import from REST-API (is set when ButtonD short-pressed in Standby)

    if "artists" in data:               #used for Media-Library-Infoscreen
        newArtists = data["artists"]
    else:
        newArtists = ''
    if newArtists is None:
        newArtists = ''

    if 'albums' in data:                #used for Media-Library-Infoscreen
        newAlbums = data["albums"]
    else:
        newAlbums = ''
    if newAlbums is None:
        newAlbums = ''

    if 'songs' in data:                 #used for Media-Library-Infoscreen
        newSongs = data["songs"]
    else:
        newSongs = ''
    if newSongs is None:
        newSongs = ''

    if 'playtime' in data:               #used for Media-Library-Infoscreen
        newPlaytime = data["playtime"]
    else:
        newPlaytime = ''
    if newPlaytime is None:
        newPlaytime = ''

    oled.activeArtists = str(newArtists) 
    oled.activeAlbums = str(newAlbums)
    oled.activeSongs = str(newSongs)
    oled.activePlaytime = str(newPlaytime)
	
    if oled.state == STATE_LIBRARY_INFO and oled.playState == 'info':                                   #this is the "Media-Library-Info-Screen"
       oled.modal.UpdateLibraryInfo() 

def onPushQueue(data):
    oled.queue = [track['name'] if 'name' in track else 'no track' for track in data]
#________________________________________________________________________________________
#________________________________________________________________________________________
#	
#    ____  _            __                  __  ___                _           
#   / __ \(_)________  / /___ ___  __      /  |/  /__  ____  __  _( )_____   _ 
#  / / / / / ___/ __ \/ / __ `/ / / /_____/ /|_/ / _ \/ __ \/ / / /// ___/  (_)
# / /_/ / (__  ) /_/ / / /_/ / /_/ /_____/ /  / /  __/ / / / /_/ / (__  )  _   
#/_____/_/____/ .___/_/\__,_/\__, /     /_/  /_/\___/_/ /_/\__,_/ /____/  (_)  
#            /_/            /____/                                             
#
class NowPlayingScreen():
    print("Inside NowPlayingScreen")
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        
    def UpdatePlayingInfo(self):
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        
    def UpdateStandbyInfo(self):
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def DrawOn(self, image):
        global ScrollArtistTag
        global ScrollArtistNext
        global ScrollArtistFirstRound
        global ScrollArtistNextRound
        global ScrollSongTag
        global ScrollSongNext
        global ScrollSongFirstRound
        global ScrollSongNextRound

        if newStatus != 'stop':
            self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
            self.ArtistWidth, self.ArtistHeight = self.draw.textsize(oled.activeArtist, font=font)
            self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
            if self.ArtistWidth >= self.width:
                if ScrollArtistFirstRound:
                    ScrollArtistFirstRound = False
                    ScrollArtistTag = 0
                    self.ArtistPosition = (Screen4text01)
                elif not ScrollArtistFirstRound and not ScrollArtistNextRound:
                    if ScrollArtistTag <= self.ArtistWidth - 1:
                        ScrollArtistTag += ArtistScrollSpeed
                        self.ArtistPosition = (-ScrollArtistTag ,Screen4text01[1])
                        ScrollArtistNext = 0
                    elif ScrollArtistTag == self.ArtistWidth:
                        ScrollArtistTag = 0
                        ScrollArtistNextRound = True
                        ScrollArtistNext = self.width + ArtistEndScrollMargin
                if ScrollArtistNextRound:        
                    if ScrollArtistNext >= 0:                    
                        self.ArtistPosition = (ScrollArtistNext ,Screen4text01[1])
                        ScrollArtistNext -= ArtistScrollSpeed
                    elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound:
                        ScrollArtistNext = 0
                        ScrollArtistNextRound = False
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen4text01)
            if self.ArtistWidth <= self.width:                  # center text
                self.ArtistPosition = (int((self.width-self.ArtistWidth)/2), Screen4text01[1])  
            self.draw.text((self.ArtistPosition), oled.activeArtist, font=font, fill='white')

            self.SongWidth, self.SongHeight = self.draw.textsize(oled.activeSong, font=font3)
            self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
            if self.SongWidth >= self.width:
                if ScrollSongFirstRound:
                    ScrollSongFirstRound = False
                    ScrollSongTag = 0
                    self.SongPosition = (Screen4text02)
                elif not ScrollSongFirstRound and not ScrollSongNextRound:
                    if ScrollSongTag <= self.SongWidth - 1:
                        ScrollSongTag += SongScrollSpeed
                        self.SongPosition = (-ScrollSongTag ,Screen4text02[1])
                        ScrollSongNext = 0
                    elif ScrollSongTag == self.SongWidth:
                        ScrollSongTag = 0
                        ScrollSongNextRound = True
                        ScrollSongNext = self.width + SongEndScrollMargin
                if ScrollSongNextRound:        
                    if ScrollSongNext >= 0:                    
                        self.SongPosition = (ScrollSongNext ,Screen4text02[1])
                        ScrollSongNext -= SongScrollSpeed
                    elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound:
                        ScrollSongNext = 0
                        ScrollSongNextRound = False
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen4text02)
            if self.SongWidth <= self.width:                  # center text
                self.SongPosition = (int((self.width-self.SongWidth)/2), Screen4text02[1])
            self.draw.text((self.SongPosition), oled.activeSong, font=font3, fill='white')
            self.draw.text((Screen4text28), oled.playstateIcon, font=labelfont, fill='white')
            if oled.duration != None:
                self.draw.text((Screen4text06), oled.activeFormat, font=font4, fill='white')
                self.draw.text((Screen4text07), str(oled.activeSamplerate), font=font4, fill='white')
                self.draw.text((Screen4text08), oled.activeBitdepth, font=font4, fill='white')
            else:
                self.draw.text((Screen4Text0008), oled.activeFormat, font=font4, fill='white')
                self.draw.text((Screen4text008), oled.bitrate, font=font4, fill='white')
            if oled.repeat:
                if not oled.repeatonce:
                    self.draw.text((Screen4text33), oledrepeat, font=labelfont, fill='white')
                if oled.repeatonce:
                    self.draw.text((Screen4text33), oledrepeat, font=labelfont, fill='white')
                    self.draw.text((Screen4text34), str(1), font=font4, fill='white')
            if oled.shuffle:
                self.draw.text((Screen4text35), oledshuffle, font=labelfont, fill='white')
            if not oled.mute:
                self.draw.text((Screen4text30), oledvolumeon, font=labelfontfa, fill='white')
            else:
                self.draw.text((Screen4text31), oledvolumeoff, font=labelfontfa, fill='white')
            # TODO Change volume to display PGA2320 Volume Level (bladelius.curVol)
            if oled.volume >= 0:
                #self.volume = 'Vol.: ' + str(oled.volume) + '%'
                self.volume = 'Vol.: ' + str(bladelius.curVol) + '%'
                self.draw.text((Screen4text29), self.volume, font=font4, fill='white')
            #self.draw.text((Screen4ActualPlaytimeText), str(timedelta(seconds=round(float(oled.seek) / 1000))), font=font4, fill='white')
            self.draw.text((Screen4ActualPlaytimeText), str(int(oled.seek / 1000)), font=font4, fill='white')
            if oled.duration != None:
                self.playbackPoint = oled.seek / oled.duration / 10
                self.bar = Screen2barwidth * self.playbackPoint / 100
                self.draw.text((Screen4DurationText), str(timedelta(seconds=oled.duration)), font=font4, fill='white')
                self.draw.rectangle((Screen4barLineX , Screen4barLineThick1, Screen4barLineX+Screen4barwidth, Screen4barLineThick2), outline=Screen4barLineBorder, fill=Screen4barLineFill)
                self.draw.rectangle((self.bar+Screen4barLineX-Screen4barNibbleWidth, Screen4barThick1, Screen4barX+self.bar+Screen4barNibbleWidth, Screen4barThick2), outline=Screen4barBorder, fill=Screen4barFill)
            image.paste(self.image, (0, 0))
#_____________________________________________________________________________________________________________
#   _____ __                  ____               _____                         
#  / ___// /_____ _____  ____/ / /_  __  __     / ___/_____________  ___  ____ 
#  \__ \/ __/ __ `/ __ \/ __  / __ \/ / / /_____\__ \/ ___/ ___/ _ \/ _ \/ __ \
# ___/ / /_/ /_/ / / / / /_/ / /_/ / /_/ /_____/__/ / /__/ /  /  __/  __/ / / /
#/____/\__/\__,_/_/ /_/\__,_/_.___/\__, /     /____/\___/_/   \___/\___/_/ /_/ 
#                                 /____/                                       
#_____________________________________________________________________________________________________________
        elif oled.playState == 'stop':
            self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
            #self.draw.text((oledtext03), oled.time, font=fontClock, fill='white')
            self.draw.text((oledtext04), oled.IP, font=fontIP, fill='white')
            self.draw.text((oledtext05), oled.date, font=fontDate, fill='white')
            self.draw.text((oledtext09), oledlibraryInfo, font=iconfontBottom, fill='white')
            image.paste(self.image, (0, 0))

class MediaLibrarayInfo():
    def __init__(self, height, width):
        self.height = height
        self.width = width

    def UpdateLibraryInfo(self):
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def DrawOn(self, image):
        self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
        self.draw.text((oledtext10), oled.activeArtists, font=font4, fill='white')
        self.draw.text((oledtext11), oled.activeAlbums, font=font4, fill='white')
        self.draw.text((oledtext12), oled.activeSongs, font=font4, fill='white')
        self.draw.text((oledtext13), oled.activePlaytime, font=font4, fill='white')
        self.draw.text((oledtext14), oledArt, font=font4, fill='white')
        self.draw.text((oledtext15), oledAlb, font=font4, fill='white')
        self.draw.text((oledtext16), oledSon, font=font4, fill='white')
        self.draw.text((oledtext17), oledPla, font=font4, fill='white')
        self.draw.text((oledtext19), oledlibraryReturn, font=iconfontBottom, fill='white')
        self.draw.text((oledtext20), oledArtistIcon, font=mediaicon, fill='white')
        self.draw.text((oledtext21), oledAlbumIcon, font=mediaicon, fill='white')            
        self.draw.text((oledtext22), oledSongIcon, font=mediaicon, fill='white')
        self.draw.text((oledtext23), oledPlaytimeIcon, font=mediaicon, fill='white')
        image.paste(self.image, (0, 0))

class OtherInputScreen():
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def UpdateInputScreen(self):
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def DrawOn(self, image):
        self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
        self.draw.text((10, 4), list(bladelius.theInputs.keys())[bladelius.curInput], font=fontClock, fill='white')
        self.draw.text((175, 4), str(bladelius.curVol), font=fontClock, fill='white')
        self.draw.text((oledtext04), oled.IP, font=fontIP, fill='white')
        self.draw.text((oledtext05), oled.date, font=fontDate, fill='white')
        self.draw.text((oledtext09), oledlibraryInfo, font=iconfontBottom, fill='white')
        image.paste(self.image, (0, 0))

class MenuScreen():
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.selectedOption = oled.playPosition
        self.menurows = oledListEntrys
        self.menuText = [None for i in range(self.menurows)]
        self.menuList = oled.queue
        self.totaloptions = len(oled.queue)
        self.onscreenoptions = min(self.menurows, self.totaloptions)
        self.firstrowindex = 0
        self.MenuUpdate()

    def MenuUpdate(self):
        self.firstrowindex = min(self.firstrowindex, self.selectedOption)
        self.firstrowindex = max(self.firstrowindex, self.selectedOption - (self.menurows-1))
        for row in range(self.onscreenoptions):
            if (self.firstrowindex + row) == self.selectedOption:
                color = "black"
                bgcolor = "white"
            else:
                color = "white"
                bgcolor = "black"
            optionText = self.menuList[row+self.firstrowindex]
            self.menuText[row] = StaticText(self.height, self.width, optionText, font2, fill=color, bgcolor=bgcolor)
        if self.totaloptions == 0:
            self.menuText[0] = StaticText(self.height, self.width, oledEmptyListText, font2, fill="white", bgcolor="black")
            
    def NextOption(self):
        self.selectedOption = min(self.selectedOption + 1, self.totaloptions - 1)
        self.MenuUpdate()

    def PrevOption(self):
        self.selectedOption = max(self.selectedOption - 1, 0)
        self.MenuUpdate()

    def SelectedOption(self):
        return self.selectedOption 

    def DrawOn(self, image):
        for row in range(self.onscreenoptions):
            self.menuText[row].DrawOn(image, (oledListTextPosX, row*oledListTextPosY))       #Here is the position of the list entrys from left set (42)
        if self.totaloptions == 0:
            self.menuText[0].DrawOn(image, (oledEmptyListTextPosition))                  #Here is the position of the list entrys from left set (42)

class ScreenSelectMenu():
    def __init__(self, height, width):
        self.height = height
        self.width = width
        index = ScreenList.index(NowPlayingLayout)
        self.selectedOption = int(index)
        self.menurows = oledListEntrys
        self.menuText = [None for i in range(self.menurows)]
        self.menuList = ScreenList
        self.totaloptions = len(ScreenList)
        self.onscreenoptions = min(self.menurows, self.totaloptions)
        self.firstrowindex = 0
        self.MenuUpdate()

    def MenuUpdate(self):
        self.firstrowindex = min(self.firstrowindex, self.selectedOption)
        self.firstrowindex = max(self.firstrowindex, self.selectedOption - (self.menurows-1))
        for row in range(self.onscreenoptions):
            if (self.firstrowindex + row) == self.selectedOption:
                color = "black"
                bgcolor = "white"
            else:
                color = "white"
                bgcolor = "black"
            optionText = self.menuList[row+self.firstrowindex]
            self.menuText[row] = StaticText(self.height, self.width, optionText, font2, fill=color, bgcolor=bgcolor)
        if self.totaloptions == 0:
            self.menuText[0] = StaticText(self.height, self.width, oledEmptyListText, font2, fill="white", bgcolor="black")
            
    def NextOption(self):
        self.selectedOption = min(self.selectedOption + 1, self.totaloptions - 1)
        self.MenuUpdate()

    def PrevOption(self):
        self.selectedOption = max(self.selectedOption - 1, 0)
        self.MenuUpdate()

    def SelectedOption(self):
        return self.selectedOption 

    def DrawOn(self, image):
        for row in range(self.onscreenoptions):
            self.menuText[row].DrawOn(image, (oledListTextPosX, row*oledListTextPosY))       #Here is the position of the list entrys from left set (42)
        if self.totaloptions == 0:
            self.menuText[0].DrawOn(image, (oledEmptyListTextPosition))                  #Here is the position of the list entrys from left set (42)

#________________________________________________________________________________________
#________________________________________________________________________________________
#	
#    ____        __  __                 ____                 __  _                      
#   / __ )__  __/ /_/ /_____  ____     / __/_  ______  _____/ /_(_)___  ____  _____   _ 
#  / __  / / / / __/ __/ __ \/ __ \   / /_/ / / / __ \/ ___/ __/ / __ \/ __ \/ ___/  (_)
# / /_/ / /_/ / /_/ /_/ /_/ / / / /  / __/ /_/ / / / / /__/ /_/ / /_/ / / / (__  )  _   
#/_____/\__,_/\__/\__/\____/_/ /_/  /_/  \__,_/_/ /_/\___/\__/_/\____/_/ /_/____/  (_)  
#                                                                                       	
def ButtonA_PushEvent(hold_time):
    oled.dimLevel += 1
    if oled.dimLevel == 4:
        oled.dimLevel = 0
        oled.hide()
    if oled.dimLevel == 1:
        oled.show()
    oled.contrast(dimLevels[oled.dimLevel])
    print('ButtonA short press event', oled.dimLevel)


def ButtonB_PushEvent(hold_time):
    if hold_time < 2:
        print('ButtonB short press event')
        bladelius.IRsignal.write(ecodes.EV_KEY, ecodes.KEY_PREVIOUS, 1)
        bladelius.IRsignal.write(ecodes.EV_SYN, ecodes.SYN_REPORT, 0)
        bladelius.IRsignal.write(ecodes.EV_KEY, ecodes.KEY_PREVIOUS, 0)
        bladelius.IRsignal.write(ecodes.EV_SYN, ecodes.SYN_REPORT, 0)

def ButtonC_PushEvent(hold_time):
    if hold_time < 2:
        bladelius.IRsignal.write(ecodes.EV_KEY, ecodes.KEY_NEXT, 1)
        bladelius.IRsignal.write(ecodes.EV_SYN, ecodes.SYN_REPORT, 0)
        bladelius.IRsignal.write(ecodes.EV_KEY, ecodes.KEY_NEXT, 0)
        bladelius.IRsignal.write(ecodes.EV_SYN, ecodes.SYN_REPORT, 0)

def ButtonD_PushEvent(hold_time):
    if hold_time < 2:
        print('ButtonD short press event')
        print('Current Standby State is', bladelius.standbyFlag)
        bladelius.standbyFlag ^= 1
        bladelius.changeOutputs(bladelius.standbyFlag)
        if bladelius.standbyFlag:
            oled.dimLevel = 0
            oled.hide()
        else:
            oled.dimLevel = 3
            oled.show()
            oled.contrast(dimLevels[oled.dimLevel])


def RightKnob_RotaryEvent(dir):
    global emit_track
    oled.stateTimeout = 6.0
    print("Inside RightKnob_RotaryEvent", dir)
    if oled.state == STATE_PLAYER:
        SetState(STATE_QUEUE_MENU)
    elif oled.state == STATE_QUEUE_MENU and dir == RotaryEncoder.LEFT:
        oled.modal.PrevOption()
        oled.selQueue = oled.modal.SelectedOption()
        emit_track = True
    elif oled.state == STATE_QUEUE_MENU and dir == RotaryEncoder.RIGHT:
        oled.modal.NextOption()
        oled.selQueue = oled.modal.SelectedOption()
        emit_track = True
    elif oled.state == STATE_SCREEN_MENU and dir == RotaryEncoder.LEFT:
        oled.modal.PrevOption()
        oled.SelectedScreen = oled.modal.SelectedOption()
    elif oled.state == STATE_SCREEN_MENU and dir == RotaryEncoder.RIGHT:
        oled.modal.NextOption()
        oled.SelectedScreen = oled.modal.SelectedOption()
    # This isn't used anymore, moved to bdgremote and events
    elif oled.state == STATE_OTHER_INPUT:
        if dir == RotaryEncoder.LEFT:
            if (bladelius.curVol >= bladelius.volMax):
                bladelius.curVol = bladelius.volMax
            else:
                bladelius.curVol += bladelius.volStep
        else:
            if (bladelius.curVol <= 0):
                bladelius.curVol = 0
            else:
                bladelius.curVol -= bladelius.volStep
        print("Current volume is (from bladelius.py): ", bladelius.curVol)
        dbVol = bladelius.volTable[bladelius.curVol]
        bladelius.pga2320.writebytes([dbVol, dbVol, dbVol, dbVol]) # 1 PGA2320/channel so 4 writes

def RightKnob_PushEvent(hold_time):
    if hold_time < 1:
        if oled.state == STATE_QUEUE_MENU:
            print ('RightKnob_PushEvent SHORT')
            oled.stateTimeout = 0
        if oled.state == STATE_SCREEN_MENU:
            print ('RightKnob_PushEvent Long')
            global NowPlayingLayout
            oled.SelectedScreen = oled.modal.SelectedOption()
            Screen = ScreenList[oled.SelectedScreen]
            WriteSelScreen = open('/home/volumio/bladelius/ConfigurationFiles/LayoutSet.txt', 'w')
            WriteSelScreen.write(Screen)
            WriteSelScreen.close
            NowPlayingLayout = Screen
            SetState(STATE_PLAYER)
            volumioIO.emit('stop') 
#________________________________________________________________________________________
#________________________________________________________________________________________
#    
#    ____        __  __                  _       __      __       __                  
#   / __ )__  __/ /_/ /_____  ____      | |     / /___ _/ /______/ /_  ___  _____   _ 
#  / __  / / / / __/ __/ __ \/ __ \_____| | /| / / __ `/ __/ ___/ __ \/ _ \/ ___/  (_)
# / /_/ / /_/ / /_/ /_/ /_/ / / / /_____/ |/ |/ / /_/ / /_/ /__/ / / /  __/ /     _   
#/_____/\__,_/\__/\__/\____/_/ /_/      |__/|__/\__,_/\__/\___/_/ /_/\___/_/     (_)  
#   
ButtonA_Push = PushButton(oledBtnA, max_time=2)
ButtonA_Push.setCallback(ButtonA_PushEvent)
ButtonB_Push = PushButton(oledBtnB, max_time=2)
ButtonB_Push.setCallback(ButtonB_PushEvent)
ButtonC_Push = PushButton(oledBtnC, max_time=2)
ButtonC_Push.setCallback(ButtonC_PushEvent)
ButtonD_Push = PushButton(oledBtnD, max_time=2)
ButtonD_Push.setCallback(ButtonD_PushEvent)

# Using overlay and events
#RightKnob_Push = PushButton(oledRtrBtn, max_time=2)
#RightKnob_Push.setCallback(RightKnob_PushEvent)
#RightKnob_Rotation = RotaryEncoder(oledRtrLeft, oledRtrRight, pulses_per_cycle=4)
#RightKnob_Rotation.setCallback(RightKnob_RotaryEvent)
#________________________________________________________________________________________
#________________________________________________________________________________________
#    
#    ____              __        __                          
#   / __ )____  ____  / /_      / /   ____  ____ _____     _ 
#  / __  / __ \/ __ \/ __/_____/ /   / __ \/ __ `/ __ \   (_)
# / /_/ / /_/ / /_/ / /_/_____/ /___/ /_/ / /_/ / /_/ /  _   
#/_____/\____/\____/\__/     /_____/\____/\__, /\____/  (_)  
#    
show_logo(oledBootLogo, oled)
if ledActive and firstStart:
    SysStart()
#show_logo(oled1BootLogo, oled)
#show_logo2(oled2BootLogo, oled2)
if ledActive and firstStart:
    Processor = threading.Thread(target=CPUload, daemon=True)
    Processor.start()
    firstStart = False
else: 
    firstStart = False
#sleep(2.0)
sleep(1)
SetState(STATE_PLAYER)
#________________________________________________________________________________________
#________________________________________________________________________________________
#  
#   __  __          __      __          ________                        __         
#  / / / /___  ____/ /___ _/ /____     /_  __/ /_  ________  ____ _____/ /____   _ 
# / / / / __ \/ __  / __ `/ __/ _ \     / / / __ \/ ___/ _ \/ __ `/ __  / ___/  (_)
#/ /_/ / /_/ / /_/ / /_/ / /_/  __/    / / / / / / /  /  __/ /_/ / /_/ (__  )  _   
#\____/ .___/\__,_/\__,_/\__/\___/    /_/ /_/ /_/_/   \___/\__,_/\__,_/____/  (_)  
#    /_/ 
#     
updateThread = Thread(target=display_update_service)
updateThread.daemon = True
updateThread.start()

def _receive_thread():
    volumioIO.wait()

receive_thread = Thread(target=_receive_thread)
receive_thread.daemon = True
receive_thread.start()

volumioIO.on('pushState', onPushState)
volumioIO.on('pushQueue', onPushQueue)

# get list of Playlists and initial state
volumioIO.emit('listPlaylist')
volumioIO.emit('getState', '', onPushState)
volumioIO.emit('getQueue', '', onPushQueue)

sleep(0.1)

try:
    with open('oledConfigurationFiles.json', 'r') as f:   #load last playing track number
        config = json.load(f)
except IOError:
    pass
else:
    oled.playPosition = config['track']
    
#if oled.playState != 'play':
#    volumioIO.emit('play', {'value':oled.playPosition})

InfoTag = 0                         #helper for missing Artist/Song when changing sources
GetIP()

def PlaypositionHelper():
    while True:
        if newStatus != 'stop':
            volumioIO.emit('getState', '', onPushState)
            now = datetime.now()
            oled.date = now.strftime("%d.%m.%Y")
        sleep(1.0)

PlayPosHelp = threading.Thread(target=PlaypositionHelper, daemon=True)
PlayPosHelp.start()

remoteProcess = threading.Thread(target=bladelius.listenRemote, daemon=True)
remoteProcess.start()
#________________________________________________________________________________________
#________________________________________________________________________________________
#	
#    __  ___      _             __                          
#   /  |/  /___ _(_)___        / /   ____  ____  ____     _ 
#  / /|_/ / __ `/ / __ \______/ /   / __ \/ __ \/ __ \   (_)
# / /  / / /_/ / / / / /_____/ /___/ /_/ / /_/ / /_/ /  _   
#/_/  /_/\__,_/_/_/ /_/     /_____/\____/\____/ .___/  (_)  
#  
while True:
#    print('State: ', oled.state)
#    print('palyState: ', oled.playState)
#    print('newStatus: ', newStatus)
#    print(oled.modal)
    if emit_track and oled.stateTimeout < 4.5:
        emit_track = False
        try:
            SetState(STATE_PLAYER)
            InfoTag = 0
        except IndexError:
            pass
        volumioIO.emit('stop')
        sleep(0.01)
        volumioIO.emit('play', {'value':oled.selQueue})
    sleep(0.1)

#this is the loop to push the actual time every 0.1sec to the "Standby-Screen"
    if oled.state == STATE_PLAYER and newStatus == 'stop' and not oled.ShutdownFlag:
        InfoTag = 0  #resets the InfoTag helper from artist/song update loop
        oled.state = 0
        oled.time = strftime("%H:%M:%S")
        SetState(STATE_PLAYER)
        oled.modal.UpdateStandbyInfo()
        sleep(0.2)  

#if playback is paused, here is defined when the Player goes back to "Standby"/Stop		
    if oled.state == STATE_PLAYER and newStatus == 'pause' and varcanc:
        secvar = int(round(time()))
        varcanc = False
    elif oled.state == STATE_PLAYER and newStatus == 'pause' and int(round(time())) - secvar > oledPause2StopTime:
        varcanc = True
        volumioIO.emit('stop')
        oled.modal.UpdateStandbyInfo()
        secvar = 0.0

# This is for the added remote code
    if not bladelius.events.empty():
        event = bladelius.events.get_nowait()
        if bladelius.curInput != selectedInput:
            if list(bladelius.theInputs.keys())[bladelius.curInput] == 'STREAM':
                volumioIO.emit('getState', '', onPushState)
                SetState(STATE_PLAYER)
                print("curInput is volumio", oled.state, newStatus)
                oled.modal.UpdatePlayingInfo()
            else: # TODO Only need to change state once
                SetState(STATE_OTHER_INPUT)
            #print("the event is", event)
            print("End of the loop and curVol is", bladelius.curVol)
            selectedInput = bladelius.curInput

sleep(0.02)
