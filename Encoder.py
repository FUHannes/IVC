import numpy as np

from EntropyEncoder import EntropyEncoder
from OBitstream import OBitstream


def _read_image(input_path):
    file = open(input_path, 'rb')
    if not file:
        raise Exception('Encoder: Could not open image file')
    # read meta data
    header = file.readline()
    if header != b'P5\n':
        raise Exception('Encoder: No PGM image')
    imgSize = file.readline()
    maxVal = file.readline()
    if maxVal != b'255\n':
        raise Exception('Encoder: PGM image has unexpected bit depth')
    width, height = str(imgSize).split(' ')
    width = int(width[2:])
    height = int(height[:len(height) - 3])
    # create image and read data
    image = np.zeros([height, width])
    for h in range(0, height):
        for w in range(0, width):
            byte = file.read(1)
            if not byte:
                raise Exception('Encoder: PGM image is corrupted')
            image[h, w] = byte[0]
    return image


class Encoder:

    def __init__(self, input_path, output_path, block_size, QP):
        self.input_path = input_path
        self.output_path = output_path
        self.block_size = block_size
        self.qp = QP
        self.qs = 2 ** (self.qp / 4)
        self.image = None
        self.entropyEncoder = None

    # Gets an image and return an encoded bitstream. 
    def encode_image(self):
        # read image
        self.image = _read_image(self.input_path)
        imgHeight = self.image.shape[0]
        imgWidth = self.image.shape[1]
        # open bitstream and write header
        outputBitstream = OBitstream(self.output_path)
        outputBitstream.addBits(imgWidth, 16)
        outputBitstream.addBits(imgHeight, 16)
        outputBitstream.addBits(self.block_size, 16)
        outputBitstream.addBits(self.qp, 8)
        # initialize entropy encoder
        self.entropyEncoder = EntropyEncoder(outputBitstream)
        # process image
        for yi in range(0, imgHeight, self.block_size):
            for xi in range(0, imgWidth, self.block_size):
                self.encode_block(xi, yi)
        # terminate bitstream
        self.entropyEncoder.terminate()
        outputBitstream.terminate()

    # encode block of current picture
    def encode_block(self, x: int, y: int):
        # accessor for current block
        currBlock = self.image[y:y + self.block_size, x:x + self.block_size]
        # prediction
        currBlock -= 128
        # quantization
        qIdxBlock = np.round(currBlock / self.qs, decimals=0).astype('int')
        # entropy coding
        self.entropyEncoder.writeQIndexBlock(qIdxBlock)

    # read PGM image
