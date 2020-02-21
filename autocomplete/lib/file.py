from __future__ import unicode_literals, print_function, division
import os
from io import open
import torch

from autocomplete.lib.constants import ENCODING

def create_directory_if_not_exists(path):
    os.makedirs(path, exist_ok=True)

def read_lines(filename, encoding=ENCODING):
    lines = []
    with open(filename, mode='r', encoding=encoding) as f:
        for l in f:
            if l[-1] == '\n':
                lines.append(l[:-1])
            else:
                lines.append(l)
    return lines

def load_if_saved(model, path):
    if os.path.isfile(path):
        model.load_state_dict(torch.load(path))
        print('Model restored from file.')
    else:
        raise Exception('Model file not exists File: {}'.format(path))

def load_cuda_on_cpu(model, path):
    if os.path.isfile(path):
        model.load_state_dict(torch.load(path, map_location=lambda storage, loc: storage))
        print('Model restored from file.')
    else:
        raise Exception('Model file not exists. File: {}'.format(path))

def save_model(model, path):
    torch.save(model.state_dict(), path)
