import network
import time

#connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("Network Name", "Password")

#init eink display
from driver import EPD_2in13_V4_Landscape
epd = EPD_2in13_V4_Landscape()
epd.Clear()
epd.fill(0xFF)
epd.text("Waiting to connect...", 5, 5, 0x00)
epd.display(epd.buffer) 

#wait until connected
while not wlan.isconnected() and wlan.status() >= 0:
    time.sleep(1)

import urequests
import ujson
import utime

#pull current time from jsontest.com
timeReq = urequests.get("http://date.jsontest.com")
time = timeReq.json()['milliseconds_since_epoch']
timeReq.close()
time = (time / 1000.0) - (60*60*6) #gmt -6
timeParts = utime.gmtime(int(time))
timeParts = (timeParts[0], timeParts[1], timeParts[2], 0, timeParts[3], timeParts[4], timeParts[5], 0)
print(timeParts)
#set internal clock
rtc = machine.RTC()
rtc.datetime(timeParts)

from utime import localtime
from utime import sleep

#other prompts I was playing around with.  Most other ones gave the same boring answers
prompts = [
    { 'role': 'You are a poet, specializing in two-line poems.  You only return the poem in your responses.  The poem must always contain the current time.', 'prompt': 'The current time is {}' },
    #{ 'role': 'You are a historian, able to give a summary of a single event that happened in the past on a specific date.  The summary must be shorter than 256 characters.', 'prompt': 'What happened in the past on {}?' },
    #{ 'role': 'You are a comedian, specializing in short jokes. Your joke must be shorter than 256 characters.', 'prompt': 'Tell me a joke!' },
    #{ 'role': 'You are a historian, able to identify famous people\'s birthdays. Identify a famous person born on the request day, and include a quote from them. Your response must be shorter than 256 characters.', 'prompt': 'Who was born on {}?' }
]

months = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

while True:
    now = localtime()
    dt = "{:04d}/{:02d}/{:02d} {}:{:02d} {}".format(now[0], now[1], now[2], (now[3] - 12 if now[3] > 12 else now[3]), now[4], ("PM" if now[3] >= 12 else "AM"))
    date = "{} {}".format(months[now[1]], now[2])
    
    #if it's not working hours, just show a generic message
    if(now[3] < 8 or now[3] >= 16):
        epd.fill(0xff)
        epd.text(dt, 5, 10, 0x00)
        epd.text('You shouldn\'t be at your', 19, 51, 0x00)
        epd.text('desk right now...', 57, 68, 0x00)
        epd.init()
        epd.display(epd.buffer)
        epd.sleep()
        sleep(60)
        continue

    #change this if you want to pick a different prompt each time
    promptKey = 0 #now[4] % len(prompts)    

    data = ujson.dumps({ 'model': 'gpt-4-turbo-preview', 'temperature': 1.4, 'messages': [ { 'role': 'system', 'content': prompts[promptKey]['role'] }, { 'role': 'user', 'content': prompts[promptKey]['prompt'].format(dt) }]})
    chat = urequests.post("https://api.openai.com/v1/chat/completions", headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {put your key here}'}, data = data)
    response = chat.json()
    if not 'choices' in response:
        print(response)
        continue
    fullpoem = chat.json()['choices'][0]['message']['content']
    chat.close()
    #some formatting of the generated text
    poem = ' / '.join([line.strip().rstrip(',').replace("’", "'").replace("—", "-") for line in fullpoem.splitlines() if line])
    epd.fill(0xff)
    epd.text(dt, 5, 10, 0x00)
    #break generated text into lines that fit on display
    lines = []
    while(len(poem) > 32):
        lineIndex = poem.rindex(' ', 0, 32)
        lines.append(poem[0:lineIndex].strip())
        poem = poem[lineIndex:]
    lines.append(poem.strip())
    row = 1
    #calculate center of poem area (not including datetime header)
    textsize = len(lines) * 15
    avail = 122 - textsize
    offset = int(avail / 2)
    #print each line
    for line in lines:
        rowavail = 250 - (len(line) * 8)
        rowoffset = int(rowavail / 2)
        epd.text(line, rowoffset, (offset + row * 15), 0x00)
        row += 1
    epd.init()
    epd.display(epd.buffer)
    print(fullpoem)
    epd.sleep()
    now = localtime()
    #wait until next minute
    sleep(60 - now[5])