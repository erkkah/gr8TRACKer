"""gr8TRACKer

Usage:
    gr8TRACKer.py --tracklen=<s> [options] <sourcedir> <target>

Options:
    -h --help       Shows this message
    --tracklen=<s>  Track length in minutes, full cartridge length is 4 times this.
    --padding=<s>   Minimum length of silence at start and end of tracks in seconds [default: 4]
    --fadelen=<s>   Length of fades in seconds, silence padding not included [default: 4]
    --pitch=<f>     Pitch correction factor, values below 1.0 slow down [default: 1.0]
"""

from docopt import docopt
from pydub import AudioSegment
from os import path
from glob import iglob
from itertools import chain

# http://www.geeksforgeeks.org/bin-packing-problem-minimize-number-of-used-bins/
# http://moose.cs.ucla.edu/publications/schreiber_korf_ijcai13.pdf

def s_to_minsec(s):
    rounded = round(s)
    min = int(rounded // 60)
    sec = int(rounded % 60)
    return "{}:{}".format(min, sec)

def pack_tracks(segments, tracklen, padding, fadelen):
    # Tracks start and end with padded silence
    track_time_seconds = tracklen * 60 - (padding * 2)
    padding_ms = padding * 1000
    fadelen_ms = fadelen * 1000
    current = None
    master = AudioSegment.silent(duration = padding_ms)
    track_time_left = track_time_seconds
    track_count = 1

    for file, segment in segments:
        print("Adding {}".format(file), end = "")
        if track_time_left > segment.duration_seconds:
            master += segment
            track_time_left -= segment.duration_seconds
            print(" [complete]")
        else:
            print(" [cut @ {}]".format(s_to_minsec(track_time_left)))
            split_point = track_time_left * 1000
            first_half = segment[:split_point]
            second_half = segment[split_point:]
            master += first_half.fade_out(fadelen_ms)
            master += AudioSegment.silent(duration = padding_ms)
            track_count += 1
            if(track_count >= 5):
                track_count -= 1
                break
            master += AudioSegment.silent(duration = padding_ms)
            master += second_half.fade_in(fadelen_ms)
            track_time_left = track_time_seconds - second_half.duration_seconds

    total = master.duration_seconds
    print("Built {} tracks, total length {}".format(track_count, s_to_minsec(total)))
    return master

def file_segments(sourcedir):
    pattern = path.join(sourcedir, "*")
    matching = sorted(iglob(pattern))
    for file in matching:
        types = ["mp4", "aac", "mp3", "wav", "ogg"]
        for type in types:
            if file.endswith(type):
                yield([file, AudioSegment.from_file(file, type)])
                break

def build_from_dir(sourcedir, target, tracklen, padding, fadelen, pitch):
    segments = file_segments(sourcedir)

    print("Packing...")
    master = pack_tracks(
        segments = segments,
        tracklen = tracklen,
        padding = padding,
        fadelen = fadelen)

    # Do pitching here!

    print("Writing track...")
    master.export(target, format = "wav")

    print("Done!")

def main():
    arguments = docopt(__doc__, version = 'gr8tracker 0.5')
    #print(arguments)

    tracklen = arguments['--tracklen']
    build_from_dir(
        sourcedir = arguments['<sourcedir>'],
        target = arguments['<target>'],
        tracklen = int(arguments['--tracklen']),
        padding = int(arguments['--padding']),
        fadelen = int(arguments['--fadelen']),
        pitch = float(arguments['--pitch']))

if __name__ == '__main__':
    main()
