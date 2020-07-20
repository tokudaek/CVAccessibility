#!/usr/bin/env python3
"""Convert graphml -> xnet"""

import argparse
import logging
import time
from os.path import join as pjoin
from logging import debug, info
import igraph
import xnet
import subprocess
import shlex
import numpy as np
import os

import xnet
##########################################################
def main():
    t0 = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graphml', required=True, help='graphml')
    parser.add_argument('--output', default='', help='Output  xnet path')
    args = parser.parse_args()
    
    logging.basicConfig(format='[%(asctime)s] %(message)s',
    datefmt='%Y%m%d %H:%M', level=logging.INFO)

    if args.output == '':
        xnetpath = pjoin('/tmp/', 
                os.path.basename(args.graphml).replace('.graphml', '.xnet'))
    else:
        xnetpath = args.output
    
    info('Loading graph...')
    g = igraph.Graph.Read(args.graphml)

    for attr in ['ref', 'highway', 'osmid', 'id']:
        del(g.vs[attr])
    for attr in g.es.attributes():
        del(g.es[attr])

    info('Converting to xnet...')
    xnet.igraph2xnet(g, xnetpath)
    info('Sucessfully generated {}'.format(xnetpath))

###########################################################
if __name__ == "__main__":
    main()
