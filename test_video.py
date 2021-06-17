import math
import subprocess
import pandas as pd
import os
import matplotlib.pyplot as plt
import argparse


from Encoder import Encoder as Encoder
from Decoder import Decoder as Decoder

# todo: adapt source of tool to your file structure
VIDEO_PSNR_TOOL_PATH = 'tools/psnr-raw-video/bin/GNU-9.3.0/psnrRaw'

DATA_ROOT_PATH = 'dat'

VIDEOS_ROOT_PATH = 'videos'
VIDEO_ORIGINAL_PATH = os.path.join(VIDEOS_ROOT_PATH, 'original')
BITSTREAM_PATH = os.path.join(VIDEOS_ROOT_PATH, 'bitstream')
VIDEO_RECONSTRUCTION_PATH = os.path.join(VIDEOS_ROOT_PATH, 'reconstruction')

VIDEO_SUFFIX = '.y'
BITSTREAM_SUFFIX = '.txt'
DATA_SUFFIX = '.dat'

VIDEO_WIDTH = 416
VIDEO_HEIGHT = 240
VIDEO_FRAME_RATE = 50
DEFAULT_BLOCK_SIZE = 16
DEFAULT_NO_OF_FRAMES = 30
DEFAULT_SEARCH_RANGE = 8

def generate_data(filename, version, block_size, num_frames, search_range):
    input_path = os.path.join(VIDEO_ORIGINAL_PATH, filename + VIDEO_SUFFIX)

    if not os.path.exists(BITSTREAM_PATH):
        os.mkdir(BITSTREAM_PATH)
    bitstream_path = os.path.join(BITSTREAM_PATH, filename
                                  + "_bs" + str(block_size)
                                  + "_fr" + str(num_frames)
                                  + "_sr" + str(search_range)
                                  + BITSTREAM_SUFFIX)

    if not os.path.exists(VIDEO_RECONSTRUCTION_PATH):
        os.mkdir(VIDEO_RECONSTRUCTION_PATH)
    output_path = os.path.join(VIDEO_RECONSTRUCTION_PATH, filename
                               + "_bs" + str(block_size)
                               + "_fr" + str(num_frames)
                               + "_sr" + str(search_range)
                               + VIDEO_SUFFIX)

    df = pd.DataFrame(columns=['bpp', 'db'])

    for index, quality in enumerate([8,12,16,20,24]):
        enc = Encoder(input_path, bitstream_path, block_size, quality)
        enc.encode_video(VIDEO_WIDTH, VIDEO_HEIGHT, num_frames, search_range)
        dec = Decoder(bitstream_path, output_path, pgm=False)
        dec.decode_all_frames()
        # ./psnrRaw (width) (height) (format) (orgVideo) (recVideo) (bitstream) (fps)
        process = subprocess.run(
            [VIDEO_PSNR_TOOL_PATH, str(VIDEO_WIDTH),str(VIDEO_HEIGHT), "400", input_path, output_path, bitstream_path, str(VIDEO_FRAME_RATE)],
            stdout=subprocess.PIPE,
        )

        stdout = process.stdout.decode("utf-8")
        out = (stdout.split('\n\n')[2]).split()
        bpp, db = float(out[0]), float(out[1])
        db = 0.0 if math.isinf(db) else db
        print("tested", bpp, db)
        df.loc[index] = [bpp, db]

    version_path = os.path.join(DATA_ROOT_PATH, version)
    if not os.path.exists(version_path):
        os.mkdir(version_path)
    df.to_pickle(os.path.join(version_path, filename + DATA_SUFFIX))


def plot_data(filename, version, versions):
    versions = versions.split(',') + [version] if versions else [version]

    plt.figure(figsize=(20, 12))
    for version in versions:
        ver = pd.DataFrame(pd.read_pickle(os.path.join(
            DATA_ROOT_PATH, version, filename + DATA_SUFFIX)))
        plt.plot(ver['bpp'], ver['db'], label=version)

    plt.xlabel('X: Bits (bpp)')
    plt.ylabel('Y: PSNR (db)')
    plt.legend()
    plt.title(filename)
    plt.savefig("PSNR_" + filename + ".pdf")
    plt.show()

def parse_args():
    parser = argparse.ArgumentParser(
        description='Tests encoder quality of a video')
    parser.add_argument('-f', '--file', dest='filename', type=str,
                        help='filename of input video without full path and suffix, e.g. BasketballPass', required=True)
    parser.add_argument('-v', '--version', dest='version', type=str, help='version of new encoder and decoder, e.g. \'1.0\'',
                        required=True)
    parser.add_argument('-vs', '--versions', dest='versions', type=str,
                        help='optional: comma separated versions that should be also compared to the new encoder and decoder version, e.g. \'1.0,2.0\'',
                        required=False)
    parser.add_argument('-print', dest='print', action='store_true',
                        help='optional: if set, no new data is computed but version curves are plotted')
    parser.add_argument('-bs', '--block_size',
                        help='block size in samples (default: 16)',
                        default=DEFAULT_BLOCK_SIZE,
                        dest='block_size',
                        type=int)
    parser.add_argument('-fr', '--frames',
                        help='number of frames',
                        default=DEFAULT_NO_OF_FRAMES,
                        dest='num_frames',
                        type=int)
    parser.add_argument('-sr', '--search_range',
                        help='search range in samples (default: 8)',
                        default=DEFAULT_SEARCH_RANGE,
                        dest='search_range',
                        type=int)

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    if not args.print:
        generate_data(args.filename, args.version, args.block_size, args.num_frames, args.search_range)
    plot_data(args.filename, args.version, args.versions)


