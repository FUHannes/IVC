import time
import argparse

from Decoder import Decoder


def main():
    parser = argparse.ArgumentParser(description='PGM decoder')
    required_named = parser.add_argument_group('required arguments')
    required_named.add_argument('-b', '--bitstream', help='bitstream file to be read by decoder',
                                required=True, dest="bitstream")
    required_named.add_argument('-o', '--output', help='reconstructed image in pgm format',
                                required=True, dest="output")
    args = parser.parse_args()

    dec = Decoder(args.bitstream, args.output)

    start_time = time.process_time()  # benchmarking speed
    dec.decode_block()
    decoding_time = time.process_time() - start_time   


if __name__ == "__main__":
    main()
