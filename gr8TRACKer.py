"""gr8TRACKer

Usage:
    gr8TRACKer.py plan --tracklen=<s> [options] <sourcedir>
    gr8TRACKer.py build <planfile> <target>

Options:
    -h --help       Shows this message
    --tracklen=<s>  Track length in minutes, full cartridge length is 4 times this.
    --padding=<s>   Minimum length of silence at start and end of tracks in seconds [default: 8]
    --fadelen=<s>   Length of fades in seconds, silence padding not included [default: 4]
    --pitch=<f>     Pitch correction factor, values below 1.0 slow down [default: 1.0]
"""

from docopt import docopt
from pydub import AudioSegment
from os import path
from glob import glob

def plan_from_dir(sourcedir, tracklen):
    all_mp3s = [AudioSegment.from_mp3(file) for file in glob(path.join(sourcedir, "*.mp3"))]
    for mp3 in all_mp3s:
        print(len(mp3))

if __name__ == '__main__':
    arguments = docopt(__doc__, version = 'gr8tracker 0.5')
    print(arguments)

    if arguments['plan']:
        # Default to 20 min tracks
        tracklen = arguments['--tracklen']
        plan_from_dir(arguments['<sourcedir>'], tracklen)

    if arguments['build']:
        build_from_plan(arguments.planfile)
