from typing import List

import torch
import torch.nn.functional as F


class GDLoss:
    def __init__(self, multiplier, label=''):
        self.multiplier = multiplier
        self.label = label

    def run(self, results_dict):
        raise NotImplementedError


class GDPortfolio:
    def __init__(self, cov, exp, losses: List[GDLoss]):
        # expect cov, exp are pandas df/series
        self.cov = torch.from_numpy(cov.to_numpy())
        self.exp = torch.from_numpy(exp.to_numpy())
        self.losses = losses

        # starting allocations. We need to softmax in order to do this
        self.props = torch.zeros_like(self.exp)
        self.props.requires_grad = True

    def get_allocations(self):
        with torch.no_grad():
            proportions = F.softmax(self.props, dim=0)
            return proportions

    def gd_portfolio(self, epochs=1000, lr=1):
        opt = torch.optim.SGD([self.props], lr=lr)
        for _ in range(epochs):
            opt.zero_grad()
            results = self.run_with_start()
            loss = self.process_losses(results)
            loss.backward()
            opt.step()

    def process_losses(self, results):
        loss = None
        for l in self.losses:
            if loss is None:
                loss = l.run(results)  # make sure it's a torch tensor, not an int
            else:
                loss += l.run(results)
        return loss

    def run(self, proportions):
        """
        :param proportions: assumes shape is n_stocks, 1
        :return:
        """
        if len(proportions.shape) == 1:
            proportions = proportions.unsqueeze(1)
        prop_matrix = proportions @ proportions.transpose(0, 1)
        cov_matrix = self.cov * prop_matrix
        expected_vals = proportions.transpose(0, 1) @ self.exp
        return {'proportions': proportions,
                'cov_matrix': cov_matrix,
                'expected_vals': expected_vals}

    def run_with_start(self):
        proportions = F.softmax(self.props, dim=0)
        return self.run(proportions)


class ExpLoss(GDLoss):
    """
    Penalizes smaller expected value
    """

    def run(self, results_dict):
        return self.multiplier * (-results_dict['expected_vals'].sum())


class VarLoss(GDLoss):
    """
    Penalizes larger variance
    """

    def run(self, results_dict):
        return self.multiplier * results_dict['cov_matrix'].sum()


class L2ExpLoss(GDLoss):
    """
    L2 norm of target_exp - exp
    """

    def __init__(self, multiplier, target_exp, label=''):
        super().__init__(multiplier, label=label)
        self.target_exp = target_exp

    def run(self, results_dict):
        exp = results_dict['expected_vals'].sum()
        return self.multiplier * torch.square(self.target_exp - exp)


class GroupLoss(GDLoss):
    def __init__(self, multiplier, indices, target, both_dirs, label=''):
        super().__init__(multiplier, label=label)
        self.indices = indices
        self.target = target
        self.both_dirs = both_dirs

    def run(self, results_dict):
        r = results_dict['proportions'][self.indices, ...]
        prop = r.sum()
        if not self.both_dirs:
            return torch.nn.functional.relu(prop - self.target)
        else:
            return torch.abs(prop - self.target)
