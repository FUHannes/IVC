import numpy as np
# !pip install joblib
from joblib import Parallel, delayed
from functools import reduce

class Decoder:

    def __init__(self,multithreaded=True):
        self.multithreaded=multithreaded

    #automatic pipeline
    def __call__(self,input_path,output_path=None):
        self.read_in(input_path)
        self.decode()
        if output_path is not None:
            self.write_out(output_path)
        return self.decoded_stream

    #opening and reading a binary file
    def read_in(self,input_path):
        in_file = open(input_path, "rb")
        self.raw_bytes = in_file.read()
        in_file.close()
        return self.raw_bytes

    #opening and writing a binary file
    def write_out(self,output_path):
        out_file = open(output_path, "wb")
        out_file.write(self.decoded_stream)
        out_file.close()
        return True

    
    def decode(self,raw_bytes=None):

        if (raw_bytes is not None):
            self.raw_bytes = raw_bytes

        #check whether the wrong files are decoded
        assert self.raw_bytes[:8] == b'IVC_SS21'

        self.version = int(self.raw_bytes[9:13].decode("ascii"))
        print(f"decoding version {self.version} ..")

        if True: #possible version switching for incompatible header format here
            # get metadata
            self.block_size = int.from_bytes(self.raw_bytes[13:15],"big")
            blocks_x = int.from_bytes(self.raw_bytes[15:17],"big")
            blocks_y = int.from_bytes(self.raw_bytes[17:19],"big")

            # retreiving blocks from binary                              
            encoded_blocks = np.frombuffer(self.raw_bytes[19:],dtype=np.uint8).reshape([blocks_x,blocks_y,-1])

            #setup empty blocks
            decoded_blocks = np.zeros([blocks_x,blocks_y,self.block_size,self.block_size],dtype=np.uint8)

            if self.multithreaded:
                #multithreaded block decoding
                def thread_task(encoded_block_stream):
                    decoded_block_stream=np.zeros([blocks_y,self.block_size,self.block_size],dtype=np.uint8)
                    for yi in range(blocks_y):
                        decoded_block_stream[yi] = self._decode_block_(encoded_block_stream[yi])
                    return decoded_block_stream

                decoded_blocks = Parallel(n_jobs=blocks_x, backend="threading")(map(delayed(thread_task), encoded_blocks))

            else:
                for xi in range(blocks_x):
                    for yi in range(blocks_y):
                        decoded_blocks[xi,yi] = self._decode_block_(encoded_blocks[xi,yi,:])

            #deblock and convert to bytestream
            pgm_image_data = np.swapaxes(decoded_blocks,1,2).ravel().tobytes()

        pgm_metadata = f'P5\n{blocks_x*self.block_size} {blocks_y*self.block_size}\n255\n'.encode()

        self.decoded_stream = pgm_metadata + pgm_image_data
        return self.decoded_stream


    def _decode_block_(self,block):

        #version check for backwards compatibility
        if self.version == 1:
            block = block.reshape([self.block_size,self.block_size])#not much to decode in version 1
            return block

        raise Exception("incompatible version")
