import numpy as np

class Encoder:

    class PGM:
        def __init__(self,raw_bytes):
            self.raw_bytes=raw_bytes
            self._get_img_data_()

        def _get_img_data_(self):

            self.width = 0
            self.height = 0
            self.max_pixel_val = 0
            self.data_start = -1

            width_done = False
            line = 0
            for byte in self.raw_bytes:

                self.data_start += 1
                
                if chr(byte) == '\n':
                    line +=1
                    continue

                if line == 1 :
                    if chr(byte) == ' ':
                        width_done = True
                        continue
                    if not width_done:
                        self.width = self.width*10 + int(chr(byte))
                    else:
                        self.height = self.height*10 + int(chr(byte))

                if line == 2 and not chr(byte) == ' ':
                    self.max_pixel_val = self.max_pixel_val*10 + int(chr(byte))

                if line == 3:
                    break 

            self.data = self.raw_bytes[self.data_start:]
            

    def __init__(self,block_size=8):
        self.block_size=block_size

    def __call__(self,path):

        #automatic pipeline
        self.read_raw_bytes(path)
        self.encode()
        return self.encoded_stream

    def read_raw_bytes(self,path):

        #opening and reading pgm file
        self.raw_bytes = open(path, "rb").read()
        return self.raw_bytes

    def _get_img_data_(self):
        self.pgm=self.PGM(self.raw_bytes)

    def encode(self,raw_bytes=None):

        if (raw_bytes is not None):
            self.raw_bytes = raw_bytes

        self._get_img_data_()

        #cut away additional data and convert to ndarray for performance improvements
        data = np.array(bytearray(self.pgm.data)[:self.pgm.height*self.pgm.width])

        data_scanlines = data.reshape(self.pgm.height,self.pgm.width)

        # currently no img padding so the img size must be an exact multiple of the block size in both directions
        assert self.pgm.width % self.block_size == 0 and self.pgm.height % self.block_size == 0
        
        blocks_x = int(self.pgm.height/self.block_size)
        blocks_y = int(self.pgm.width/self.block_size)

        data_blocks = np.zeros([blocks_x,blocks_y,self.block_size,self.block_size])
        for xi in range(blocks_x):
            for yi in range(blocks_y):
                data_blocks[xi,yi] = data_scanlines[xi:xi+self.block_size, yi:yi+self.block_size]

        magic_header="IVC_SS21".encode("ascii")

        self.encoded_stream=magic_header
        return self.encoded_stream
