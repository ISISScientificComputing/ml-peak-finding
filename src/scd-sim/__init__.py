import os
import sys
import argparse
import logging

import simulate

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-files', type=str, nargs='+')
    parser.add_argument('-o', '--output-dir', type=str)
    parser.add_argument('-p', '--prefix', type=str, default='SXD')

    args = parser.parse_args()

    if not check_files_exist(args.input_files):
        sys.exit(1)

    if not check_is_directory(args.output_dir):
        logger.error("Cannot find directory called %s" % args.output_dir)
        sys.exit(1)

    params = {
        "instrument_name": "SXD",
        "wavelength_range": (.5, 10.),
        "md_extents": [-17, 17, -7, 17, 0, 33],
        "mask_binning": 'SXD23767.raw',
        "mask_workspace":  "mask",
        "nbins": 300,
        "temperature": 50,
        "background_alpha": 0.3e-3,
        "output_directory": args.output_dir,
        "file_prefix": args.prefix
    }

    simulate.create_simulated_data(params, args.input_files)    


    

