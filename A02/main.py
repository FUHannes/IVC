from Encoder import Encoder as Enc
from Decoder import Decoder as Dec

def main():
    filepath_raw = "/home/hannes/uni/video_enc/ivc-ss21/A01/pgm/Berlin.pgm" or input("file to transcode: ")
    filepath_encoded = "/home/hannes/uni/video_enc/ivc-ss21/out/Berlin.ivc21" or input("encoded path: ")
    filepath_transcoded = "/home/hannes/uni/video_enc/ivc-ss21/A01/pgm/Berlin_transcoded.pgm" or input("file to output: ")

    enc = Enc()
    dec = Dec()

    encoded_stream = enc(filepath_raw)

    enc_file = open(filepath_encoded,"wb")
    enc_file.write(encoded_stream)
    enc_file.close()

    dec(encoded_stream,path=filepath_transcoded)


if __name__ == "__main__":
    main()