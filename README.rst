gr8TRACKer
========
**Fill your 8-tracks from a bunch of music files!**

You know the problem. You have a bunch of mp3s that you want to record to an
8-track cartridge, but you would like to avoid that awful CLICK noise in the middle
of songs by filling each track perfectly.

Or - if fitting songs to tracks is really hard, at least fade out and in
on track changes.

If you recognize any of this, *this is the tool for you*!

If you have no idea what I'm talking about, you might want to go
`here <https://en.wikipedia.org/wiki/8-track_tape>`_.

What it does
------------
gr8TRACKer loads audio files from a given location and outputs an audio file, the **master**,
that is prepared to fill the 4 stereo tracks of an 8-track cartridge of a given size.

gr8TRACKer will try to create a master wihout having to cut songs at track changes,
but since this is a *hard problem* |TM|, many masters will fade out the current song
before track changes and fade in again after the track change.

Also, since tapes are not exactly of the specified length, some padding will be used at
track starts/ends so that a full tape can be recorded in one go.

Most of the time, this is enough, sometimes you need to tweak stuff.

The audio files are typically mp3 files, but can be of any format that libav_ or ffmpeg_
supports, depending on your installation of pydub_. WAV files should always work.

Installation and operation
---------
gr8TRACKer requires python 3 and depends on pip to install required libraries.
Run pip and follow pydub_ instructions to get libav_ or ffmpeg_ installed.

::

	pip install -r requirements.txt

With all requirements resolved, running gr8TRACKer is easy:

::

	python gr8TRACKer.py --tracklen 20 /mediafiles/Steely_Dan/Pretzel_Logic master.wav

This will try to create a `master.wav` file that is 80 (four tracks times 20) minutes long.
This example will not make a full tape, since the given album is only 33:14, but you get the idea.

Run ``python gr8TRACKer.py -h`` to list options and get basic help.

Songs might get reordered, you migh need to tweak padding depending on tape lengths, et.c.

Have fun and keep on 8-tracking!


.. |TM| unicode:: U+2122
	:trim:

.. _libav: https://libav.org/
.. _ffmpeg: http://www.ffmpeg.org/general.html#File-Formats
.. _pydub: https://github.com/jiaaro/pydub
