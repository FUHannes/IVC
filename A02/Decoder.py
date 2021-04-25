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
            
            blocks = np.zeros([blocks_x,blocks_y,block_size,block_size])
            counter = 0
            current_block = np.zeros([block_size^2])
            for byte in encoded_stream[19:]:
                if counter%(block_size^2) == 0:
                    blocks[counter/block_size,(counter/block_size)%blocks_x]
                    counter = 0
                    continue
                current_block[counter]=byte
                counter += 1

            # actual decoding
            pgm_image_data=b''

            pgm_metadata = f'P5\n{blocks_x_count*block_size} {blocks_y_count*block_size}\n255\n'.encode()

            self.decoded_data = pgm_metadata + pgm_image_data
            return self.decoded_data

        raise Exception("Version not Found")
