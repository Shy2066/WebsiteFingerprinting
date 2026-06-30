import logging
import argparse
import pandas as pd
import numpy as np
import glob
import os
import sys
import multiprocessing as mp
from datetime import datetime

logger = logging.getLogger('ovhd')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, 'log')


def resolve_log_path(log_arg, input_dir):
    if log_arg == 'stdout':
        return None
    dataset_name = os.path.basename(os.path.normpath(input_dir)) or 'dataset'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_name = '{}_overhead_{}.log'.format(dataset_name, timestamp)
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
    return os.path.join(LOG_DIR, log_name)


def config_logger(args):
    # Set file
    log_file = sys.stdout
    if args.log != 'stdout':
        log_path = resolve_log_path(args.log, args.dir)
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        log_file = open(log_path, 'w')
    ch = logging.StreamHandler(log_file)

    # Set logging format
    LOG_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
    ch.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(ch)

    # Set level format
    logger.setLevel(logging.INFO)

def parse_arguments():

    parser = argparse.ArgumentParser(description='Calculate overhead for a trace folder.')

    parser.add_argument('dir',
                        metavar='<traces path>',
                        help='Path to the directory with the traffic traces to be simulated.')

    parser.add_argument('-format',
                        metavar='<format>',
                        default = '.merge',
                        help='file format, default: "xx.merge" ')

    parser.add_argument('--log',
                        type=str,
                        dest="log",
                        metavar='<log path>',
                        default='stdout',
                        help='path to the log file. It will print to stdout by default.')

    args = parser.parse_args()
    config_logger(args)

    return args

def calc_single_ovhd(t):
    logger.debug('Processing file {}'.format(t))
    with open(t,'r') as f:
        trace = pd.Series(f.readlines()).str.slice(0,-1)
        trace = trace.str.split('\t',expand = True)
        size = trace[1].astype('float')
    RPOV = size.where(abs(size) == 888).count()
    MPOV = size.where(abs(size) == 999).count()
    TOTAL = size.count() - RPOV - MPOV
    return (RPOV, MPOV, TOTAL)
def parallel(flist, n_jobs = 25):
    pool = mp.Pool(n_jobs)
    ovhds  = pool.map(calc_single_ovhd, flist)    
    return ovhds

if __name__ == '__main__':
    args = parse_arguments()
    if not os.path.isdir(args.dir):
        logger.error('Trace directory not found: %s', args.dir)
        sys.exit(1)

    flist = glob.glob(os.path.join(args.dir, '*' + args.format))
    if not flist and args.format == '.merge':
        fallback = [f for f in glob.glob(os.path.join(args.dir, '*')) if os.path.isfile(f)]
        if fallback:
            logger.info('No files matched .merge; using all regular files in %s', args.dir)
            flist = fallback

    if not flist:
        logger.error('No trace files found in %s (pattern: %s)', args.dir, '*' + args.format)
        sys.exit(1)

    # ovhds = []
    # for f in flist:
    #     overhead = calc_single_ovhd(f)
    #     ovhds.append(overhead)
    ovhds = parallel(flist)
    ovhds = list(zip(*ovhds))
    rpovhds = np.array(ovhds[0])
    mpovhds = np.array(ovhds[1])
    total = np.array(ovhds[2])
    rpovhds = 1.0*rpovhds.sum()/total.sum()
    mpovhds = 1.0*mpovhds.sum()/total.sum()
    logger.info('total packets:           {:.4f} +- {:.4f}'.format(total.mean(), total.std()))
    logger.info('Merge Padding overhead:  {:.4f} '.format(mpovhds))
    logger.info('Random Padding overhead: {:.4f} '.format(rpovhds))
    # logger.info('total packets:           {:.4f} +- {:.4f}'.format(total.mean(), total.std()))
    # logger.info('Merge Padding overhead:  {:.4f} +- {:.4f}'.format(mpovhds.mean(), mpovhds.std()))
    # logger.info('Random Padding overhead: {:.4f} +- {:.4f}'.format(rpovhds.mean(), rpovhds.std()))
    





