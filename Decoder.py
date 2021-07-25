import numpy as np
from tqdm import tqdm

from EntropyDecoder import EntropyDecoder
from IBitstream import IBitstream
from dct import Transformation
from PredictionCalculator import PredictionCalculator
from PredictionCalculator import PredictionMode

from ColorSpaceConversion import *


def de_diagonalize(arr: np.ndarray) -> np.ndarray:
    x = 0
    y = 0
    x_start = 0

    wx, wy = arr.shape
    res = np.zeros(arr.shape, dtype=arr.dtype)
    arr = arr.flatten()
    for i in range(arr.size):
        res[y][x] = arr[i]
        x += 1
        y -= 1
        if y < 0 or x >= wx:
            y = min(x, wx - 1)

            if x >= wx:
                x_start += 1
            x = x_start
    return res


class Decoder:

    def __init__(self, input_path, output_path, pgm):
        self.output_path = output_path
        self.pgm = pgm
        self.bitstream = IBitstream(input_path)
        self.full_width, self.full_height = self.bitstream.get_bits(16), self.bitstream.get_bits(16) # todo swap reihenfolge for consistency
        self.block_size = self.bitstream.get_bits(16)
        self.set_image_size(self.full_height,self.full_width)
        self.qp = self.bitstream.get_bits(8)
        self.qs = 2 ** (self.qp / 4)

        self.isColored = self.bitstream.get_bit()
        if self.isColored:
            self.isRGB = not self.bitstream.get_bit()
            if not self.isRGB:
                self.isYCbCr = self.bitstream.get_bit()
                self.subsampling_num = self.bitstream.get_bits(2)

        self.image = np.zeros([self.image_height + self.pad_height, self.image_width+self.pad_width], dtype=np.uint8)
        self.image_array = []
        self.transformation = Transformation(self.block_size)

    def set_image_size(self, height, width): # remember width is y and shape[1]
        self.image_height = int(height)
        self.image_width = int(width)
        self.pad_height = self.block_size - self.image_height % self.block_size if self.image_height % self.block_size != 0 else 0
        self.pad_width = self.block_size - self.image_width % self.block_size if self.image_width % self.block_size != 0 else 0

    def decode_block_intra_pic(self, x: int, y: int):
        # entropy decoding (EntropyDecoder)
        ent_dec_block, prediction_mode = self.ent_dec.read_block_intra_pic()

        # scan unpacking
        if prediction_mode == PredictionMode.DC_PREDICTION or prediction_mode == PredictionMode.PLANAR_PREDICTION:
            ordered_block = de_diagonalize(ent_dec_block)
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            ordered_block = ent_dec_block.T
        elif prediction_mode == PredictionMode.VERTICAL_PREDICTION:
            ordered_block = ent_dec_block

        # de-quantization
        recBlock = ordered_block * self.qs
        # idct
        recBlock = self.transformation.backward_transform(recBlock, prediction_mode)
        # adding prediction
        recBlock = recBlock + self.pred_calc.get_prediction(x, y, prediction_mode) # += not possible 
        # clipping (0,255) and store to image
        self.image[x:x + self.block_size, y:y + self.block_size] = np.clip(recBlock, 0, 255).astype('uint8')

    def decode_block_inter_pic(self, x: int, y: int):
        # entropy decoding (EntropyDecoder)
        ent_dec_block, inter_flag, dmx, dmy = self.ent_dec.read_block_inter_pic()
        # reverse scanning
        ordered_block = de_diagonalize(ent_dec_block)
        # de-quantization
        recBlock = ordered_block * self.qs
        # idct
        recBlock = self.transformation.backward_transform(recBlock, PredictionMode.DC_PREDICTION) # set predMode=DC for correct transform

        # prediction
        if inter_flag:
            mxp, myp = self.pred_calc.get_mv_pred(x, y)
            mx = mxp + dmx
            my = myp + dmy
            self.pred_calc.store_mv(x, y, mx, my)
            recBlock += self.pred_calc.get_inter_prediction(x, y, mx, my)
        else:
            recBlock += self.pred_calc.get_prediction(x, y, PredictionMode.DC_PREDICTION)

        # clipping (0,255) and store to image
        self.image[x:x + self.block_size, y:y + self.block_size] = np.clip(recBlock, 0, 255).astype('uint8')

    # opening and writing a binary file
    def write_out(self):
        if self.isColored:
            with open(self.output_path, 'wb') as file:
                if self.pgm:
                    file.write(f'P6\n{self.full_width} {self.full_height}\n255\n'.encode())
                # padding is removed directly before output
                self.RGBimg = self.RGBimg[:self.full_height,:self.full_width,:]
                print(self.RGBimg.shape)
                file.write(self.RGBimg.ravel().tobytes())
        else:
            out_file = open(self.output_path, "wb")
            if self.pgm:
                out_file.write(f'P5\n{self.image_width} {self.image_height}\n255\n'.encode())
            for image in self.image_array:
                # padding is removed directly before output
                image = image[:self.image_height,:self.image_width]
                out_file.write(image.ravel().tobytes())
            out_file.close()
            return True

    def decode_next_frame_intra(self):
        self.pred_calc = PredictionCalculator(self.image, self.block_size)

        # start new arithmetic codeword
        self.ent_dec = EntropyDecoder(self.bitstream, self.block_size)

        # decode blocks
        for xi in tqdm(range(0, self.image_height + self.pad_height, self.block_size)):
            for yi in range(0, self.image_width + self.pad_width, self.block_size):
                self.decode_block_intra_pic(xi, yi)

        # terminate arithmatic codeword and check whether everything is ok so far
        is_ok = self.ent_dec.terminate()
        if not is_ok:
            raise Exception('Arithmetic codeword not correctly terminated at end of frame')

        self.image_array.append(self.image)
        if self.isColored:
            self.image = np.zeros(self.image.shape)
        else:
            self.image = np.zeros([self.image_height + self.pad_height, self.image_width + self.pad_width],dtype=np.uint8)

    def decode_next_frame_inter(self):
        padded_last_frame = np.pad(self.image_array[-1], ((self.block_size, self.block_size), (self.block_size, self.block_size)), "edge")
        self.pred_calc = PredictionCalculator(self.image, self.block_size, padded_last_frame)

        # start new arithmetic codeword
        self.ent_dec = EntropyDecoder(self.bitstream, self.block_size)

        # decode blocks
        for xi in tqdm(range(0, self.image_height + self.pad_height, self.block_size)):
            for yi in range(0, self.image_width + self.pad_width, self.block_size):
                self.decode_block_inter_pic(xi, yi)

        # terminate arithmatic codeword and check whether everything is ok so far
        is_ok = self.ent_dec.terminate()
        if not is_ok:
            raise Exception('Arithmetic codeword not correctly terminated at end of frame')
        

        self.image_array.append(self.image)
        self.image = np.zeros([self.image_height + self.pad_height, self.image_width + self.pad_width],
                               dtype=np.uint8)

    def decode_all_frames(self):
        self.decode_next_frame_intra()
        if self.isColored:
            if self.isRGB:
                self.decode_next_frame_intra() # G
                self.decode_next_frame_intra() # B
                self.RGBimg = np.moveaxis(self.image_array,0,-1)
            else:
                full_height, full_width = self.image_height, self.image_width
                if self.subsampling_num == 0:
                    self.decode_next_frame_intra() # Co/Cb
                    self.decode_next_frame_intra() # Cg/Cr
                elif self.subsampling_num == 1:
                    self.set_image_size(full_height,full_width/2)
                    self.decode_next_frame_intra() # Co/Cb
                    self.decode_next_frame_intra() # Cg/Cr
                    pass #TODO unsample
                elif self.subsampling_num == 2:
                    self.set_image_size(full_height,full_width/4)
                    pass #TODO
                elif self.subsampling_num == 3:
                    self.set_image_size(full_height/2,full_width/2)
                    pass #TODO
                else:
                    raise Exception('the given subsmapling is not supported')
                img = np.moveaxis(self.image_array,0,-1)
                self.RGBimg = ycbcr2rgb(img) if self.isYCbCr else ycocg2rgb(img)
        else:
            while not self.bitstream.is_EOF():
                self.decode_next_frame_inter()
        self.write_out()

