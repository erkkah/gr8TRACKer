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
from glob import glob

# http://www.geeksforgeeks.org/bin-packing-problem-minimize-number-of-used-bins/
# http://moose.cs.ucla.edu/publications/schreiber_korf_ijcai13.pdf

def pack_tracks(files, tracklen, padding, fadelen):
    # Tracks start and end with padded silence
    track_time_seconds = tracklen * 60 - (padding * 2)
    padding_ms = padding * 1000
    fadelen_ms = fadelen * 1000
    current = None
    master = AudioSegment.silent(duration = padding_ms)
    track_time_left = track_time_seconds
    track_count = 1

    for file in files:
        if track_time_left > file.duration_seconds:
            master += file
            track_time_left -= file.duration_seconds
        else:
            split_point = track_time_left * 1000
            first_half = file[:split_point]
            second_half = file[split_point:]
            master += first_half.fade_out(fadelen_ms)
            master += AudioSegment.silent(duration = padding_ms)
            track_count += 1
            if(track_count >= 5):
                track_count -= 1
                break
            master += AudioSegment.silent(duration = padding_ms)
            master += second_half.fade_in(fadelen_ms)
            track_time_left = track_time_seconds - second_half.duration_seconds

    print("Build {} tracks, total length {}s".format(track_count, master.duration_seconds))
    return master

def build_from_dir(sourcedir, target, tracklen, padding, fadelen, pitch):
    types = ["mp4", "aac", "mp3", "wav", "ogg"]
    all_files = []
    for type in types:
        ext = "*." + type
        pattern = path.join(sourcedir, ext)
        all_files += [AudioSegment.from_file(file, type) for file in glob(pattern)]

    total_len = 0
    for file in all_files:
        total_len += file.duration_seconds

    total_len_minutes = total_len / 60
    print("Loaded {} files\n".format(len(all_files)))
    print("Len: {}".format(total_len_minutes))

    master = pack_tracks(
        files = all_files,
        tracklen = tracklen,
        padding = padding,
        fadelen = fadelen)

    # Do pitching here!

    master.export(target, format = "wav")

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
