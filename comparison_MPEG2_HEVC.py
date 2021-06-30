import os
import subprocess

import math
import pandas as pd

from Decoder import Decoder as Decoder
from Encoder import Encoder as Encoder

VIDEO_WIDTH = 416
VIDEO_HEIGHT = 240
VIDEO_SUFFIX = '.y'
DATA_ROOT_PATH = 'dat'
DATA_SUFFIX = '.dat'
VIDEOS_PATH = 'videos/original'
MPEG_OUTPUT = f'videos/test/MPEG2'
HEVC_OUTPUT = f'videos/test/HEVC'
OUR_OUTPUT = f'videos/test/our'

# Adjust on your machine
VIDEO_PSNR_TOOL_PATH = 'tools/psnr-raw-video/bin/AppleClang-12.0.0.12000032/psnrRaw'

NO_FRAMES = {
    'BasketballPass_416x240_50Hz_P400': {'n_frames': 501, 'fr': 50},
    'BQSquare_416x240_60Hz_P400': {'n_frames': 601, 'fr': 60},
    'Johnny_416x240_60Hz_P400': {'n_frames': 600, 'fr': 60},
    'RaceHorses_416x240_30Hz_P400': {'n_frames': 300, 'fr': 30},
}

if __name__ == '__main__':
    df_our = pd.DataFrame(columns=['bpp', 'db'])
    df_mpeg2 = pd.DataFrame(columns=['bpp', 'db'])
    df_hevc = pd.DataFrame(columns=['bpp', 'db'])

    if not os.path.exists(MPEG_OUTPUT):
        os.makedirs(MPEG_OUTPUT)

    if not os.path.exists(HEVC_OUTPUT):
        os.makedirs(HEVC_OUTPUT)

    if not os.path.exists(OUR_OUTPUT):
        os.makedirs(OUR_OUTPUT)

    for video in os.listdir(VIDEOS_PATH):
        filename = video.split('.')[0]
        n_frames = NO_FRAMES.get(filename)['n_frames']
        f_rate = NO_FRAMES.get(filename)['fr']
        """
            Our codec
        """
        for index, qp in enumerate([8, 12, 16, 20, 24]):
            export_filename = f'{OUR_OUTPUT}/{filename}_QP_{qp}'
            # Encode
            enc = Encoder(f'{VIDEOS_PATH}/{filename}.y', f'{export_filename}.txt', 16, qp, True)
            enc.encode_video(VIDEO_WIDTH, VIDEO_HEIGHT, n_frames, 16)
            # Decode
            dec = Decoder(f'{export_filename}.txt', f'{export_filename}.y', pgm=False)
            dec.decode_all_frames()

            # Run PSNR tool
            process = subprocess.run(
                [VIDEO_PSNR_TOOL_PATH, str(VIDEO_WIDTH), str(VIDEO_HEIGHT), "400", f'{VIDEOS_PATH}/{filename}.y',
                 f'{export_filename}.y', f'{export_filename}.txt', str(f_rate)], stdout=subprocess.PIPE)

            stdout = process.stdout.decode("utf-8")
            out = (stdout.split('\n\n')[2]).split()
            bpp, db = float(out[0]), float(out[1])
            db = 0.0 if math.isinf(db) else db
            df_our.loc[index] = [bpp, db]
            break

        # Store PSNR data
        version_path = os.path.join(DATA_ROOT_PATH, 'our')
        if not os.path.exists(version_path):
            os.mkdir(version_path)
        df_our.to_pickle(os.path.join(version_path, filename + DATA_SUFFIX))

        """
            MPEG-2
        """
        for index, qp in enumerate(range(2, 20)):
            export_filename = f'{MPEG_OUTPUT}/{filename}_QP_{qp}'
            # encode
            os.system(f'ffmpeg -f rawvideo -pix_fmt gray -s:v 416x240 -r 50.0 -i {VIDEOS_PATH}/{filename}.y \
                        -c:v mpeg2video -qscale:v {qp} -g 600 -bf 0 -vframes {n_frames} {export_filename}.mpg')
            # decode
            os.system(
                f'ffmpeg -i  {export_filename}.mpg -c:v rawvideo -pix_fmt gray {export_filename}.yuv')

            # # Run PSNR tool
            process = subprocess.run(
                [VIDEO_PSNR_TOOL_PATH, str(VIDEO_WIDTH), str(VIDEO_HEIGHT), "400", f'{VIDEOS_PATH}/{filename}.y',
                 f'{export_filename}.yuv', f'{export_filename}.mpg', str(f_rate)], stdout=subprocess.PIPE)

            stdout = process.stdout.decode("utf-8")
            out = (stdout.split('\n\n')[2]).split()
            bpp, db = float(out[0]), float(out[1])
            db = 0.0 if math.isinf(db) else db
            df_mpeg2.loc[index] = [bpp, db]

        # Store PSNR data
        # TODO: Investigate why DataFrame is empty after reading from filesystem
        version_path = os.path.join(DATA_ROOT_PATH, 'mpeg2')
        if not os.path.exists(version_path):
            os.mkdir(version_path)
        df_our.to_pickle(os.path.join(version_path, filename + DATA_SUFFIX))

        """
        " HEVC
        """
        for index, qp in enumerate(range(8, 32)):
            export_filename = f'{HEVC_OUTPUT}/{filename}_QP_{qp}'
            # encode
            os.system(
                f'ffmpeg -f rawvideo -pix_fmt gray -s:v 416x240 -r 50.0 -i {VIDEOS_PATH}/{filename}.y -c:v libx264 -crf {qp} -g 600 -bf 0 -vframes {n_frames} {export_filename}.mp4')
            # decode
            os.system(f'ffmpeg -i {export_filename}.mp4 -c:v rawvideo -pix_fmt gray {export_filename}.yuv')

            process = subprocess.run(
                [VIDEO_PSNR_TOOL_PATH, str(VIDEO_WIDTH), str(VIDEO_HEIGHT), "400", f'{VIDEOS_PATH}/{filename}.y',
                 f'{export_filename}.yuv', f'{export_filename}.mp4', str(f_rate)], stdout=subprocess.PIPE)

            stdout = process.stdout.decode("utf-8")
            out = (stdout.split('\n\n')[2]).split()
            bpp, db = float(out[0]), float(out[1])
            db = 0.0 if math.isinf(db) else db
            df_hevc.loc[index] = [bpp, db]

        # Store PSNR data
        version_path = os.path.join(DATA_ROOT_PATH, 'mpeg2')
        if not os.path.exists(version_path):
            os.mkdir(version_path)
        df_our.to_pickle(os.path.join(version_path, filename + DATA_SUFFIX))
