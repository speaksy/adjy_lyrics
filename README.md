# this is a twitter bot that tweets adjy lyrics

[look](https://twitter.com/idyll_text)

## here are the dependencies

1. whatever is listed in `requirements.txt`
2. [pdf2img requires poppler](https://pdf2image.readthedocs.io/en/latest/installation.html)
3. if you want to run it yourself you'll also need a twitter api key, etc. i'm not documenting that shit here

do not ask me why the poppler binary i use is for windows when everything else
assumes it runs on linux -- the answer is that i'm stupid and lazy

## here is how it works

### script explication

in order that you'll need to run them when starting

- `convert_pdfs.py`: takes a directory containing pdfs and rasterizes them to `.tif`s (aka take the lyrics from [the official lyrics](https://www.theidyllopus.com/text) and make them into images)
- `main.py`: entry point for the whole thing -- chooses a lyrics, searches images for the lyric, makes a tweet
    - `convolution.py`: selects which lyrics to look for, treats [tesseract](https://github.com/tesseract-ocr/tesseract) like a convolution kernel and runs it over lyric images to find where the lyrics reside
        - `string_align.py`: used for matching tesseract output with ground truth lyrics -- this is hand-rolled and i'm proud of it
    - `tweet.py`: nice wrapper module for making tweets :)

### the ALGORITHM

sike there's nothing here (i'll write a little bit eventually)

