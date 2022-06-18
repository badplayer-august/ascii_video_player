import array
import cv2
import argparse
import math
from curses import wrapper
from threading import Event, Thread, Lock

parser = argparse.ArgumentParser()
parser.add_argument('-n','--name', default='video.mp4')
# parser.add_argument('-i', '--info', default=0, type=bool)
args = parser.parse_args()

ascii_grayscale = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@']
binning = 256/len(ascii_grayscale)
TO_ASCII = []


for i in range(256):
    TO_ASCII.append(ascii_grayscale[int(i//binning)])

# TO_ASCII = array.array('b', TO_ASCII)
buffer = []
is_end = False
is_finish = False
access_buffer = Lock()
not_full = Event()
not_full.set()
not_update = Event()

class BufferFrame(Thread):
    BUFFER_SIZE = 64

    def __init__(self, video, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.video = video

    def run(self):
        global buffer
        global is_end
        global access_buffer
        global not_full

        for _ in range(int(self.video.get(7))):
            has_frames, frame = self.video.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            not_full.wait()
            with access_buffer:
                buffer.append(frame)

            if len(buffer) == self.BUFFER_SIZE:
                not_full.clear()

        is_end = True

class UpdateScreen(Thread):
    def __init__(self, stdscr, frame_width_rate, frame_height_rate, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stdscr = stdscr
        self.frame_width_rate = frame_width_rate
        self.frame_height_rate = frame_height_rate

    def run(self):
        global buffer
        global is_end
        global access_buffer
        global not_full
        global not_update
        global is_finish

        while not (is_end and len(buffer) == 0):
            self.stdscr.erase()
            scr_height, scr_width = self.stdscr.getmaxyx()
            if scr_height*self.frame_width_rate < scr_width*self.frame_height_rate:
                resize_rate = scr_height//self.frame_height_rate
            else:
                resize_rate = scr_width//self.frame_width_rate

            resize_frame_height = int(resize_rate*self.frame_height_rate)
            resize_frame_width = int(resize_rate*self.frame_width_rate)
            padding_y = int(scr_height - resize_frame_height)>>1
            padding_x = int(scr_width - resize_frame_width)>>1

            while len(buffer) == 0: continue
            with access_buffer:
                frame = buffer.pop(0)
                not_full.set()

            frame = cv2.resize(
                frame,
                dsize=(resize_frame_width, resize_frame_height),
                interpolation=cv2.INTER_CUBIC
            )

            not_update.wait()
            not_update.clear()

            for y, row in enumerate(frame):
                for x, ele in enumerate(row):
                    self.stdscr.addch(
                        y + padding_y,
                        x + padding_x,
                        TO_ASCII[ele],
                    )
            self.stdscr.addstr(0, 0, '{}'.format(len(buffer)))
            self.stdscr.refresh()

        is_finish = True

class Clock(Thread):
    def __init__(self, spf, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spf = spf

    def run(self):
        global not_update
        global is_finish

        clock = Event()

        while not clock.wait(self.spf):
            if is_finish: break
            not_update.set()

class Fake_Screen():
    def __init__(self):
        self.width = 20
        self.height = 15
        self.text = [['' for _ in range(20)] for _ in range(15)]

    def erase(self):
        self.text = [['' for _ in range(20)] for _ in range(15)]

    def addch(self, x, y, c):
        self.text[x][y] = c

    def getmaxyx(self):
        return 15, 20

    def refresh(self):
        for i in range(15):
            print(self.text[i])

def main(stdscr):
    stdscr.clear()
    video = cv2.VideoCapture(args.name)
    if video.isOpened():
        frame_width = video.get(3)
        frame_height = video.get(4)
        fps = video.get(5)

        gcd = math.gcd(int(frame_height), int(frame_width))

        frame_height_rate = int(frame_height/gcd)
        frame_width_rate = int(frame_width/gcd)*2
    else:
        exit()

    buffer_thread = BufferFrame(video)
    load_thread = UpdateScreen(stdscr, frame_width_rate, frame_height_rate)
    refresh_thread = Clock(1/fps)
    buffer_thread.start()
    load_thread.start()
    refresh_thread.start()

    buffer_thread.join()
    load_thread.join()
    refresh_thread.join()

wrapper(main)
