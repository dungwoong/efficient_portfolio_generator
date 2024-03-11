import pandas as pd

from pipeline.base_classes import PipelineModule
import pipeline.gdportfolio as gd


# assume input is a dict


TYPES_DICT = {
    'exp': gd.ExpLoss,
    'var': gd.VarLoss,
    'exp_l2': gd.L2ExpLoss,
    'group': gd.GroupLoss,
}

HELP_DICT = {
    'exp': {'help': 'Penalizes smaller expected values',
            'args': dict()},
    'var': {'help': 'Penalizes larger variance values',
            'args': dict()},
    'exp_l2': {'help': 'Places an L2 loss around a target expected value. '
                       'Thus, tries to have the portfolios EXP be close to the target',
               'args': {'target_exp': 'target expected value'}},
    'group': {'help': 'Places a loss around the proportion of the portfolio that'
                      'a group of stocks takes up.',
              'args': {'indices': 'Symbols that you want to include in the group',
                       'target': 'target proportion',
                       'both_dirs': 'If true, we penalize smaller proportions. '
                                    'If not, we only penalize larger proportions.'}}
}


def create_loss(cfg):
    assert 'type' in cfg, 'cfg needs <type> key, specifying type of loss'
    loss = TYPES_DICT[cfg['type']]
    cfg.pop('type')
    if 'multiplier' not in cfg:
        cfg['multiplier'] = 1
    return loss(**cfg)


class CreateGDModule(PipelineModule):
    def __init__(self, cfg, exp_key, cov_key, gd_key, losses_key):
        self.cfg = cfg
        self.exp_key, self.cov_key = exp_key, cov_key
        self.gd_key = gd_key
        self.losses_key = losses_key

    def run(self, global_state, verbose=False):
        # cfg['losses'] should be a list of dicts
        losses = [create_loss(l_cfg) for l_cfg in self.cfg['losses']]
        global_state[self.losses_key] = losses
        global_state[self.gd_key] = gd.GDPortfolio(global_state[self.cov_key],
                                                   global_state[self.exp_key],
                                                   losses)


class RunGDModule(PipelineModule):
    def __init__(self, gd_key, losses_key, save_results_key, tickers_key):
        self.gd_key = gd_key
        self.losses_key = losses_key
        self.save_key = save_results_key
        self.tickers_key = tickers_key  # list of tickers in same order as gd uses them

    @staticmethod
    def process_label(loss):
        return loss.label if loss.label != '' else str(type(loss))

    def run(self, global_state, verbose=False):
        global_state[self.gd_key].gd_portfolio()
        allocations = dict(pd.Series(global_state[self.gd_key].get_allocations(), index=global_state[self.tickers_key]))
        results = global_state[self.gd_key].run_with_start()
        final_loss_breakdown = [(self.process_label(loss), loss.run(results).item()) for loss in global_state[self.losses_key]]
        ret = {
            'final_allocations': allocations,
            'final_loss_breakdown': final_loss_breakdown,
            'final_exp': results['expected_vals'].sum().item(),
            'final_var': results['cov_matrix'].sum().item(),
        }
        global_state[self.save_key] = ret
