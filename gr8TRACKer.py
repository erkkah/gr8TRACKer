"""gr8TRACKer

Usage:
    gr8TRACKer.py --tracklen=<s> [options] <sourcedir> <target>

Options:
    -h --help       Shows this message
    --tracklen=<s>  Track length in minutes, full cartridge length is 4 times this.
    --padding=<s>   Minimum length of silence at start and end of tracks in seconds [default: 4]
    --fadelen=<s>   Length of fades in seconds, silence padding not included [default: 4]
    --pitch=<f>     Pitch correction factor, values below 1.0 slow down [default: 1.0]
    --pack          Reorder songs to avoid cuts on track changes
"""

from docopt import docopt
from pydub import AudioSegment
from os import path
from glob import iglob
import array

def s_to_minsec(s):
    rounded = round(s)
    min = int(rounded // 60)
    sec = int(rounded % 60)
    return "{}:{:02}".format(min, sec)

def binpack(bin_size, items, sizefun = len):
    """
    returns a number of bins, packed with the specified items
    using the "fit first decreasing" method
    """
    bins = [[]]
    bin_capacities = [bin_size]

    # Go through items in falling size order
    for item in sorted(items, reverse = True, key = sizefun):
        size = sizefun(item)
        assert(size <= bin_size)
        packed = False
        for i in range(0, len(bins)):
            if bin_capacities[i] >= size:
                bins[i].append(item)
                bin_capacities[i] -= size
                packed = True
                break
        if not packed:
            bins.append([item])
            bin_capacities.append(bin_size - size)

    return bins

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
            split_point = track_time_left * 1000

            if track_time_left < 20:
                # Don't add a new song just to be cut short (20s?), go directly to next track
                print(" [complete (padded with {:.2}s)]".format(track_time_left))

                first_half = AudioSegment.silent(split_point)
                second_half = segment
            else:
                print(" [cut @ {}]".format(s_to_minsec(track_time_left)))

                first_half = segment[:split_point].fade_out(fadelen_ms)
                second_half = segment[split_point:].fade_in(fadelen_ms)

            master += first_half
            master += AudioSegment.silent(duration = padding_ms)

            track_count += 1
            if(track_count >= 5):
                track_count -= 1
                break

            track_time_left = track_time_seconds
            master += AudioSegment.silent(duration = padding_ms)

            if second_half.duration_seconds > 10:
                # Don't fade in just to get to the end (10s) of a song
                master += second_half
                track_time_left -= second_half.duration_seconds
            else:
                print("Skip short end at track start ({:.2s})".format(second_half.duration_seconds))

    total = master.duration_seconds
    print("Built {} tracks, total length {}".format(track_count, s_to_minsec(total)))
    return master

def segment_to_float_array(segment):
    """
    Convert from AudioSegment (interleaved packed arrays of integer samples)
    to 2D array of floats.
    First dimension is channel index, second is float sample values
    in the range of (-1.0, 1.0).
    """
    channels = segment.channels
    bits_per_sample = segment.sample_width * 8
    # Assume signed values, centered around zero
    max_sample_value = (1 << (bits_per_sample - 1)) - 1

    samples = segment.get_array_of_samples();
    frames = int(segment.frame_count())
    assert(len(samples) == frames * channels)

    result = [ [] for c in range(0, channels) ]

    # De-interleave and scale
    for i in range(0, frames):
        for c in range(0, channels):
            sample = samples[i * channels + c]
            sample_value = sample / max_sample_value
            result[c].append(sample_value)

    return result

def segment_to_nparray(segment):
    """
    Convert from AudioSegment (interleaved packed arrays of integer samples)
    to a 2D nparray of floats.
    First dimension is channel index, second is float sample values
    in the range of (-1.0, 1.0).
    """

    import numpy as np

    channels = segment.channels
    bits_per_sample = segment.sample_width * 8
    # Assume signed values, centered around zero
    max_sample_value = (1 << (bits_per_sample - 1)) - 1

    samples = segment.get_array_of_samples();
    frames = int(segment.frame_count())
    assert(len(samples) == frames * channels)

    def deinterleave(samples):
        for c in range(0, channels):
            for i in range(0, frames):
                sample = samples[i * channels + c]
                sample_value = sample / max_sample_value
                yield sample_value

    return np.fromiter(deinterleave(samples), np.float, frames * channels).reshape((channels, -1))


def float_array_to_segment(samples, sample_rate):
    """
    Convert from 2D float array to 32 bit AudioSegment.
    """
    channels = len(samples)
    assert(channels > 0)
    frames = len(samples[0])

    bits_per_sample = 16
    # Assume signed values, centered around zero
    max_sample_value = (1 << (bits_per_sample - 1)) - 1

    def interleave(samples):
        for i in range(0, frames):
            for c in range(0, channels):
                yield samples[c][i]

    sample_data = (int(val * max_sample_value) for val in interleave(samples))
    # Signed 16 bit int array
    packed_data = array.array("h", sample_data)

    # Use of undocumented constructor!
    return AudioSegment(data = packed_data.tostring(), metadata={
        "channels": channels,
        "sample_width": 2,
        "frame_rate": sample_rate,
        "frame_width": 2 * channels
    })

def repitch(segment, factor):
    import resampy

    print("\tDeinterleaving...")
    samples = segment_to_nparray(segment)

    target_rate = segment.frame_rate / factor
    print("\tResampling...")
    resampled = resampy.resample(samples, segment.frame_rate, target_rate)

    print("\tInterleaving...")
    return float_array_to_segment(resampled, segment.frame_rate)

def file_segments(sourcedir):
    pattern = path.join(sourcedir, "**")
    matching = sorted(iglob(pattern, recursive = True))
    for file in matching:
        types = ["mp4", "aac", "mp3", "wav", "ogg"]
        for type in types:
            if file.endswith(type):
                yield([file, AudioSegment.from_file(file, type)])
                break

def build_from_dir(sourcedir, target, tracklen, padding, fadelen, pack = False, pitch = 1.0):
    segments = file_segments(sourcedir)

    if pack:
        print("Packing...")
        track_time_seconds = tracklen * 60 - padding * 2
        packed = binpack(track_time_seconds, segments, lambda x: x[1].duration_seconds)

        # Here we could pre-fill bins by inserting silence between songs or at the
        # end. This would completely eliminate cut tracks.

        def joined_bins(bins):
            for bin in bins:
                for item in bin:
                    yield item

        segments = joined_bins(packed)

    print("Mastering...")
    master = pack_tracks(
        segments = segments,
        tracklen = tracklen,
        padding = padding,
        fadelen = fadelen)

    segments = None

    if pitch != 1.0:
        print("Pitching...")
        master = repitch(master, pitch)

    print("Writing track...")
    master.export(target, format = "wav")

    print("Done!")


def run_tests():
    samples = [[0, 1, 0, -1, 0], [-1, 0, 1, 0, 1]]
    segment = float_array_to_segment(samples, 11025)
    reconstructed = segment_to_float_array(segment)
    assert(samples == reconstructed)

def main():
    run_tests()

    arguments = docopt(__doc__, version = 'gr8tracker 0.5')
    #print(arguments)

    tracklen = arguments['--tracklen']
    build_from_dir(
        sourcedir = arguments['<sourcedir>'],
        target = arguments['<target>'],
        tracklen = int(arguments['--tracklen']),
        padding = int(arguments['--padding']),
        fadelen = int(arguments['--fadelen']),
        pitch = float(arguments['--pitch']),
        pack = arguments['--pack'])

if __name__ == '__main__':
    main()
