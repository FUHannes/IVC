import argparse
import time

from Encoder import Encoder as Enc


def main():
    parser = argparse.ArgumentParser(description='PGM encoder')
    parser.add_argument('-bs', '--blocksize',
                        help='block size in samples (default: 8)',
                        default=8,
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
    args = parser.parse_args()

    enc = Enc(block_size=args.blocksize, qp=args.qp)

    start_time = time.process_time()                # benchmarking speed
    enc.encode_image(args.input, args.bitstream)    # encoding
    encoding_time = time.process_time() - start_time

    print(f'it took {encoding_time * 1000} ms to encode')


if __name__ == '__main__':
    main()
