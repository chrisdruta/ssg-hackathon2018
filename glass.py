import sys, os
import time
import math
import pyowm
import random
import requests
import operator
from datetime import datetime

from PIL import Image
from PIL import ImageFont
from PIL import ImageStat
from PIL import ImageDraw

import webcolors

from picamera import PiCamera
from io import BytesIO

import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

import orientation_data as orient

# Raspberry Pi pin configuration:
RST = 24
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

stateList = ['wait', 'time', 'temp', 'pic', 'ped', 'space',
                '3D', 'acc', 'bio', 'color', 'meme']

# Track state
pos = 0

# Camrea Module stuff
stream = BytesIO()
camera = PiCamera()

# Button Allias
pin_Prev = 26
pin_Action = 21
pin_Next = 18

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_Next, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_Prev, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_Action, GPIO.IN, pull_up_down=GPIO.PUD_UP)

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, sclk=11, din=10, cs=8)

def checkEvent():
    # Getting button events
    get_Next = GPIO.input(pin_Next)
    get_Prev = GPIO.input(pin_Prev)
    get_Action = GPIO.input(pin_Action)

    get_Next_move = orient.checkpos(0)
    get_Prev_move = orient.checkpos(1)
    
    global pos

    # Handlers
    if not get_Next or get_Next_move:
        print("Current state: " + stateList[pos])
        if pos == len(stateList) - 1:
            pos = 0
        else:
            pos += 1
        print("New state: " + stateList[pos])
        time.sleep(0.3)

        # Next signal
        return 1

    if not get_Prev or get_Prev_move:
        print("Current state: " + stateList[pos])
        if pos == 0:
            pos = len(stateList) - 1
        else:
            pos -= 1
        print("New state: " + stateList[pos])
        time.sleep(0.3)

        # Prev signal
        return 2

    if not get_Action:
        print("Action!")
        time.sleep(0.3)

        # Action signal
        return 3

    # No event signal
    return 0

# Normalizing colors (by fraxel from stackoverflow)
def closestColor(requestedColor):
    min_colors = {}
    for key, name in webcolors.css3_hex_to_names.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requestedColor[0]) ** 2
        gd = (g_c - requestedColor[1]) ** 2
        bd = (b_c - requestedColor[2]) ** 2
        min_colors[(rd + gd + bd)] = name
    return min_colors[min(min_colors.keys())]

def getColorName(requestedColor):
    try:
        closestName = actualName = webcolors.rgb_to_name(requestedColor)
    except ValueError:
        closestName = closestColor(requestedColor)
        actualName = None
    return actualName, closestName

# Display stuff
disp.begin()
disp.clear()
disp.display()

##########################
#
#   MAIN LOOOOOP ;)
#
##########################

