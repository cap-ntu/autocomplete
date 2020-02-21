import os
import torch
from abc import abstractmethod
import torch.nn as nn

from tqdm import tqdm
tqdm.monitor_interval = 0

from autocomplete.lib.metrics import Metrics
from autocomplete.lib.visualization.plotter import TensorboardPlotter, \
    TensorboardPlotterCombined
from autocomplete.lib.file import save_model
from autocomplete.lib.data import DataGenerator

LOG_EVERY = 1000


class NetworkRoutine:
    def __init__(self, network):
        self.network = network

    @abstractmethod
    def run(self, iter_num, iter_data):
        pass


def save_current_model(model, dir, name):
    if dir is not None:
        print('Saving model: {}'.format(name))
        save_model(
            model=model,
            path=os.path.join(dir, name)
        )
        print('Saved!')


class TrainEpochRunner:
    def __init__(
            self,
            network: nn.Module,
            train_routine: NetworkRoutine,
            validation_routine: NetworkRoutine,
            metrics: Metrics,
            data_generator: DataGenerator,
            schedulers=None,
            plotter='tensorboard',
            save_dir=None,
            title=None,
            report_train_every=1,
            plot_train_every=1,
            save_model_every=1
    ):
     
        self.network = network
        self.train_routine = train_routine
        self.validation_routine = validation_routine
        self.metrics = metrics
        self.data_generator = data_generator
        self.schedulers = schedulers
        self.save_dir = save_dir
        self.report_train_every = report_train_every
        self.plot_train_every = plot_train_every
        self.save_model_every = save_model_every

        self.epoch = None 
        self.it = None 

        if self.plot_train_every % self.report_train_every != 0:
            raise Exception('report_train_every should divide plot_train_every')

        if plotter == 'tensorboard':
            self.plotter = TensorboardPlotter(title=title)
        elif plotter == 'tensorboard_combined':
            self.plotter = TensorboardPlotterCombined(title=title)
        else:
            raise Exception('Unknown plotter')

    def run(self, number_of_epochs):
        self.epoch = -1
        self.it = 0

        try:
            while self.epoch < number_of_epochs:
                self.epoch += 1
                if self.schedulers is not None:
                    t = 1
                    if self.epoch > 20:
                        t = 5
                    for i in range(t):
                        for scheduler in self.schedulers:
                            scheduler.step()

                self._run_for_epoch()
                self._validate()

                for hc in self.network.health_checks():
                    hc.do_check()

                if (self.epoch + 1) % self.save_model_every == 0:
                    save_current_model(self.network, self.save_dir, name='model_epoch_{}'.format(self.epoch))
        except KeyboardInterrupt:
            print('-' * 89)
            print('Exiting from training early')
        finally:
            self.plotter.on_finish()

    def _run_for_epoch(self):
        self.metrics.train()
        self.metrics.drop_state()

        self.network.train()
        train_data = self.data_generator.get_train_generator()

        for iter_data in train_data:
            if self.it % LOG_EVERY == 0:
                print('Training... Epoch: {}, Iters: {}'.format(self.epoch, self.it))

            metrics_values = self.train_routine.run(
                iter_num=self.it,
                iter_data=iter_data
            )

            if self.it % self.plot_train_every == 0:
                self.metrics.drop_state()
                self.metrics.report(metrics_values)
                self.plotter.on_new_point(
                    label='train',
                    x=self.it,
                    y=self.metrics.get_current_value(should_print=False)
                )

            self.it += 1

    def _validate(self):
        validation_data = self.data_generator.get_validation_generator()
        self.metrics.drop_state()
        self.network.eval()

        with torch.no_grad():
            validation_it = 0
            for iter_data in validation_data:
                if validation_it % LOG_EVERY == 0:
                    print('Validating... Epoch: {} Iters: {}'.format(self.epoch, validation_it))

                metrics_values = self.validation_routine.run(
                    iter_num=self.it,
                    iter_data=iter_data
                )

                self.metrics.report(metrics_values)

                validation_it += 1

            self.plotter.on_new_point(
                label='validation',
                x=self.it,
                y=self.metrics.get_current_value(should_print=False)
            )

            print('Validation done. Epoch: {}'.format(self.epoch))
            self.metrics.get_current_value(should_print=True)
