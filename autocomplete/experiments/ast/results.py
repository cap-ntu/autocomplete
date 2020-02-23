import argparse

import torch

from autocomplete.experiments.ast.main import get_main
from autocomplete.lib.argutils import add_general_arguments, add_batching_data_args, add_optimization_args, \
    add_recurrent_core_args, add_non_terminal_args, add_terminal_args
from autocomplete.lib.log import logger
from autocomplete.lib.log import tqdm_lim
from autocomplete.lib.metrics import MaxPredictionAccuracyMetrics

parser = argparse.ArgumentParser(description='AST level neural network')
add_general_arguments(parser)
add_batching_data_args(parser)
add_optimization_args(parser)
add_recurrent_core_args(parser)
add_non_terminal_args(parser)
add_terminal_args(parser)
parser.add_argument('--terminal_embeddings_file', type=str, help='File with pretrained terminal embeddings')
parser.add_argument('--prediction', type=str, help='One of: nt2n, nt2nt, ntn2t')

def print_results(args):
    main = get_main(args)
    routine = main.validation_routine
    metrics = MaxPredictionAccuracyMetrics()
    metrics.drop_state()
    main.model.eval()

    for iter_num, iter_data in enumerate(tqdm_lim(main.data_generator.get_eval_generator(), lim=1000)):
        metrics_data = routine.run(iter_num, iter_data)
        metrics.report(metrics_data)
        metrics.get_current_value(should_print=True)

if __name__ == '__main__':
    _args = parser.parse_args()
    assert _args.title is not None
    logger.should_log = _args.log
    print_results(_args)
