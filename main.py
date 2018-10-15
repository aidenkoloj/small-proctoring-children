#!/usr/bin/env python3

"""
Created by Tennyson T Bardwell, tennysontaylorbardwell@gmail.com, on 2018-10-07

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
import curses, datetime, threading, time, csv, argparse, textwrap


SECOND = datetime.timedelta(seconds=1)


exit_flag = False
wait_for_continue = False
stdscr = None


def setup_curses():
    global stdscr
    stdscr = curses.initscr()
    stdscr.clear()
    stdscr.refresh()


def format(delta):
    return '{}.{}'.format(delta.seconds, delta.microseconds)


class Trial:
    def __init__(self,
                 trial_name,
                 prompt,
                 time_looking_at_images=None,
                 time_after_looking_at_an_image=None,
                 min_time_looking_at_an_image=None):

        if time_looking_at_images is None and \
           time_after_looking_at_an_image is None:
            raise ValueError('Trial "{}" will never end'.format(trial_name))

        self.trial_name = trial_name
        self.prompt = prompt
        self.time_looking_at_images = time_looking_at_images
        self.time_after_looking_at_an_image = time_after_looking_at_an_image
        self.min_time_looking_at_an_image = min_time_looking_at_an_image


    def append_log(self, action, time_):
        delta = time_ - self.last_log_timestamp
        self.last_log_timestamp = time_
        self.log.append([action,
                    format(delta),
                    format(self.time_spent['away']),
                    format(self.time_spent['left']),
                    format(self.time_spent['right']),])

    def start(self):
        self.time_spent = {
            'away': datetime.timedelta(),
            'left': datetime.timedelta(),
            'right': datetime.timedelta()
        }
        self.focus = 'away'  # left, right, awway
        self.last_change = datetime.datetime.now()
        self.first_look_at_image = None
        self.last_log_timestamp = self.last_change
        self.log = [['focus', 'timestamp', 'time since last action',
                     'total away time', 'total left time', 'total right time']]
        self.append_log(self.focus, self.last_change)

    def show_prompt(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        stdscr.addstr(height // 2 - 3, 0, self.trial_name)
        stdscr.addstr(height // 2 - 2, 0, '=' * len(self.trial_name))
        stdscr.addstr(height // 2 - 0, 0, '(press SPACE to continue)')
        for i,line in enumerate(self.prompt.split('\n')):
            stdscr.addstr(height // 2 + 2 + i, 0, line)
        stdscr.refresh()
    
    def display(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.addstr(height // 2, 0, 'Current focus: ' + self.focus)
        for i,(k,v) in enumerate(self.time_spent.items()):
            stdscr.addstr(height // 2 + i + 1, 0,
                        'Time spent {}: {} seconds'.format(k, format(v)))
        stdscr.refresh()

    def update(self, new_focus=None):
        current_time = datetime.datetime.now()
        delta = (current_time - self.last_change)
        self.time_spent[self.focus] += delta
        self.last_change = current_time

        if new_focus is None:
            new_focus = self.focus
        elif new_focus != self.focus:
            self.append_log(new_focus, current_time)
            # keep track of when they first look at the image
            if self.first_look_at_image is None:
                self.first_look_at_image = current_time

        self.focus = new_focus

        image_time = self.time_spent['left'] + self.time_spent['right'] 
        if self.first_look_at_image is None:
            look_time = datetime.timedelta()
        else:
            look_time = current_time - self.first_look_at_image

        save = lambda: self.append_log('finish', datetime.datetime.now())
        if self.time_looking_at_images and \
           image_time > self.time_looking_at_images:
            save()
            return 'success'

        elif self.time_after_looking_at_an_image and \
           look_time > self.time_after_looking_at_an_image:
            if self.min_time_looking_at_an_image is not None and \
               image_time < self.min_time_looking_at_an_image:
                save()
                return 'failed'
            else:
                save()
                return 'success'
        else:
            return 'running'


def receive_keys(callback):
    global exit_flag
    while True:
        k = stdscr.getch()
        if k == ord('q'):  # q key and esc key
            print("Saw an exit key, quitting the program without saving")
            exit_flag = True
            exit()
        elif k == curses.KEY_UP:
            callback('away')
        elif k == curses.KEY_RIGHT:
            callback('right')
        elif k == curses.KEY_LEFT:
            callback('left')
        elif k == ord(' '):
            callback('continue')

def get_trials():
    yield Trial(
        trial_name='Trial 1',
        prompt=textwrap.dedent('''\
        A child will be presented with two images

        Press the LEFT ARROW KEY when the child looks at the LEFT IMAGE

        Press the RIGHT ARROW KEY when the child looks at the RIGHT IMAGE

        Press the UP ARROW KEY when the child looks AWAY from both images.\
        '''),
        time_looking_at_images=2 * SECOND,
        time_after_looking_at_an_image=None,
        min_time_looking_at_an_image=None)

def main(stdscr_):
    global stdscr, exit_flag, wait_for_continue
    stdscr = stdscr_
    setup_curses()

    current_trial = None
    def handle_key(key):
        global wait_for_continue
        if current_trial is not None and key in {'away', 'right', 'left'}:
            current_trial.update(new_focus=key)
        elif key == 'continue':
            wait_for_continue = False

    thread = threading.Thread(target=receive_keys, args=[handle_key])
    thread.daemon = True
    thread.start()

    for trial in get_trials():
        global wait_for_continue

        wait_for_continue = True
        trial.show_prompt(stdscr)
        while wait_for_continue:
            if exit_flag:
                exit()

        trial.start()
        current_trial = trial
        while True:
            if exit_flag:
                exit()

            res = trial.update()
            trial.display(stdscr_)

            if res in {'success', 'failed'}:
                if res == 'success':
                    name = "{}.csv".format(trial.trial_name)
                else:
                    name = '{}_failed_{}.csv'.format(
                        trial.trial_name, datetime.now())
                with open(name, "w") as f:
                    writer = csv.writer(f)
                    writer.writerows(trial.log)
                break

            time.sleep(0.05)


if __name__ == '__main__':
    curses.wrapper(main)
