# Ascii video player

## Demo
[![demo video](https://img.youtube.com/vi/g5M4U-x5d1A/0.jpg)](https://www.youtube.com/watch?v=g5M4U-x5d1A)

## Usage
### C++ (Fast and have braille code)
In `cpp` directory run

```sh
make
./AsciiVideoPlayer FILE
```

### Python (Slow and don't have braille code)
In `python` directory run with argument `-n | --name`

```sh
python ascii_video.py -n video2.mp4
```

## Known Bugs

`ascii_video.py`

-   The terminal crash after the program finish, terminate.
-   Still drop frames sometime.

## WIP
`cpp` version with more options.
