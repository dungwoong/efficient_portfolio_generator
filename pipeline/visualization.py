import os
import seaborn as sns
import matplotlib.pyplot as plt

from pipeline.base_classes import PipelineModule


class CreateOutputFolder(PipelineModule):
    def __init__(self, path, path_key):
        self.path_key = path_key
        self.path = path

    def run(self, global_state, verbose=False):
        if not os.path.exists(self.path):
            os.mkdir(self.path)
            if verbose:
                print(f'Made folder at {self.path}')
        if self.path_key is not None:
            global_state[self.path_key] = self.path


class ExpCovPlots(PipelineModule):
    def __init__(self, exp_key, cov_key, path_key):
        self.exp_key = exp_key
        self.cov_key = cov_key
        self.path_key = path_key

    def run(self, global_state, verbose=False):
        if verbose:
            print('Generating exp barplot and heatmap')
        self.exp_barplot(global_state)
        self.cov_heatmap(global_state)

    def exp_barplot(self, global_state):
        exp = global_state[self.exp_key]
        exp = exp.sort_values()

        f = plt.figure(figsize=(10, 5))
        plt.bar(exp.index, exp)
        plt.title('Expected %change per period')
        f.savefig(os.path.join(global_state[self.path_key], 'exp.jpg'))

    def cov_heatmap(self, global_state):
        cov = global_state[self.cov_key]
        f = plt.figure(figsize=(10, 10))
        sns.heatmap(cov)
        plt.title('Covariances of %change per period')
        f.savefig(os.path.join(global_state[self.path_key], 'cov.jpg'))
