import argparse
import threading
import math
import time
import cv2
from curses import wrapper

ascii_grayscale = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@']
# ascii_grayscale = ['$', '@', 'B', '%', '8', '&', 'W', 'M', '#', '*', 'o', 'a', 'h', 'k', 'b', 'd', 'p', 'q', 'w', 'm', 'Z', 'O', '0', 'Q', 'L', 'C', 'J', 'U', 'Y', 'X', 'z', 'c', 'v', 'u', 'n', 'x', 'r', 'j', 'f', 't', '/', '\\', '|', '(', ')', '1', '{', '}', '[', ']', '?', '-', '_', '+', '~', '<', '>', 'i', '!', 'l', 'I', ';', ':', ',', '"', '^', '`', '\'', '.', ' ']

parser = argparse.ArgumentParser()
parser.add_argument('-n','--name', default='video.mp4')
# parser.add_argument('-i', '--info', default=0, type=bool)
args = parser.parse_args()

binning = 256/len(ascii_grayscale)
to_ascii = []

for i in range(256):
    to_ascii.append(ascii_grayscale[int(i//binning)])

vid = cv2.VideoCapture(args.name)
if vid.isOpened():
    frame_width = vid.get(3)
    frame_height = vid.get(4)
    fps = vid.get(5)

    gcd = math.gcd(int(frame_height), int(frame_width))

    frame_height_rate = int(frame_height/gcd)
    frame_width_rate = int(frame_width/gcd)*2
else:
    exit()

buffer_size = 1<<6
n_finish = True
n_refresh = False
buff = [[] for _ in range(buffer_size)]
r, w = 0, 0

def buffer():
    global w
    global buff

    for _ in range(int(vid.get(7))):
        while (w + 1 & 63) == r:
            time.sleep(0.001)

        has_frames, frame = vid.read()
        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY,
        )
        buff[w] = frame
        w = (w + 1 & 63)
 #      print('w={}'.format(w))

def load(stdscr):
    global r
    global n_refresh
    global n_finish

    for _ in range(int(vid.get(7))):
        while r == w or n_refresh:
            time.sleep(0.001)

        stdscr.erase()
        scr_height, scr_width = stdscr.getmaxyx()

        if scr_height*frame_width_rate < scr_width*frame_height_rate:
            resize_rate = scr_height//frame_height_rate
        else:
            resize_rate = scr_width//frame_width_rate

        resize_frame_height = int(resize_rate*frame_height_rate)
        resize_frame_width = int(resize_rate*frame_width_rate)
        padding_y = int(scr_height - resize_frame_height)>>1
        padding_x = int(scr_width - resize_frame_width)>>1

        buff_frame = cv2.resize(
            buff[r],
            dsize=(resize_frame_width, resize_frame_height),
            interpolation=cv2.INTER_CUBIC
        )

        for y, row in enumerate(buff_frame):
            for x, ele in enumerate(row):
                stdscr.addch(
                    y + padding_y,
                    x + padding_x,
                    to_ascii[ele],
                )
        stdscr.addstr(0, 0, '{}'.format((w+64-r)&63))
        stdscr.refresh()
        n_refresh = True
        r = (r + 1 & 63)
 #      print('r={}'.format(r))

    n_finish = False

def refresh(stdscr):
    global n_refresh
    global n_finish

    while n_finish:
        time.sleep(1/fps)
        n_refresh = False

def main(stdscr):
    buffer_thread = threading.Thread(target=buffer)
    load_thread = threading.Thread(target=load, args=(stdscr, ))
    refresh_thread = threading.Thread(target=refresh, args=(stdscr, ))

    buffer_thread.start()
    load_thread.start()
    refresh_thread.start()
    stdscr.close()

wrapper(main)
