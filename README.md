# Boss Looper

A simple Python script that will load a user's music file and their input, creating a system where they can transition between certain segments of the song.

Made simple thanks to [Pydub](https://github.com/jiaaro/pydub) and [PyGame](https://www.pygame.org/wiki/GettingStarted)

Right now this currently works for certain on Windows.

### Installing

This requires a few modules that can be installed with pip.

    pip install pygame
    pip install pydub
    pip install keyboard

Since this program is intended for use with .ogg files, make sure you install [ffmpeg](https://www.ffmpeg.org/download.html) and add it to your PATH.

Once that's done, you can load a song (.ogg) and its complement loop portions (.csv)
and the program will cut the song into the portions specified. An example .csv would look like:

    0:00.000, 0:16.000, 0, Intro
    0:16.000, 1:57.200, 1, Battle 1
    2:07.000, 3:01.320, 0, Transition 1
    3:01.320, 4:26.920, 1, Battle 2
    4:28.000, 4:59.600, 0, Transition 2
    4:59.600, 5:57.950, 1, Battle 3
    5:26.000, 6:07.056, 0, Finale

## Module Documentation

* [PyGame mixer](https://www.pygame.org/docs/ref/mixer.html)
* [Pydub](https://github.com/jiaaro/pydub/blob/master/API.markdown)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
