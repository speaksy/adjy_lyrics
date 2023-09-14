# this is a twitter bot that tweets adjy lyrics

[look](https://twitter.com/idyll_text)

## here are the dependencies

1. whatever is listed in `requirements.txt`
2. [pdf2img requires poppler](https://pdf2image.readthedocs.io/en/latest/installation.html)
3. if you want to run it yourself you'll also need a twitter api key, etc. i'm not documenting that shit here
4. things probably only run right on linux

## here is how it works

### script explication

in order that you'll need to run them when starting

- `convert_pdfs.py`: takes a directory containing pdfs and rasterizes them to `.tif`s (aka take the lyrics from [the official lyrics](https://www.theidyllopus.com/text) and make them into images)
- `main.py`: entry point for the whole thing -- chooses a lyrics, searches images for the lyric, makes a tweet
    - `convolution.py`: selects which lyrics to look for, treats [tesseract](https://github.com/tesseract-ocr/tesseract) like a convolution kernel and runs it over lyric images to find where the lyrics reside
        - `string_align.py`: used for matching tesseract output with ground truth lyrics -- this is hand-rolled and i'm proud of it
        - `strutils.py`: convenience functions for finding aesthetically pleasing and tweet-sized lyrics
    - `tweet.py`: nice wrapper module for making tweets :)

### the ALGORITHM

okay obviously no one cares about how to make a tweet so i'll skip that part.

#### lyric selection

i don't actually select lyrics, i select a page first. it is assumed that each page (image) of the text has an associated `.txt` file which is just the text on the page. so i choose a page, then select a random lyric from the text on that page.

a heuristic is used to try to get lyrics i think are nice :) which operates in two modes:
1. single line: choose a single lyric line defined as a series of words with either punctuation or newlines bounding it
2. paragraph: select words bounded by newlines

#### finding an image

here is where tesseract comes into play. i gotta find the chosen lyrics in a big ass image, and general OCR on these images sucks ass (typeface is weird, model isn't retrained on this data, i may have just chosen shitty settings) and returns a garbled mess of characters.

my solution is to throw electricity and time at the CPU until it gives me something good: i choose a window size, then treat tesseract as a [convolution "kernel"](https://en.wikipedia.org/wiki/Kernel_(image_processing)) and run it while sliding that window all around the image.

this gives a whole bunch of garbled messes of characters, so i need to decide which garbled mess is the best garbled mess that most likely matches the lyric i'm searching for. to do this, i use a sequence alignment algorithm to see which mess requires the fewest changes to transform back into the lyric i want (this is similar to/maybe the same as [string edit distance](https://en.wikipedia.org/wiki/Edit_distance), if you've heard of that before). this part is naively parallelized to make it faster (hopefully, i just trust that numba is doing its job).

anyways, now i've taken our list of garbled messes and assigned a score to each one of them -- using the window size/location, i can say "oh this window at position (x, y) has a score of z" and so i just take the maximum of these scores to find the window which most likely holds the lyric i want.

#### finishing up

now, i just write the best window found in the last step and the lyric i chose initially to the disk and upload the whole thing as a tweet.

#### improvements?

- the last part could def be made way better, since i choose the first window encountered if multiple windows have the same score (this leads to most lyrics being to the right-hand side of the final image). should really replace this with something smarter.
- i use really small windows which leads to non-aesthetic framing of the text. should consider zooming out once i found the best window
- my lyric selection code is kinda finnicky: it posts a lot of "! and ..." and stuff.

