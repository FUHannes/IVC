import time
import argparse

from Decoder import Decoder as Dec



def main():
    parser = argparse.ArgumentParser(description='PGM decoder')
    requiredNamed = parser.add_argument_group('required arguments')
    requiredNamed.add_argument('-o', '--output', help='ireconstructed image in pgm format', required=True,dest="output")
    requiredNamed.add_argument('-b', '--bitstream', help='bitstream file to be read by decoder', required=True, dest="bitstream")
    args = parser.parse_args()

    dec = Dec()

    start_time = time.process_time()                        #benchmarking speed
    dec(args.bitstream,args.output)                         #decoding
    decoding_time = time.process_time() - start_time   



if __name__ == "__main__":
    main()