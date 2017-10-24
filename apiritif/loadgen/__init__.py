"""
destination file format - how to work in functional (LDJSON) vs performance mode (CSV? JTL?)
logging approach - is STDOUT/STDERR enough? how to minimize files written?
how to implement hits/s control/shape?

nosetests plugin (might be part of worker)
"""

import logging
import multiprocessing
import sys
import time
from multiprocessing.pool import ThreadPool
from optparse import OptionParser

import nose

log = logging.getLogger("loadgen")


def supervisor():
    """
    apiritif-loadgen CLI utility
        spawns workers, spreads them over time
        if concurrency < CPU_count: workers=concurrency else workers=CPU_count
        distribute load among them equally +-1
        smart delay of subprocess startup to spread ramp-up gracefully (might be responsibility of worker
        overwatch workers, kill them when terminated
        probably reports through stdout log the names of report files
    """

    args, opts = parse_options()
    log.debug("%s %s", opts, args)

    worker_count = min(opts.concurrency, multiprocessing.cpu_count())
    log.info("Total workers: %s", worker_count)

    workers = multiprocessing.Pool(processes=worker_count)
    workers.map(start_worker, concurrency_slicer(worker_count, opts.concurrency, opts, args))
    workers.close()
    workers.join()


def start_worker(params):
    idx, conc, opts, worker_count, args = params
    res_file = opts.result_file_template % idx
    log.info("Adding worker: idx=%s\tconcurrency=%s\tresults=%s", idx, conc, res_file)

    threads = ThreadPool(processes=conc)
    threads.map(run_nose, ((res_file, args, opts.iterations, opts.hold_for),))
    threads.close()
    threads.join()
    cmd = [
        '--ramp-up', opts.ramp_up,
        '--steps', opts.steps,
        '--worker-index', idx,
        '--workers-total', worker_count,
    ]


def run_nose(params):
    logging.debug("Starting nose iterations: %s", params)
    report_file, files, iteration_limit, hold = params
    argv = [__file__, '-v']
    argv.extend(files)
    argv.extend(['--nocapture', '--exe', '--nologcapture'])

    if iteration_limit == 0:
        if hold > 0:
            iteration_limit = sys.maxsize
        else:
            iteration_limit = 1

    start_time = int(time.time())
    iteration = 0
    while True:
        nose.run(addplugins=[], argv=argv)
        iteration += 1
        if 0 < hold < int(time.time()) - start_time:
            break
        if iteration >= iteration_limit:
            break


def concurrency_slicer(worker_count, concurrency, opts, args):
    total_concurrency = 0
    inc = concurrency / float(worker_count)
    assert inc >= 1
    for idx in range(0, worker_count):
        progress = (idx + 1) * inc
        conc = int(round(progress - total_concurrency))
        total_concurrency += conc
        assert conc > 0
        assert total_concurrency >= 0
        log.debug("Idx: %s, concurrency: %s", idx, conc)
        yield idx, conc, opts, worker_count, args

    assert total_concurrency == concurrency
    log.debug("conc sliced")
    # sys.executable, args


def parse_options():
    parser = OptionParser()
    parser.add_option('', '--concurrency', action='store', type="int", default=1)
    parser.add_option('', '--iterations', action='store', type="int", default=sys.maxsize)
    parser.add_option('', '--ramp-up', action='store', type="int", default=0)
    parser.add_option('', '--steps', action='store', type="int", default=sys.maxsize)
    parser.add_option('', '--hold-for', action='store', type="int", default=0)
    parser.add_option('', '--result-file-template', action='store', type="str", default="result-%s.csv")  # TODO?
    parser.add_option('', '--verbose', action='store_true', default=False)
    opts, args = parser.parse_args()
    return args, opts


if __name__ == '__main__':
    # do the subprocess starter utility
    logging.basicConfig(level=logging.DEBUG)
    supervisor()
