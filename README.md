# Go game progress animation

This Python script generates an animated GIF from Go game file (kifu).
The resulting gif file could be embedded into a web page or posted to social network.

![Example](out.gif "Example")

## Installation

Python 3.9+ is required. To install required packages, run:

    python -m pip install -r requirements.txt

## Usage

Run:

    python sgf2gif.py [OPTIONS] SGF_FILE GIF_FILE

where:

    SGF_FILE    Path to a kifu file (.sgf)
    GIF_FILE    Output file (either .gif or any other image file extension)

Options:

    -s, --size INTEGER RANGE  Starting and ending positions range limit [default: 512; 128<=x<=2048]
    -r, --range INTEGER...    Starting and ending positions range
    -d, --duration FLOAT      Pause between the moves, seconds  [default: 3]
    -n, --numbers             Show move numbers
    --final                   Make a picture with final game position instead of GIF file

For example:

Generate a GIF file with numbered moves and 3 sec delay between each:

    python .\sgf2gif.py .\20221219_Shin-Jinseo_Ke-Jie.sgf out.gif -d 3 -n

Generate a static PNG file for final game position with numbered moves:

    python .\sgf2gif.py .\20221219_Shin-Jinseo_Ke-Jie.sgf out.gif -n
