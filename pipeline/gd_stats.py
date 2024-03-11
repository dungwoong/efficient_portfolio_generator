import os
import json

from matplotlib import pyplot as plt

from pipeline.base_classes import PipelineModule


class GDVis(PipelineModule):
    def __init__(self, gd_results_key, output_path_key, df_key):
        self.gd_results_key = gd_results_key
        self.output_path_key = output_path_key
        self.df_key = df_key

    def run(self, global_state, verbose=False):
        self.allocations_pie(global_state)
        self.final_exp_pie(global_state)
        self.final_var_pie(global_state)
        self.final_losses_pie(global_state)

    def allocations_pie(self, state):
        data = state[self.gd_results_key]['final_allocations']
        f, ax = plt.subplots()
        ax.pie(list(data.values()), labels=list(data.keys()), autopct='%1.1f%%')
        plt.title('Final Allocations')
        f.savefig(os.path.join(state[self.output_path_key], 'allocations_pie.jpg'))

    def final_exp_pie(self, state):
        data = state[self.df_key].mean()
        data['portfolio'] = state[self.gd_results_key]['final_exp']
        data = data.sort_values(ascending=False)
        idx = list(data.index).index('portfolio')
        f, ax = plt.subplots()
        bars = ax.bar(data.index, data)
        bars[idx].set_color('red')
        plt.title('Final Expected Value Comparison')
        plt.ylabel('Expected % increase per month')
        f.savefig(os.path.join(state[self.output_path_key], 'final_exp.jpg'))

    def final_var_pie(self, state):
        data = state[self.df_key].var()
        data['portfolio'] = state[self.gd_results_key]['final_var']
        data = data.sort_values(ascending=True)
        idx = list(data.index).index('portfolio')
        f, ax = plt.subplots()
        bars = ax.bar(data.index, data)
        bars[idx].set_color('red')
        plt.title('Final Variance Comparison')
        plt.ylabel('Expected % increase per month')
        f.savefig(os.path.join(state[self.output_path_key], 'final_var.jpg'))

    def final_losses_pie(self, state):
        data = state[self.gd_results_key]['final_loss_breakdown_without_multipliers']
        f, ax = plt.subplots()
        ax.bar([x for x, _ in data], [y for _, y in data])
        plt.title('Final loss breakdown(without multiplier)')
        plt.ylabel('Raw loss')
        f.savefig(os.path.join(state[self.output_path_key], 'final_losses.jpg'))


class ResultsToJson(PipelineModule):
    def __init__(self, output_path_key, gd_results_key):
        self.output_path_key = output_path_key
        self.gd_results_key = gd_results_key

    def run(self, global_state, verbose=False):
        with open(os.path.join(global_state[self.output_path_key], 'gd_results.json'), 'w') as f:
            json.dump(global_state[self.gd_results_key], f, ensure_ascii=True, indent=4)
