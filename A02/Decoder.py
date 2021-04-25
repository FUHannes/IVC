import numpy as np

class Decoder:

    def __init__(self):
        pass

    def __call__(self,encoded_stream,path = None):

        self.decode(encoded_stream)

        if(path is not None):
            self.write_file(path)

        return self.decoded_data

    def write_file(self,path,decoded_data=None):

        if(decoded_data is not None):
            self.decoded_data=decoded_data

        file = open(path, "wb")
        file.write(self.decoded_data)
        file.close()
        return True

    def decode(self,encoded_stream):

        #check whether the wrong files are decoded
        assert encoded_stream[:8] == b'IVC_SS21'

        #version check for backwards compatibility
        if encoded_stream[8:13] == b'v0001':
            print("decoding version 0001 ..")

            # get metadata
            block_size = int.from_bytes(encoded_stream[13:15],"big")
            blocks_x = int.from_bytes(encoded_stream[15:17],"big")
            blocks_y = int.from_bytes(encoded_stream[17:19],"big")

            # retreiving blocks from binary

            blocks = np.frombuffer(encoded_stream[19:],dtype=np.uint8)
            print(blocks.shape)

            # actual decoding
            pgm_image_data = encoded_stream[19:]

            pgm_metadata = f'P5\n{blocks_x*block_size} {blocks_y*block_size}\n255\n'.encode()

            self.decoded_data = pgm_metadata + pgm_image_data
            return self.decoded_data

        raise Exception("Version not Found")
