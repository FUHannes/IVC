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
    args = parser.parse_args()

    start_time = time.process_time()  # benchmarking speed
    enc = Encoder(args.input, args.bitstream, args.blocksize, args.qp, args.reconstruction_path)
    enc.encode_image()  # encoding
    encoding_time = time.process_time() - start_time
    print(f'it took {encoding_time * 1000} ms to encode')


if __name__ == '__main__':
    main()
