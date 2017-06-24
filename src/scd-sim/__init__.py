import os
import sys
import argparse
import logging
import numpy as np

import simulate
from simulation_builder import SimulationBuilder

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)


def check_files_exist(file_names):
    """ Check that the given file names exist

    @param file_names: list of strings representing file names
    @return whether the file names exist
    """
    for file_name in file_names:
        if not os.path.exists(file_name):
            logger.error("Cannot find file named %s" % file_name)
            return False
    return True


def check_is_directory(directory):
    """ Check if a directory exits

    @param directory: a string representing the directory path
    @return whether the directory exists
    """
    return os.path.exists(directory) and os.path.isdir(directory)


def make_data(args):
    if not check_files_exist(args.input_files):
        sys.exit(1)

    if not check_is_directory(args.output_dir):
        logger.error("Cannot find directory called %s" % args.output_dir)
        sys.exit(1)

    builder = SimulationBuilder()
    builder.instrument_name = "SXD"
    builder.wavelength_range = (.5, 10.)
    builder.extents = [-17, 17, -7, 17, 0, 33]
    builder.nbins = 300
    builder.temperature = 50.
    builder.background_alpha = 0.3e-3

    # make a mask for the instrument, only need to do this once
    mask_data = np.load(args.mask) 
    mask_data = mask_data.reshape([builder.nbins]*3)
    simulate.create_simulated_data(builder, args.input_files, mask_data, 
                                   args.prefix, args.output_dir)    


def make_mask(args):
    extents = [-17, 17, -7, 17, 0, 33]
    simulate.create_mask_workspace(args.instrument_file, args.output_file, 
                                   args.nbins, extents)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    create_parser = subparsers.add_parser('create')
    create_parser.add_argument('-i', '--input-files', nargs='+', type=str)
    create_parser.add_argument('-o', '--output-dir', type=str)
    create_parser.add_argument('-p', '--prefix', type=str, default='SXD')
    create_parser.add_argument('-m', '--mask', type=str)

    mask_parser = subparsers.add_parser('mask')
    mask_parser.add_argument('-t', '--instrument-file', type=str)
    mask_parser.add_argument('-i', '--input-file', type=str)
    mask_parser.add_argument('-o', '--output-file', type=str)
    mask_parser.add_argument('-n', '--nbins', type=int, default=300)

    args = parser.parse_args()

    if args.command == "create":
        make_data(args)
    else:
        make_mask(args)


