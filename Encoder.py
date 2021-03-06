import numpy as np
from tqdm import tqdm
import random
import math

from EntropyEncoder import EntropyEncoder, bitsUsed
from PredictionCalculator import PredictionCalculator
from PredictionCalculator import PredictionMode
from OBitstream import OBitstream
from dct import Transformation


# read PGM image
def read_image(input_path):
    with open(input_path, 'rb') as file:
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
        image = np.zeros([height, width], dtype=np.uint8)
        for h in range(0, height):
            for w in range(0, width):
                byte = file.read(1)
                if not byte:
                    raise Exception('Encoder: PGM image is corrupted')
                image[h, w] = byte[0]
        return image


def read_video(input_path, width, height, n_frames):
    with open(input_path, 'rb') as file:
        n_bytes = width * height * n_frames
        frames = file.read(n_bytes)
    _frames = np.frombuffer(frames, dtype='uint8')
    _frames = _frames.reshape(n_frames, height, width)

    return _frames


def sort_diagonal(mat: np.ndarray) -> np.ndarray:
    res = []
    (rows, columns) = mat.shape
    for line in range(1, (rows + columns)):

        start_col = max(0, line - rows)
        count = min(line, (columns - start_col), rows)

        for j in range(0, count):
            res.append(mat[min(rows, line) - j - 1][start_col + j])
    return np.array(res)


