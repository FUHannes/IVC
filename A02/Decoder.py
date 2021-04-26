import numpy as np
# !pip install joblib
from joblib import Parallel, delayed
from functools import reduce

class Decoder:

    def __init__(self,multithreaded=True):
        self.multithreaded=multithreaded

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

        self.version = int(encoded_stream[9:13].decode("ascii"))
        print(f"decoding version {self.version} ..")

        if True: #possible version switching for incompatible header format here
            # get metadata
            self.block_size = int.from_bytes(encoded_stream[13:15],"big")
            blocks_x = int.from_bytes(encoded_stream[15:17],"big")
            blocks_y = int.from_bytes(encoded_stream[17:19],"big")

            # retreiving blocks from binary                              
            encoded_blocks = np.frombuffer(encoded_stream[19:],dtype=np.uint8).reshape([blocks_x,blocks_y,-1])

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


        pgm_metadata = f'P5\n{blocks_x*self.block_size} {blocks_y*self.block_size}\n255\n'.encode()
        
        #deblock and convert to bytestream
        pgm_image_data = np.swapaxes(decoded_blocks,1,2).ravel().tobytes()

        self.decoded_data = pgm_metadata + pgm_image_data
        return self.decoded_data
        raise Exception("incompatible version")


    def _decode_block_(self,block):

        #version check for backwards compatibility
        if self.version == 1:
            block = block.reshape([self.block_size,self.block_size])#not much to decode in version 1
            return block

        raise Exception("incompatible version")
