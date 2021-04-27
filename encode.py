import time
import argparse 

from Encoder import Encoder as Enc


def main():
    parser = argparse.ArgumentParser(description='PGM encoder')
    parser.add_argument('-bs', '--blocksize', help='block size in samples (default: 16)', default=16, dest="blocksize")
    requiredNamed = parser.add_argument_group('required arguments')
    requiredNamed.add_argument('-i', '--input', help='input image in pgm format', required=True,dest="input")
    requiredNamed.add_argument('-b', '--bitstream', help='bitstream file written by encoder', required=True, dest="bitstream")
    args = parser.parse_args()

    enc = Enc(block_size=args.blocksize)

    start_time = time.process_time()                        #benchmarking speed
    enc(args.input,args.bitstream)                          #encoding
    encoding_time = time.process_time() - start_time  

    print(f"it took {encoding_time*1000}ms to encode")




if __name__ == "__main__":
    main()