class Encoder:

    def __init__(self, input_path, output_path, block_size, QP, fast_search, reconstruction_path=None):
        self.input_path = input_path
        self.output_path = output_path
        self.block_size = block_size
        self.qp = QP
        self.qs = 2 ** (self.qp / 4)
        self.image_reconstructed = None
        self.image_reconstructed_array = []
        self.entropyEncoder = None
        self.reconstruction_path = reconstruction_path
        self.raw_video = False
        self.transformation = Transformation(block_size)
        self.search_range = 0
        self.rmv = []
        self.fast_search = fast_search

    def init_obitstream(self, img_height, img_width, path):
        outputBitstream = OBitstream(path)
        outputBitstream.addBits(img_width, 16)
        outputBitstream.addBits(img_height, 16)
        outputBitstream.addBits(self.block_size, 16)
        outputBitstream.addBits(self.qp, 8)
        return outputBitstream

    def set_image_size(self, width, height):
        self.image_height = height
        self.image_width = width
        self.pad_height = self.block_size - self.image_height % self.block_size if self.image_height % self.block_size != 0 else 0
        self.pad_width = self.block_size - self.image_width % self.block_size if self.image_width % self.block_size != 0 else 0

    def _add_padding(self):
        self.image = np.pad(self.image, ((0, self.pad_height), (0, self.pad_width)), "edge")

    # Gets an image and return an encoded bitstream.
    def encode_image(self):
        self.image = read_image(self.input_path)
        self.set_image_size(width=self.image.shape[1], height=self.image.shape[0])

        # open bitstream and write header
        self.outputBitstream = self.init_obitstream(self.image_height, self.image_width, self.output_path)

        self.encode_frame_intra(show_frame_progress=True)

        # terminate bitstream
        self.outputBitstream.terminate()
        if self.reconstruction_path:
            self.image_reconstructed_array.append(self.image_reconstructed)
            self.write_out()

    def calculate_lookup_table(self):
        rmv = []
        for i in range(4 * self.search_range + 3):
            rmv.append(2*bitsUsed(i) +1)
        return rmv

    def encode_video(self, width, height, n_frames, search_range):
        self.raw_video = True
        video = read_video(self.input_path, width, height, n_frames)
        self.set_image_size(width, height)
        self.search_range = search_range
        self.rmv = self.calculate_lookup_table()

        # open bitstream and write header
        self.outputBitstream = self.init_obitstream(height, width, self.output_path)

        is_first_frame = True
        for frame in tqdm(video):
            self.image = frame
            if not is_first_frame:
                self.encode_frame_inter()
            else:
                self.encode_frame_intra()
                is_first_frame = False

            self.padded_rec_img = np.pad(self.image_reconstructed, ((self.block_size, self.block_size), (self.block_size, self.block_size)), "edge")

            self.image_reconstructed_array.append(self.image_reconstructed)

        # terminate bitstream
        self.outputBitstream.terminate()
        if self.reconstruction_path:
            self.write_out()

    # If you change this methods pay attention because is used in both encode_image and encode_video() methods
    # This method should be called for the first frame only
    def encode_frame_intra(self, show_frame_progress=False):
        # add padding
        self._add_padding()
        self.image_reconstructed = np.zeros([self.image_height + self.pad_height, self.image_width + self.pad_width],
                                            dtype=np.uint8)

        # start new arithmetic codeword for each frame
        self.entropyEncoder = EntropyEncoder(self.outputBitstream, self.block_size)

        # initialize intra prediction calculator
        self.pred_calc = PredictionCalculator(self.image_reconstructed, self.block_size)

        if show_frame_progress:
            total_blocks = ((self.image_height + self.pad_height) // self.block_size) * (
                    (self.image_width + self.pad_width) // self.block_size)
            progress_bar = tqdm(total=total_blocks)

        # process image
        lagrange_multiplier = 0.1 * self.qs * self.qs
        for yi in range(0, self.image_height + self.pad_height, self.block_size):
            for xi in range(0, self.image_width + self.pad_width, self.block_size):
                if show_frame_progress:
                    progress_bar.update()

                # mode decision
                cost_mode_tuples = []
                for pred_mode in PredictionMode:
                    cost, rec_block, qidx_list = self.test_encode_block_intra_pic(xi, yi, pred_mode, lagrange_multiplier)
                    cost_mode_tuples.append( (cost, pred_mode, rec_block, qidx_list) )
                min_cost_mode = min(cost_mode_tuples, key=lambda t: t[0])
                pred_mode = min_cost_mode[1]
                rec_block = min_cost_mode[2]
                qidx_list = min_cost_mode[3]

                # encoding using selected mode
                self.encode_block_intra_pic(xi, yi, rec_block, qidx_list, pred_mode)

        if show_frame_progress:
            progress_bar.close()

        # terminate arithmetic codeword (but keep output bitstream alive)
        self.entropyEncoder.terminate()

    # This method should be called for all frames except the first one
    def encode_frame_inter(self):
        # add padding
        self._add_padding()

        
        self.image_reconstructed = np.zeros([self.image_height + self.pad_height, self.image_width + self.pad_width],
                                            dtype=np.uint8)

        # start new arithmetic codeword for each frame
        self.entropyEncoder = EntropyEncoder(self.outputBitstream, self.block_size)

        # initialize intra prediction calculator
        self.pred_calc = PredictionCalculator(self.image_reconstructed, self.block_size,
                                                    self.padded_rec_img)

        # process image
        lagrange_multiplier = 0.1 * self.qs * self.qs
        lagrange_root = math.sqrt(lagrange_multiplier)


        for yi in range(0, self.image_height + self.pad_height, self.block_size):
            for xi in range(0, self.image_width + self.pad_width, self.block_size):
                # estimate motion
                mxp, myp = self.pred_calc.get_mv_pred(xi, yi)
                mx, my = self.estimate_motion_vector(xi, yi, mxp, myp, lagrange_root)

                # mode decision between inter and dc mode
                inter_mode_cost, inter_rec, inter_qidx = self.test_encode_block_inter_pic(lagrange_multiplier, xi, yi, 1, mx, my, mxp, myp)
                dc_mode_cost, dc_rec, dc_qidx = self.test_encode_block_inter_pic(lagrange_multiplier, xi, yi, 0)
                if inter_mode_cost < dc_mode_cost:
                    self.encode_block_inter_pic(xi, yi, inter_rec, inter_qidx, 1, mx, my, mxp, myp)
                else:
                    self.encode_block_inter_pic(xi, yi, dc_rec, dc_qidx, 0)

        # terminate arithmetic codeword (but keep output bitstream alive)
        self.entropyEncoder.terminate()

    def find_start_mv(self, xi, yi, pred_x_mv, pred_y_mv, lagrange_root):
        candidates = self.pred_calc.get_start_mv_candidates(xi, yi)
        candidates = np.append(candidates, [(pred_x_mv, pred_y_mv)], axis=0)
        candidates = np.sign(candidates) * (np.abs(candidates) // 2)  # round candidates to integer precision (towards zero)

        start_mv = np.zeros(2, dtype='int')
        min_cost = float('inf')
        for mv in candidates:
            if mv[0] >= self.mx_min and mv[0] <= self.mx_max and mv[1] >= self.my_min and mv[1] <= self.my_max:
                cost = self.get_lagrangian_cost(mv, pred_x_mv, pred_y_mv, xi, yi, lagrange_root)
                if cost < min_cost:
                    min_cost = cost
                    start_mv = mv

        return start_mv

    def perf_log_step(self, current_x, current_y, center_x_mv, center_y_mv, diamond_size, lagrange_root, pred_x_mv, pred_y_mv):
        
        if diamond_size < 1:
            return (center_x_mv, center_y_mv)
        
        # Left motion vector
        lx_mv = center_x_mv - diamond_size  
        ly_mv = center_y_mv

        # Right motion vector
        rx_mv = center_x_mv + diamond_size
        ry_mv = center_y_mv 

        # Top motion vector
        tx_mv = center_x_mv
        ty_mv = center_y_mv + diamond_size

        # Bottom motion vector
        bx_mv = center_x_mv
        by_mv = center_y_mv - diamond_size

        candidates = [(lx_mv, ly_mv), (rx_mv, ry_mv), (tx_mv, ty_mv), (bx_mv, by_mv), (center_x_mv, center_y_mv)]

        candidates = list(filter(lambda mvs: mvs[0] >= self.mx_min and mvs[0] <= self.mx_max and mvs[1] >= self.my_min and mvs[1] <= self.my_max, candidates))
        
        min_cost = float('inf')

        for mv in candidates:
            cost = self.get_lagrangian_cost(mv, pred_x_mv, pred_y_mv, current_x, current_y, lagrange_root)
            if cost < min_cost:
                min_cost = cost
                min_cost_mv = mv
            if cost == min_cost and mv[0] == center_x_mv and mv[1] == center_y_mv:
                min_cost_mv = (center_x_mv, center_y_mv)

        if min_cost_mv[0] == center_x_mv and min_cost_mv[1] == center_y_mv:
            diamond_size //= 2
        
        return self.perf_log_step(current_x, current_y, min_cost_mv[0], min_cost_mv[1], diamond_size, lagrange_root, pred_x_mv, pred_y_mv)
    
    def get_lagrangian_cost(self, cand_mv, pred_x_mv, pred_y_mv, current_x, current_y, lagrange_root):

        cand_block = self.padded_rec_img[current_y + cand_mv[1]  + self.block_size : current_y + cand_mv[1] +  2 * self.block_size,
            current_x + cand_mv[0] + self.block_size : current_x + cand_mv[0] + 2 * self.block_size]

        curr_block = self.image[current_y : current_y + self.block_size, current_x : current_x + self.block_size]

        _sad = self.sum_absolute_differences(cand_block, curr_block)
        diff_mx = abs(2 * cand_mv[0] - pred_x_mv)  # predictors have half-sample precision
        diff_my = abs(2 * cand_mv[1] - pred_y_mv)
        lagrangian_cost = _sad + lagrange_root * (self.rmv[diff_mx] + self.rmv[diff_my])

        return lagrangian_cost

    def do_log_search(self, xi, yi, pred_x_mv, pred_y_mv, lagrange_root):

        self.mx_min = max(-self.search_range, -(xi + self.block_size))
        self.my_min = max(-self.search_range, -(yi + self.block_size))
        self.mx_max = min(self.search_range, self.padded_rec_img.shape[1] - xi - 2 * self.block_size)
        self.my_max = min(self.search_range, self.padded_rec_img.shape[0] - yi - 2 * self.block_size)

        start = self.find_start_mv(xi, yi, pred_x_mv, pred_y_mv, lagrange_root)

        return self.perf_log_step(xi, yi, start[0], start[1], 2, lagrange_root, pred_x_mv, pred_y_mv)

    def estimate_motion_vector(self, xi, yi, mxp, myp, lagrange_root):
        # integer motion vector
        if self.fast_search:
            int_mx, int_my = self.do_log_search(xi, yi, mxp, myp, lagrange_root)
        else:
            int_mx, int_my = self.estimate_integer_motion_vector_full_search(xi, yi, mxp, myp, lagrange_root)

        # half-sample refinement
        mx, my = self.half_sample_refinement(xi, yi, int_mx, int_my, mxp, myp, lagrange_root)

        return mx, my

    def estimate_integer_motion_vector_full_search(self, xi, yi, mxp, myp, lagrange_root):
        minimum_lagrangian_cost = float('inf')

        mx = 0
        my = 0

        mx_min = max(-self.search_range, -(xi + self.block_size))
        my_min = max(-self.search_range, -(yi + self.block_size))
        mx_max = min(self.search_range, self.padded_rec_img.shape[1] - xi - 2 * self.block_size)
        my_max = min(self.search_range, self.padded_rec_img.shape[0] - yi - 2 * self.block_size)

        current_block = self.image[yi:yi + self.block_size, xi:xi + self.block_size]
        for _my in range(my_min, my_max + 1):
            for _mx in range(mx_min, mx_max + 1):
                search_block = self.padded_rec_img[yi + _my + self.block_size:yi + _my + 2 * self.block_size,
                           xi + _mx + self.block_size:xi + _mx + 2 * self.block_size]
                _sad = self.sum_absolute_differences(search_block, current_block)
                diff_mx = abs(2*_mx - mxp) # pred is half-sample accurate
                diff_my = abs(2*_my - myp) # while mx/my are sample accurate
                lagrangian_cost = _sad + lagrange_root * (self.rmv[diff_mx] +self.rmv[diff_my])
                if lagrangian_cost < minimum_lagrangian_cost:
                    minimum_lagrangian_cost = lagrangian_cost
                    mx = _mx
                    my = _my

        return mx, my
 
    def half_sample_refinement(self, xi, yi, integer_mx, integer_my, mxp, myp, lagrange_root):
        minimum_lagrangian_cost = float('inf')

        int_subsample_mx = 2 * integer_mx
        int_subsample_my = 2 * integer_my

        mx_min = int_subsample_mx - 1
        my_min = int_subsample_my - 1
        mx_max = int_subsample_mx + 2
        my_max = int_subsample_my + 2

        current_block = self.image[yi:yi + self.block_size, xi:xi + self.block_size]
        for _my in range(my_min, my_max):
            for _mx in range(mx_min, mx_max):
                search_block = self.pred_calc.get_inter_prediction(xi, yi, _mx, _my)
                _sad = self.sum_absolute_differences(search_block, current_block)

                diff_mx = abs(_mx - mxp)
                diff_my = abs(_my - myp)
                lagrangian_cost = _sad + lagrange_root * (self.rmv[diff_mx] + self.rmv[diff_my])
                if lagrangian_cost < minimum_lagrangian_cost:
                    minimum_lagrangian_cost = lagrangian_cost
                    subsample_mx = _mx
                    subsample_my = _my

        return subsample_mx, subsample_my

    def sum_absolute_differences(self, a, b):
        # Compute the sum of the absolute differences
        return np.sum(np.abs(np.subtract(a, b, dtype=np.int)))

    def reconstruct_block(self, pred_block, q_idx_block, x, y, prediction_mode):
        # reconstruct transform coefficients from quantization indexes
        recBlock = q_idx_block * self.qs
        # invoke 2D Transform inverse
        recBlock = self.transformation.backward_transform(recBlock, prediction_mode)
        # invoke prediction function (see 4.3 DC prediction)
        recBlock += pred_block
        recBlock = np.clip(recBlock, 0, 255).astype('uint8')
        return recBlock

    # encode block of current picture
    def encode_block_intra_pic(self, x: int, y: int, rec_block, qidx_list, pred_mode: PredictionMode):
        # actual entropy encoding
        self.entropyEncoder.write_block_intra_pic(qidx_list, pred_mode)

        # reconstruction
        self.image_reconstructed[y:y + self.block_size, x:x + self.block_size] = rec_block

    # encode block of current picture
    def encode_block_inter_pic(self, x: int, y: int, rec_block, qidx_list, inter_flag: int, mx: int = 0, my: int = 0, mxp: int = 0, myp: int = 0):
        # actual entropy encoding
        self.entropyEncoder.write_block_inter_pic(qidx_list, inter_flag, mx - mxp, my - myp)

        # reconstruction and motion vector storage
        self.image_reconstructed[y:y + self.block_size, x:x + self.block_size] = rec_block
        if inter_flag:
            self.pred_calc.store_mv(x, y, mx, my)

    # Calculate lagrangian cost for given block and prediction mode.
    def test_encode_block_intra_pic(self, x: int, y: int, pred_mode: PredictionMode, lagrange_multiplier):
        # Accessor for current block.
        org_block = self.image[y:y + self.block_size, x:x + self.block_size]

        # Prediction, Transform, Quantization.
        pred_block = self.pred_calc.get_prediction(x, y, pred_mode)
        pred_error = org_block.astype('int') - pred_block

        trans_coeff = self.transformation.forward_transform(pred_error, pred_mode)

        q_idx_block = (np.sign(trans_coeff) * np.floor((np.abs(trans_coeff) / self.qs) + 0.4)).astype('int')

        rec_block = self.reconstruct_block(pred_block, q_idx_block, x, y, pred_mode)

        # Distortion calculation using SSD.
        distortion = np.sum(np.square(np.subtract(org_block, rec_block, dtype='int')))

        if pred_mode == PredictionMode.PLANAR_PREDICTION or pred_mode == PredictionMode.DC_PREDICTION:
            # diagonal scan
            scanned_block = sort_diagonal(q_idx_block)
        elif pred_mode == PredictionMode.HORIZONTAL_PREDICTION:
            # vertical scan: Transposed block
            scanned_block = q_idx_block.T
        elif pred_mode == PredictionMode.VERTICAL_PREDICTION:
            # horizontal scan: unchanged block
            scanned_block = q_idx_block

        bitrate_estimation = self.entropyEncoder.est_block_bits_intra_pic(pred_mode, scanned_block)

        # Return Lagrangian cost.
        return distortion + lagrange_multiplier * bitrate_estimation, rec_block, scanned_block

    # Calculate lagrangian cost for given block: Extent and use later
    def test_encode_block_inter_pic(self, lagrange_multiplier, x: int, y: int, inter_flag: int, mx: int = 0, my: int = 0, mxp: int = 0, myp: int = 0):
        # Accessor for current block.
        org_block = self.image[y:y + self.block_size, x:x + self.block_size]

        # Prediction
        if inter_flag:
            pred_block = self.pred_calc.get_inter_prediction(x, y, mx, my)
        else:
            pred_block = self.pred_calc.get_prediction(x, y, PredictionMode.DC_PREDICTION)

        # Prediction, Transform, Quantization.
        pred_error = org_block.astype('int') - pred_block

        trans_coeff = self.transformation.forward_transform(pred_error,
                                                            PredictionMode.DC_PREDICTION)  # set predMode=DC for using correct transform

        q_idx_block = (np.sign(trans_coeff) * np.floor((np.abs(trans_coeff) / self.qs) + 0.4)).astype('int')

        rec_block = self.reconstruct_block(pred_block, q_idx_block, x, y, PredictionMode.DC_PREDICTION)

        # Distortion calculation using SSD.
        distortion = np.sum(np.square(np.subtract(org_block, rec_block, dtype='int')))

        # diagonal scan
        scanned_block = sort_diagonal(q_idx_block)

        # Lagrangion cost if all quantization indices 0
        distortion_zeros = np.sum(np.square(np.subtract(org_block, pred_block, dtype='int')))
        zero_block = np.zeros([self.block_size, self.block_size], dtype='int')
        bitrate_estimation_zeros = self.entropyEncoder.est_block_bits_inter_pic(zero_block, inter_flag, mx - mxp, my - myp)
        lagrange_zeros = distortion_zeros + lagrange_multiplier * bitrate_estimation_zeros

        bitrate_estimation = self.entropyEncoder.est_block_bits_inter_pic(scanned_block, inter_flag, mx - mxp, my - myp)
        lagrange_real = distortion + lagrange_multiplier * bitrate_estimation

        # return lagrangian cost either with or without forcing QIs to zero
        if lagrange_real < lagrange_zeros:
            return lagrange_real, rec_block, scanned_block
        else:
            return lagrange_zeros, pred_block, zero_block

    # opening and writing a binary file
    def write_out(self):
        out_file = open(self.reconstruction_path, "wb")
        # write PGM header only if input was PGM image
        if not self.raw_video:
            out_file.write(f'P5\n{self.image_width} {self.image_height}\n255\n'.encode())
        # output all reconstructed frames (remove padding just before output)
        for image_reconstructed in self.image_reconstructed_array:
            # remove padding
            image_reconstructed = image_reconstructed[:self.image_height, :self.image_width]
            out_file.write(image_reconstructed.ravel().tobytes())
        out_file.close()
        return True
