import json
import os
import torch

from autocomplete.lib.metrics import Metrics, IndexedAccuracyMetrics

class PythonPerNonTerminalAccuracyMetrics(Metrics):
    def __init__(self, non_terminals_file, results_dir=None, add_unk=False, dim=2):
        super().__init__()
        print('Python SingleNonTerminalAccuracyMetrics created!')

        self.non_terminals = read_non_terminals(non_terminals_file)
        if add_unk:
            self.non_terminals.append('<unk>')

        self.non_terminals_number = len(self.non_terminals)
        self.results_dir = results_dir
        self.dim = dim

        self.accuracies = [IndexedAccuracyMetrics(label='ERROR') for _ in self.non_terminals]

    def report(self, data):
        prediction, target = data
        if self.dim is None:
            predicted = prediction
        else:
            _, predicted = torch.max(prediction, dim=self.dim)
        predicted = predicted.view(-1)
        target = target.non_terminals.view(-1)

        for cur in range(len(self.non_terminals)):
            indices = (target == cur).nonzero().squeeze()
            self.accuracies[cur].report(predicted, target, indices)

    def drop_state(self):
        for accuracy in self.accuracies:
            accuracy.drop_state()

    def save_to_file(self, result):
    if self.results_dir is not None:
        with open(os.path.join(self.results_dir, 'py_nt_acc.txt'), mode='w') as f:
            f.write(json.dumps(result))

    def get_current_value(self, should_print=False):
        result = []
        for cur in range(len(self.non_terminals)):
            cur_hits = self.accuracies[cur].metrics.hits
            cur_misses = self.accuracies[cur].metrics.misses
            result.append({
                'type': self.non_terminals[cur],
                'hits': cur_hits,
                'misses': cur_misses
            })

            if should_print:
                accuracy = 0
                if cur_hits + cur_misses != 0:
                    accuracy = cur_hits / (cur_hits + cur_misses)

                print('Accuracy on {} is {}'.format(self.non_terminals[cur], accuracy))

        self.save_to_file(result)
        return 0 
