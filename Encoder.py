from functools import reduce

import numpy as np
# !pip install joblib
from joblib import Parallel, delayed


# import numba #use if further speedups required

class Encoder:

    def __init__(self, block_size=100, multithreaded=True, use_version=1):
        self.use_version = use_version
        self.block_size = block_size
        self.multithreaded = multithreaded

    # automatic pipeline
    def __call__(self, input_path, output_path=None):
        self.read_in(input_path)
        self.encode()
        if output_path is not None:
            self.write_out(output_path)
        return self.encoded_stream

    # opening and reading a binary file
    def read_in(self, input_path):
        in_file = open(input_path, "rb")
        self.raw_bytes = in_file.read()
        in_file.close()
        return self.raw_bytes

    # opening and writing a binary file
    def write_out(self, output_path):
        out_file = open(output_path, "wb")
        out_file.write(self.encoded_stream)
        out_file.close()
        return True

    # parsing all the pgm (meta-)data into a pgm object
    def _get_img_data_(self):
        self.pgm = self.PGM(self.raw_bytes)

    def encode(self, raw_bytes=None):

        if (raw_bytes is not None):
            self.raw_bytes = raw_bytes

        self._get_img_data_()

        # cut away additional data and convert to ndarray for performance improvements
        data = np.array(bytearray(self.pgm.data)[
                        :self.pgm.height * self.pgm.width])  # data = np.frombuffer(self.raw_bytes,offset=self.pgm.data_start-1,count=self.pgm.height*self.pgm.width)

        if False:
            # TODO : make padding work 
            # padding img so weird block_size s work
            width_diskrepanz = self.block_size - (self.pgm.width % self.block_size)
            height_diskrepanz = self.block_size - (self.pgm.height % self.block_size)
            self.width = self.pgm.width + width_diskrepanz
            self.height = self.pgm.height + height_diskrepanz
            unpadded_img = data.reshape([self.pgm.width, self.pgm.height])
            data = np.pad(unpadded_img, ((0, width_diskrepanz), (0, height_diskrepanz)), 'constant').ravel()

            blocks_x = int(self.width / self.block_size)
            blocks_y = int(self.height / self.block_size)

        else:
            blocks_x = int(self.pgm.width / self.block_size)
            blocks_y = int(self.pgm.height / self.block_size)
            # currently no img padding so the img size must be an exact multiple of the block size in both directions
            assert self.pgm.width % self.block_size == 0 and self.pgm.height % self.block_size == 0

        # this is where the magic happens
        data_blocks = np.swapaxes(data.reshape([blocks_x, self.block_size, blocks_y, self.block_size]), 1, 2)

        magic_header = b'IVC_SS21'

        metadata = b'v' + str(self.use_version).zfill(4).encode() + self.block_size.to_bytes(2,
                                                                                             "big") + blocks_x.to_bytes(
            2, "big") + blocks_y.to_bytes(2, "big")

        if self.multithreaded:
            # multithreaded block encoding
            def thread_task(arr):
                encoded_block_stream = b''
                for yi in range(blocks_y):
                    encoded_block_stream += self._encode_block_(arr[yi])
                return encoded_block_stream

            encoded_block_streams = Parallel(n_jobs=blocks_x, backend="threading")(
                map(delayed(thread_task), data_blocks))
            encoded_block_stream = reduce(lambda a, b: a + b, encoded_block_streams, b'')

        else:
            encoded_block_stream = b''
            for xi in range(blocks_x):
                for yi in range(blocks_y):
                    encoded_block_stream += self._encode_block_(data_blocks[xi, yi])

        self.encoded_stream = magic_header + metadata + encoded_block_stream
        return self.encoded_stream

    def _encode_block_(self, block):
        # switch versions so in the end we can do this automatically and plot our psnr progress
        if self.use_version == 1:
            return block.ravel().tobytes()

        raise Exception("incompatible version")

    class PGM:
        def __init__(self, raw_bytes):
            self.raw_bytes = raw_bytes
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
                    line += 1
                    continue

                if line == 1:
                    if chr(byte) == ' ':
                        width_done = True
                        continue
                    if not width_done:
                        self.width = self.width * 10 + int(chr(byte))
                    else:
                        self.height = self.height * 10 + int(chr(byte))

                if line == 2 and not chr(byte) == ' ':
                    self.max_pixel_val = self.max_pixel_val * 10 + int(chr(byte))

                if line == 3:
                    break

            self.data = self.raw_bytes[self.data_start:]
