from Encoder import Encoder as Enc
from Decoder import Decoder as Dec

import time

def main():
    filepath_raw = "/home/hannes/uni/video_enc/ivc-ss21/A01/pgm/Berlin.pgm" or input("file to transcode: ")
    filepath_encoded = "/home/hannes/uni/video_enc/ivc-ss21/out/Berlin.ivc21" or input("encoded path: ")
    filepath_transcoded = "/home/hannes/uni/video_enc/ivc-ss21/A01/pgm/Berlin_transcoded.pgm" or input("file to output: ")

    enc = Enc()
    dec = Dec()

    start_time = time.process_time()                #benchmarking speed
    encoded_stream = enc(filepath_raw)              #encoding
    encoding_time = time.process_time() - start_time    

    #writeout file
    enc_file = open(filepath_encoded,"wb")
    enc_file.write(encoded_stream)
    enc_file.close()

    start_time = time.process_time()                #benchmarking speed
    dec(encoded_stream,path=filepath_transcoded)    #decoding
    decoding_time = time.process_time() - start_time   

    print(f"it took {encoding_time*1000}ms to encode and {decoding_time*1000}ms to decode")


if __name__ == "__main__":
    main()