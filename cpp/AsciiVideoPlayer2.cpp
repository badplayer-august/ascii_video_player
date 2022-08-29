#include <opencv2/opencv.hpp>
#include <opencv4/opencv2/core/mat.hpp>
#include <curses.h>
#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <string>
#include <vector>
#include <array>
#include <codecvt>
#include <locale>
#include <wchar.h>
#include <future>
#include <chrono>
#include <thread>

using namespace cv;
using namespace std;

string filename;
wstring char_list = 
  L"⠀⠁⠈⠉⠂⠃⠊⠋⠐⠑⠘⠙⠒⠓⠚⠛⠄⠅⠌⠍⠆⠇⠎⠏⠔⠕⠜⠝⠖⠗⠞⠟"
  "⠠⠡⠨⠩⠢⠣⠪⠫⠰⠱⠸⠹⠲⠳⠺⠻⠤⠥⠬⠭⠦⠧⠮⠯⠴⠵⠼⠽⠶⠷⠾⠿"
  "⡀⡁⡈⡉⡂⡃⡊⡋⡐⡑⡘⡙⡒⡓⡚⡛⡄⡅⡌⡍⡆⡇⡎⡏⡔⡕⡜⡝⡖⡗⡞⡟"
  "⡠⡡⡨⡩⡢⡣⡪⡫⡰⡱⡸⡹⡲⡳⡺⡻⡤⡥⡬⡭⡦⡧⡮⡯⡴⡵⡼⡽⡶⡷⡾⡿"
  "⢀⢁⢈⢉⢂⢃⢊⢋⢐⢑⢘⢙⢒⢓⢚⢛⢄⢅⢌⢍⢆⢇⢎⢏⢔⢕⢜⢝⢖⢗⢞⢟"
  "⢠⢡⢨⢩⢢⢣⢪⢫⢰⢱⢸⢹⢲⢳⢺⢻⢤⢥⢬⢭⢦⢧⢮⢯⢴⢵⢼⢽⢶⢷⢾⢿"
  "⣀⣁⣈⣉⣂⣃⣊⣋⣐⣑⣘⣙⣒⣓⣚⣛⣄⣅⣌⣍⣆⣇⣎⣏⣔⣕⣜⣝⣖⣗⣞⣟"
  "⣠⣡⣨⣩⣢⣣⣪⣫⣰⣱⣸⣹⣲⣳⣺⣻⣤⣥⣬⣭⣦⣧⣮⣯⣴⣵⣼⣽⣶⣷⣾⣿";
uchar round_color[256], ascii_index[256];

void prase_args(int argc, char** argv);
Mat preprocessing(Mat img, int win_rows, int win_cols);
vector<wstring> to_ascii(Mat img);
bool set_str(WINDOW *w, vector<wstring> ascii_img, int row_pad, int col_pad);

int main(int argc, char **argv) {
  setlocale(LC_ALL, "");
  
  int max_win_rows, max_win_cols, vid_width, vid_height, mspf, win_rows, win_cols, row_pad, col_pad;
  float ratio;
  Mat frame, img;
  vector<wstring> ascii_img(0);
  VideoCapture vid;
  WINDOW *w = initscr();

  prase_args(argc, argv);

  vid = VideoCapture(filename);
  mspf = 1e3/vid.get(CAP_PROP_FPS);
  vid_width = vid.get(CAP_PROP_FRAME_WIDTH);
  vid_height = vid.get(CAP_PROP_FRAME_HEIGHT)/2;
  ratio = (float) vid_width/vid_height;

  for (int f=0; f<vid.get(CAP_PROP_FRAME_COUNT); f++) {
    vid.read(frame);
    getmaxyx(w, max_win_rows, max_win_cols);

    if (ratio >= (float) max_win_cols/max_win_rows) {
      win_rows = (vid_height*max_win_cols)/vid_width;
      win_cols = max_win_cols;
      row_pad = (max_win_rows-win_rows)/2;
      col_pad = 0;
    } else {
      win_rows = max_win_rows;
      win_cols = (vid_width*max_win_rows)/vid_height;
      row_pad = 0;
      col_pad = (max_win_cols-win_cols)/2;
    }

    clear();
    future<Mat> fut1 = async(launch::async, preprocessing, frame, win_rows, win_cols);
    future<vector<wstring>> fut2 = async(launch::async, to_ascii, img);
    future<bool> fut3 = async(launch::async, set_str, w, ascii_img, row_pad, col_pad);
    this_thread::sleep_for(chrono::milliseconds(mspf));

    img = fut1.get();
    ascii_img = fut2.get();
    fut3.get();
    refresh();
  }
}

void prase_args(int argc, char **argv) {
  bool inverse = false;
  int opt;
  int color_cluster[2] = {0, 255};

  while ((opt = getopt(argc, argv, "i")) != -1) {
    switch (opt) {
      case 'i':
        inverse = true;
        break;
      default:
        fprintf(stderr, "Usage: %s [-i] FILE\n", argv[0]);
        exit(EXIT_FAILURE);
    }
  }

  for (int i=0; i<128; i++){
    round_color[i] = inverse? 255: 0;
    ascii_index[i] = 0;
  }

  for (int i=128; i<256; i++){
    round_color[i] = inverse? 0: 255;
    ascii_index[i] = 1;
  }

  if (optind >= argc) {
    fprintf(stderr, "Expected argument after options\n");
    exit(EXIT_FAILURE);
  }
  filename = string(argv[optind]);
}

Mat preprocessing(Mat img, int win_rows, int win_cols) {
  int rows = win_rows<<2, cols = win_cols<<1;
  Mat resized_img, gray_img;

  img.convertTo(resized_img, 0);
  resize(resized_img, resized_img, Size(cols, rows), INTER_CUBIC);
  cvtColor(resized_img, gray_img, COLOR_BGR2GRAY);

  return gray_img;
}

vector<wstring> to_ascii(Mat img) {
  int rows = img.rows, cols = img.cols, old_pixel, dither_pixel, err, set_y, set_x, offset_y, offset_x;
  uchar new_pixel, *ptr;
  vector<int> offset(cols>>1);
  vector<vector<int>> err_table(rows+1, vector<int>(cols+2, 0));
  vector<wstring> ascii_img(rows>>2, wstring(cols>>1, L' '));

  for (int y=0; y<rows; y++) {
    ptr = img.ptr<uchar>(y);

    for (int x=0; x<cols; x++) {
      dither_pixel = ptr[x] + err_table[y][x+1];
      old_pixel = min(max(dither_pixel, 0), 255);
      new_pixel = round_color[old_pixel];

      err = dither_pixel - new_pixel;
      err_table[y+0][x+1] += err>>1;
      err_table[y+1][x-1] += err>>3;
      err_table[y+1][x]   += err>>2;
      err_table[y+1][x+1] += err>>3;

      set_y = y>>2;
      set_x = x>>1;
      offset_y = y&3;
      offset_x = x&1;

      offset[set_x] += ascii_index[new_pixel]*pow(2, (offset_y<<1)+offset_x);
      if (offset_y == 3 && offset_x == 1) {
        ascii_img[set_y][set_x] = char_list[offset[set_x]];
        offset[set_x] = 0;
      }
    }
  }

  return ascii_img;
}

bool set_str(WINDOW *w, vector<wstring> ascii_img, int row_pad, int col_pad) {
  for (int r=0; r<ascii_img.size(); r++)
    mvwaddwstr(w, r+row_pad, col_pad, ascii_img[r].c_str());
  return true;
}

