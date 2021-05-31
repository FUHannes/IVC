#!/usr/bin/env python3

import argparse

from test import *


def parse_args():
    parser = argparse.ArgumentParser(
        description='Tests encoder and decoder quality with respect to an original JPEG codec.')
    parser.add_argument('-f', '--file', dest='filename', type=str,
                        help='filename of input image without full path and suffix, e.g. Berlin', required=True)
    parser.add_argument('-v', '--version', dest='version', type=str, help='version of new encoder and decoder, e.g. \'1.0\'',
                        required=True)
    parser.add_argument('-vs', '--versions', dest='versions', type=str,
                        help='optional: comma separated versions that should be also compared to the new encoder and decoder version, e.g. \'1.0,2.0\'',
                        required=False)
    parser.add_argument('-bs', '--block-sizes', dest='bs', action='store_true',
                        help='optional: if set, curves for blocksizes [4,8,16,32] are computed')
    parser.add_argument('-print', dest='print', action='store_true',
                        help='optional: if set, no new data is computed but version curves are plotted')

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if args.bs:
        versions = args.versions.split(',') if args.versions else []
        for block_size in [4, 8, 16, 32]:
            version = args.version + "_bs-" + str(block_size)
            if not args.print:
                generate_data(args.filename, version, block_size)
            if not block_size == 32:
                versions += [version]
        versions = ','.join(versions)
        plot_data(args.filename, version, versions)
    else:
        if not args.print:
            generate_data(args.filename, args.version, 16)
        plot_data(args.filename, args.version, args.versions)


if __name__ == '__main__':
    main()
