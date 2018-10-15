#!/usr/bin/env python3

"""
Created by Tennyson T Bardwell, ttb33@cornell.edu, on 2018-10-07

Copyright 2018 Tennyson T Bardwell

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import pygame, datetime, threading, time, csv
from pygame.locals import *

name = input('Filename: ')

# set up pygame and display a gui
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption('Pygame Keyboard Test')
pygame.mouse.set_visible(0)


exit_flag = None
focus = 'away'  # left, right, awway
last_change = datetime.datetime.now()
last_log_timestamp = last_change
log = [['focus', 'timestamp', 'time since last action', 'total away time',
       'total left time', 'total right time']]

time_spent = {
    'away': datetime.timedelta(),
    'left': datetime.timedelta(),
    'right': datetime.timedelta()
}

def format(delta):
    return '{}.{}'.format(delta.seconds, delta.microseconds)

def append_log(action, time_):
    global last_log_timestamp
    delta = time_ - last_log_timestamp
    last_log_timestamp = time_
    log.append([action,
                format(delta),
                format(time_spent['away']),
                format(time_spent['left']),
                format(time_spent['right']),])

append_log(focus, last_change)

def display():
    print('\n\n\nCurrent focus: ', focus)
    for k,v in time_spent.items():
        print('Time spent {}: {} seconds'.format(k, format(v)))

def update(new_focus=None):
    global last_change, focus, exit_flag

    current_time = datetime.datetime.now()
    delta = (current_time - last_change)
    time_spent[focus] += delta
    last_change = current_time

    if new_focus is None:
        new_focus = focus
    elif new_focus != focus:
        append_log(new_focus, current_time)

    focus = new_focus

    if time_spent['left'] + time_spent['right'] > datetime.timedelta(seconds=20):
        display()
        print('Exiting cleanly!')
        exit_flag = 'clean'


def threaded_function():
    global exit_flag
    while True:
        for event in pygame.event.get():
            # display()
            if (event.type == KEYUP) or (event.type == KEYDOWN):
                if event.key in { 27, 113 }:
                    # q, escape
                    print("Saw an exit key, quitting the program without saving")
                    exit_flag = 'abort'
                    exit()

                if event.key == 276:
                    # left arrow key
                    update('left')

                if event.key == 275:
                    # right arrow key
                    update('right')

                if event.key == 273:
                    # up arrow key
                    update('away')

thread = threading.Thread(target = threaded_function)
thread.daemon = True
thread.start()

while True:
    if exit_flag == 'clean':
        # import json; print(json.dumps(log, indent=4))
        append_log('finish', datetime.datetime.now())
        with open("{}.csv".format(name), "w") as f:
            writer = csv.writer(f)
            writer.writerows(log)
        pygame.mixer.music.load("beep.mp3")
        pygame.mixer.music.play()
        time.sleep(1)
        exit()
    elif exit_flag == 'abort':
        exit()
    update()
    display()
    time.sleep(0.1)

