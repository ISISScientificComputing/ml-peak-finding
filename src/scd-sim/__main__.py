import os
import sys
import argparse
import logging
import json
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


def load_config(path):
    with open(args.config, 'r') as f:
        return json.load(f)


def make_data(args, config):
    if not check_files_exist(args.input_files):
        sys.exit(1)

    if not check_is_directory(args.output_dir):
        logger.error("Cannot find directory called %s" % args.output_dir)
        sys.exit(1)

    builder = SimulationBuilder()
    builder.instrument_name = str(config['instrument_name'])
    builder.wavelength_range = tuple(config['wavelength_range'])
    builder.extents = config['extents']
    builder.nbins = config['nbins']
    builder.temperature = config['temperature']
    builder.background_alpha = config['alpha']

    # make a mask for the instrument, only need to do this once
    mask_data = np.load(args.mask) 
    mask_data = mask_data.reshape([builder.nbins]*3)
    simulate.create_simulated_data(builder, args.input_files, mask_data, 
                                   args.prefix, args.output_dir)    


def make_mask(args, config):
    simulate.create_mask_workspace(args.instrument_file, args.output_file, 
                                   config['nbins'], config['extents'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    create_parser = subparsers.add_parser('create')
    create_parser.add_argument('-c', '--config', type=str)
    create_parser.add_argument('-i', '--input-files', nargs='+', type=str)
    create_parser.add_argument('-o', '--output-dir', type=str)
    create_parser.add_argument('-p', '--prefix', type=str, default='SXD')
    create_parser.add_argument('-m', '--mask', type=str)

    mask_parser = subparsers.add_parser('mask')
    mask_parser.add_argument('-c', '--config', type=str)
    mask_parser.add_argument('-i', '--instrument-file', type=str)
    mask_parser.add_argument('-o', '--output-file', type=str)

    args = parser.parse_args()
    config = load_config(args.config)

    if args.command == "create":
        make_data(args, config)
    else:
        make_mask(args, config)


