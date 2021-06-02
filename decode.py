#!/usr/bin/env python3

import argparse
import time

from Decoder import Decoder


def main():
    parser = argparse.ArgumentParser(description='image/video decoder')
    parser.add_argument('-b', '--bitstream',
                        help='bitstream file to be read by decoder',
                        required=True,
                        dest='bitstream')
    parser.add_argument('-o', '--output',
                        help='reconstructed image or video',
                        required=True,
                        dest='output')
    parser.add_argument('-pgm',
                        help='if set write output as PGM image',
                        action='store_true',
                        dest='pgm')
    args = parser.parse_args()

    start_time = time.process_time()  # benchmarking speed
    dec = Decoder(args.bitstream, args.output, args.pgm)
    dec.decode_image()
    decoding_time = time.process_time() - start_time
    print(f'it took {decoding_time * 1000} ms to decode')


if __name__ == '__main__':
    main()