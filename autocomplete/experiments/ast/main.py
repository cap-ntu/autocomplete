import argparse
import os
import torch

from autocomplete.experiments.ast.nt2n_base.main import NT2NBaseMain
from autocomplete.experiments.ast.nt2n_base_attention.main import NT2NBaseAttentionMain
from autocomplete.lib.argutils import add_general_arguments, add_batching_data_args, add_optimization_args, \
    add_recurrent_core_args, add_non_terminal_args, add_terminal_args
from autocomplete.lib.log import logger

parser = argparse.ArgumentParser(description='AST level neural network')
add_general_arguments(parser)
add_batching_data_args(parser)
add_optimization_args(parser)
add_recurrent_core_args(parser)
add_non_terminal_args(parser)
add_terminal_args(parser)

parser.add_argument('--prediction', type=str, help='nt2n')
parser.add_argument('--save_model_every', type=int, help='How often to save model', default=1)
parser.add_argument('--eval', action='store_true', help='Evaluate or train')
parser.add_argument('--eval_results_directory', type=str, help='Where to save results of evaluation')
parser.add_argument('--grid_name', type=str, help='Parameter to grid search')
# parser.add_argument("--gpu_devices", type=int, nargs='+', default=None, help="")
parser.add_argument(
    '--grid_values', nargs='+', type=int,
    help='Values for grid searching'
) 
parser.add_argument(
    '--node_depths_embedding_dim', type=int,
    help='Dimension of continuous representation of node depth'
)
parser.add_argument(
    '--nodes_depths_stat_file', type=str,
    help='File with number of times particular depth is occurred in train file'
)

# parse_args = parser.parse_args()
# gpu_devices = ','.join([str(id) for id in parse_args.gpu_devices])
os.environ["CUDA_VISIBLE_DEVICES"] = "0 1 2 3"

def get_main(args):
    if args.prediction == 'nt2n_base':
        main = NT2NBaseMain(args)
    elif args.prediction == 'nt2n_base_attention':
        main = NT2NBaseAttentionMain(args)
    else:
        raise Exception('Not supported prediction type: {}'.format(args.prediction))
    return main


def train(args):
    get_main(args).train(args)


def evaluate(args):
    if args.saved_model is None:
        print('WARNING: Running eval without saved_model.')
    get_main(args).eval(args)


def grid_search(args):
    parameter_name = args.grid_name
    parameter_values = args.grid_values

    initial_title = args.title
    initial_save_dir = args.model_save_dir

    for p in parameter_values:
        suffix = '_grid_' + parameter_name + '_' + str(p)
        args.title = initial_title + suffix
        args.model_save_dir = initial_save_dir + suffix
        if not os.path.exists(args.model_save_dir):
            os.makedirs(args.model_save_dir)

        setattr(args, parameter_name, p)

        main = get_main(args)
        main.train(args)


if __name__ == '__main__':
    print(torch.__version__)
    _args = parser.parse_args()
    assert _args.title is not None
    logger.should_log = _args.log

    if _args.grid_name is not None:
        grid_search(_args)
    elif _args.eval:
        evaluate(_args)
    else:
        train(_args)
