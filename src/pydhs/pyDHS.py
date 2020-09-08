# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
[options.entry_points] section in setup.cfg:

    console_scripts =
         pyDHS = pydhs.skeleton:run

Then run `python setup.py install` which will install the command `pyDHS`
inside your current environment.
Besides console scripts, the header (i.e. until _logger...) of this file can
also be used as template for Python modules.

Note: This skeleton file can be safely removed if not needed!
"""

import argparse
import sys
import logging
from pydhs import dcss
from pydhs import test
from pydhs.test import testDHS

from pydhs import __version__

__author__ = "Scott Classen"
__copyright__ = "Scott Classen"
__license__ = "mit"

_logger = logging.getLogger(__name__)

def parse_args(args):
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description="DHS Distributed Hardware Server")
    parser.add_argument(
        "--version",
        action="version",
        version="pyDHS {ver}".format(ver=__version__))
    parser.add_argument(
        dest="beamline",
        help="Beamline Name (e.g. BL-831)",
        metavar="Beamline")
    parser.add_argument(
        dest="dhs_name",
        help="DHS_Name",
        metavar="DHS_Name")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO)
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG)
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def main(args):
   """Main entry point allowing external calls

   Args:
      args ([str]): command line parameter list
   """
   args = parse_args(args)
   setup_logging(args.loglevel)
   _logger.info("Starting pyDHS")

   # start communication with DCSS
   print("connect to DCSS for beamline: {}".format(args.beamline))
   # perform DHS-specific stuff 
   print("DHS-specific stuff: {}".format(args.dhs_name))

   cv = test.myClassVar
   print("cv: {}".format(cv))
   my_dhs = testDHS.testDHS('my_test_dhs', '10.11.12.13')
   # my_dhs.loop()


   _logger.info("Ending pyDHS")


def run():
   """Entry point for console_scripts
   """
   main(sys.argv[1:])


if __name__ == "__main__":
   run()
