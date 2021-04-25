from Encoder import Encoder as Enc
from Decoder import Decoder as Dec

def main():
    filepath_raw = "/home/hannes/uni/video_enc/ivc-ss21/A01/pgm/Berlin.pgm" or input("file to transcode: ")
    filepath_transcoded = "/home/hannes/uni/video_enc/ivc-ss21/A01/pgm/Berlin_transcoded.pgm" or input("file to output: ")

    enc = Enc()
    dec = Dec()

    encoded_stream = enc(filepath_raw)
    print(f"encoded stream : {type(encoded_stream)}")

    dec(encoded_stream,path=filepath_transcoded)


if __name__ == "__main__":
    main()