# video2anki
a tool to generate anki decks from subtitles of videos, complete with audio embedding and cjk info.


# setup
before anything, install ffmpeg, python and pip

you might also want to install anki, to review the generated decks

setup the venv, pick a path of your convenience. for example:
```
python -m .venv
```
for more information on python venvs, look at https://docs.python.org/3/library/venv.html

install dependencies. this tool currently uses genanki to generate the anki deck, and pysrt to parse srt subtitle files (the only external subtitle format supported by this tool so far)
```
.venv/bin/pip install genanki pysrt
```

now you need
- a video file, with subtitles in both source and target languge as srt files
- some patience. genanki is REALLY slow (I mean it's python after all...). if you donate me enough xmr (42vkdWEgEcDP66jbn7KvsqbvaLGixmhs1VydJxJJqD35ZXYfnPjqzsTQ6SVRsmJfqNTtWEqF8KUSHF1frac9ecNvLa8EG2Y) i might consider a rewrite of genanki and probaly this script in a decent language to speed up things.

now run like this:
```
.venv/bin/python video2anki.py --media-file movie.mp4 --track-a movie_jp.srt --track-b movie_en.srt --title Movie --cjk-mode j
```

note that cjk-mode flag? it tells video2anki to generate anki cards with weblinks to popular online dictionaries to lookup hanzi, kanji and hanja characters.

# caution
this tool extracts audio from the movie for embedding into anki cards, and it generally tries to match audio and subtitles generously.
however, there's known issues with subtitles which contain audio descriptions. so, while it's mostly straightforward you *might* need to edit the anki deck.
tl;dr i can't fix broken or ill-suited subtitles.
