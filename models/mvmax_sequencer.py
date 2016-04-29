# -*- coding: utf-8 -*-
"""
Run Sequencer with specific model
"""

import argparse
import os
import sys
import logging
import sequencer
from sequencer import NetworkPlan
from sequencer.Models import EnergyMaximizeReturn

if __name__ == '__main__':
    # setup log
    logger = logging.getLogger('sequencer')

    logger.info("sequencer %s (Python %s)" % (
                    sequencer.__version__,
                    '.'.join(map(str, sys.version_info[:3]))))

    parser = argparse.ArgumentParser(
                description="Run Sequencer on MVMax derived scenario")
    parser.add_argument("-i", "--input-directory", default="data/input",
                        help="the input directory")
    parser.add_argument("-o", "--output-directory", default="data/output",
                        help="the output directory")

    args = parser.parse_args()
    csv_file = os.path.join(args.input_directory, "metrics-local.csv")
    shp_file = os.path.join(args.input_directory, "networks-proposed.shp")

    nwp = NetworkPlan.from_files(shp_file, csv_file, prioritize='Population')
    model = EnergyMaximizeReturn(nwp)

    results = model.sequence()
    model.output(args.output_directory)
