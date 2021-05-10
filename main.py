import time

from Decoder import Decoder as Dec
from Encoder import Encoder as Enc


def main():
    # TODO : use argparse
    filepath_raw = '/home/hannes/uni/video_enc/ivc-ss21/A01/pgm/Berlin.pgm' or input('file to transcode: ')
    filepath_encoded = '/home/hannes/uni/video_enc/ivc-ss21/out/Berlin.ivc21' or input('encoded path: ')
    filepath_transcoded = '/home/hannes/uni/video_enc/ivc-ss21/A01/pgm/Berlin_transcoded.pgm' or input(
        'file to output: ')
    blocksize = 8

    enc = Enc(block_size=blocksize)
    dec = Dec()

    start_time = time.process_time()  # benchmarking speed
    enc(filepath_raw, filepath_encoded)  # encoding
    encoding_time = time.process_time() - start_time

    start_time = time.process_time()  # benchmarking speed
    dec(filepath_encoded, filepath_transcoded)  # decoding
    decoding_time = time.process_time() - start_time

    print(f'it took {encoding_time * 1000}ms to encode and {decoding_time * 1000}ms to decode')


if __name__ == '__main__':
    main()
