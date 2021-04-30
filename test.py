import argparse
from tests.psnr import *


def parse_args():
    parser = argparse.ArgumentParser(description='Tests encoder and decoder quality with respect to an original JPEG codec.')
    parser.add_argument('-f', dest='filename', type=str, help='filename of input image without full path and suffix, e.g. Berlin', required=True)
    parser.add_argument('-v', dest='version', type=str, help='version of new encoder and decoder, e.g. \'1.0\'', required=True)
    parser.add_argument('-vs', dest='versions', type=str, help='comma separated versions that should be also compared to the new encoder and decoder version, e.g. \'1.0,2.0\'', required=True)

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    generate_data(args.filename, args.version)
    plot_data(args.filename, [args.versions, args.version])


if __name__ == '__main__':
    main()
