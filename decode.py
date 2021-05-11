import argparse
import time

from Decoder import Decoder

def main():
    parser = argparse.ArgumentParser(description='PGM decoder')
    parser.add_argument('-b', '--bitstream',
                        help='bitstream file to be read by decoder',
                        required=True,
                        dest='bitstream')
    parser.add_argument('-o', '--output',
                        help='reconstructed image in pgm format',
                        required=True,
                        dest='output')
    args = parser.parse_args()

    dec = Decoder(args.bitstream, args.output)

    start_time = time.process_time()  # benchmarking speed
    dec.decode_image()
    decoding_time = time.process_time() - start_time
    print(f'it took {decoding_time * 1000}ms to decode')


if __name__ == '__main__':
    main()
