#!/usr/bin/env python3

import argparse
import time

from Encoder import Encoder


def main():
    parser = argparse.ArgumentParser(description='PGM encoder')
    parser.add_argument('-bs', '--blocksize',
                        help='block size in samples (default: 16)',
                        default=16,
                        dest='blocksize',
                        type=int)
    parser.add_argument('-qp', '--quantization-parameter',
                        help='quantization parameter, range [0;31] (default: 12)',
                        default=12,
                        choices=(range(0, 32)),
                        dest='qp',
                        type=int)
    parser.add_argument('-i', '--input',
                        help='input image in pgm format',
                        required=True,
                        dest='input', )
    parser.add_argument('-b', '--bitstream',
                        help='bitstream file written by encoder',
                        required=True,
                        dest='bitstream')
    parser.add_argument('-r', '--reconstruct',
                        help='path for reconstructed image at the encoder side',
                        dest='reconstruction_path')
    parser.add_argument('-s', '--size',
                        help='Specify the video dimensions (WxH) when encoding a video file (default: 416x240)',
                        default='416x240',
                        dest='video_size',
                        type=str)
    parser.add_argument('-n', '--n-frames',
                        help='Specify the number of frames to be encoded',
                        default=100,
                        dest='n_frames',
                        type=int)
    args = parser.parse_args()

    start_time = time.process_time()  # benchmarking speed
    enc = Encoder(args.input, args.bitstream, args.blocksize, args.qp, args.reconstruction_path)
    if args.video_size is None:
        enc.encode_image()
    else:
        width, height = list(map(int, args.video_size.split('x')))  # Parse width and height and cast to int
        enc.encode_video(width, height, args.n_frames)
    encoding_time = time.process_time() - start_time
    print(f'it took {encoding_time * 1000} ms to encode')


if __name__ == '__main__':
    main()
