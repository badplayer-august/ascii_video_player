#include <opencv2/videoio.hpp>
#include <ncurses.h>
#include <iostream>
using namespace cv;

ascii_grayscale = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@']

int main() {
    char vid_name[] = "video.mp4";
    int x, y;
    initscr();
    getmaxyx(stdscr, y, x);
    printw("%d, %d\n", y, x);
    refresh();
    getch();
    endwin();
    return 0;
}