while True:
    checkEvent()

    #Welcome
    if pos == 0:
        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break

            image = Image.new('1', (128, 64))
            font = ImageFont.truetype("DejaVuSansMono.ttf", 18)
            draw = ImageDraw.Draw(image)

            draw.text((0,0), "Welcome", fill="white", font=font)
            draw.text((0,32), "Hacker!", fill="white", font=font)

            disp.image(image.transpose(Image.FLIP_LEFT_RIGHT))
            disp.display()

    # Time
    if pos == 1:
        today_last_time = "Unknown"
        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break
            now = datetime.now()
            today_date = now.strftime("%d %b %y")
            today_time = now.strftime("%H:%M:%S")

            if today_time != today_last_time:
                today_last_time = today_time
                now = datetime.now()
                today_date = now.strftime("%d %b %y")

                margin = 4

                cx = 30
                cy = min(64, 64) / 2

                left = cx - cy
                right = cx + cy

                p = lambda ang, arm: (int(math.cos(math.radians(ang)) * arm),
                                        int(math.sin(math.radians(ang)) * arm))

                hrs_angle = 270 + (30 * (now.hour + (now.minute / 60.0)))
                hrs = p(hrs_angle, cy - margin - 7)

                min_angle = 270 + (6 * now.minute)
                mins = p(min_angle, cy - margin - 2)

                sec_angle = 270 + (6 * now.second)
                secs = p(sec_angle, cy - margin - 2)

                image = Image.new('1', (128, 64))
                font = ImageFont.truetype("DejaVuSansMono.ttf", 32)
                draw = ImageDraw.Draw(image)

                draw.ellipse((left + margin, margin, right - margin, min(64, 64) - margin), outline="white")
                draw.line((cx, cy, cx + hrs[0], cy + hrs[1]), fill="white")
                draw.line((cx, cy, cx + mins[0], cy + mins[1]), fill="white")
                draw.line((cx, cy, cx + secs[0], cy + secs[1]), fill="white")
                draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill="white", outline="white")
                draw.text((2 * (cx + margin), cy - 8), today_date, fill="white")
                draw.text((2 * (cx + margin), cy), today_time, fill="white")

                disp.image(image.transpose(Image.FLIP_LEFT_RIGHT))
                disp.display()

    # Temp
    if pos == 2:
        image = Image.new('1', (128, 64))
        font = ImageFont.truetype("DejaVuSansMono.ttf", 16)
        draw = ImageDraw.Draw(image)

        owm = pyowm.OWM('e7224b9e6a89aba889c4cca22af779c4')
        observation =  owm.weather_at_place('Tucson,AZ,USA')
        w = observation.get_weather()
        temp = w.get_temperature('fahrenheit')
        temp2 = w.get_temperature('celsius')

        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break

            draw.text((0,0), str(temp['temp']) + " F", fill="white", font=font)
            draw.text((0,32), str(temp2['temp']) + " C", fill="white", font=font)

            disp.image(image.transpose(Image.FLIP_LEFT_RIGHT))
            disp.display()

    # Picture
    if pos == 3:

        image = Image.new('1', (128, 64))
        font = ImageFont.truetype("DejaVuSansMono.ttf", 12)
        draw = ImageDraw.Draw(image)

        draw.text((5,5), "Click to take", fill = "white", font=font)
        draw.text((5,20), "a pic! ;)", fill = "white", font=font)

        disp.image(image.transpose(Image.FLIP_LEFT_RIGHT))
        disp.display()

        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break

            elif e == 3:
                camera.capture(stream, format='jpeg')
                image = Image.open(stream)
                
                image_bw = image.resize((128,64), Image.BICUBIC).convert('1')

                disp.image(image_bw.transpose(Image.FLIP_LEFT_RIGHT))
                disp.display()
                stream = BytesIO()

    # Pedometer
    if pos == 4:
        numSteps = 0
        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break
            if orient.checkpos(69):
                numSteps += 1
            
            image = Image.new('1', (128, 64))
            font = ImageFont.truetype("DejaVuSansMono.ttf", 16)
            draw = ImageDraw.Draw(image)

            draw.text((0,0), "Steps: ", fill="white", font=font)
            font = ImageFont.truetype("DejaVuSansMono.ttf", 14)
            draw.text((0,20), str(numSteps), fill="white", font=font)

            disp.image(image.transpose(Image.FLIP_LEFT_RIGHT))
            disp.display()

    # Space
    if pos == 5:
        r = requests.get('http://www.howmanypeopleareinspacerightnow.com/peopleinspace.json',
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'})

        try:
            string = str(r.json()['number'])
        except:
            string = "Error"

        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break
            
            image = Image.open("moon.ppm")
            font = ImageFont.truetype("DejaVuSansMono.ttf", 10)
            draw = ImageDraw.Draw(image)

            draw.text((4,0), "There are", fill="white", font=font)
            draw.text((4,26), string + " people", fill="white", font=font)
            draw.text((4,52), "in space!", fill="white", font=font)

            disp.image(image.transpose(Image.FLIP_LEFT_RIGHT))
            disp.display()

    # 3D
    if pos == 6:
        image = Image.new('1', (128, 64))
        font = ImageFont.truetype("DejaVuSansMono-Oblique.ttf", 16)
        draw = ImageDraw.Draw(image)

        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break

            draw.text((5,5), "3D: WIP", fill="white", font=font)
            
            disp.image(image.transpose(Image.FLIP_LEFT_RIGHT))
            disp.display()

    # Accident
    if pos == 7:
        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break
            image = Image.new('1', (128, 64))
            font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", 16)
            draw = ImageDraw.Draw(image)

            draw.text((0,0), "CAUTION", fill = "white", font=font)
            font = ImageFont.truetype("DejaVuSansMono.ttf", 12)
            draw.text((0,20), "Car Crash in 2min", fill="white", font=font)

            disp.image(image.transpose(Image.FLIP_LEFT_RIGHT))
            disp.display()

    # Biometrics
    if pos == 8:
        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break
            image = Image.new('1', (128, 64))
            font = ImageFont.truetype("DejaVuSansMono.ttf", 14)
            draw = ImageDraw.Draw(image)

            draw.text((0,0), "HR: 97bpm", fill = "white", font=font)
            draw.text((0,32), "GL: 90mg/dL", fill="white", font=font)

            disp.image(image.transpose(Image.FLIP_LEFT_RIGHT))
            disp.display()

    # Color picker
    # TODO: finish
    if pos == 9:
        r = 400 # 1/3rd of sensor height
        o = (1920/2, 1080/2)
        s = (128/2, 64/2)        

        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break

            # Change radius
            if e == 3:
                if r/ 2 < 100:
                    r = 800
                else:
                    r /= 2

            image = Image.new('1', (128, 64))
            font = ImageFont.truetype("DejaVuSansMono.ttf", 10)
            draw = ImageDraw.Draw(image)
                
            # Draw crosshair
            draw.line((s[0], s[1], s[0] + r/40, s[1]), fill="white")
            draw.line((s[0], s[1], s[0], s[1] + r/40), fill="white")
            draw.line((s[0], s[1], s[0] - r/40, s[1]), fill="white")
            draw.line((s[0], s[1], s[0], s[1] - r/40), fill="white")

            # Capture image and calculate avg color
            camera.capture(stream, format='jpeg')
            cap = Image.open(stream)

            cap.crop((o[0] - r, o[1] - r, o[0] + r, o[1] + r))
            stream = BytesIO()

            rgb = ImageStat.Stat(cap).mean
            rgb = (int(rgb[0]), int(rgb[1]), int(rgb[2]))

            draw.text((5,48), "Color: " + getColorName(rgb)[1], fill="white", font=font)

            disp.image(image.transpose(Image.FLIP_LEFT_RIGHT))
            disp.display()

    # Memes
    if pos == 10:
        while True:
            e = checkEvent()
            if e == 1 or e == 2:
                break
            filename = random.choice(os.listdir("./dank"))
            image = Image.open("./dank/" + filename)
            image_r = image.resize((128,64), Image.BICUBIC)
            image_bw = image_r.convert('1')
            disp.image(image_bw.transpose(Image.FLIP_LEFT_RIGHT))
            disp.display()