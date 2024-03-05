class PipelineModule:
    def run(self, global_state, verbose=False):
        raise NotImplementedError


class SequentialModule(PipelineModule):
    def __init__(self, modules):
        self.modules = modules

    def run(self, global_state, verbose=False):
        for m in self.modules:
            m.run(global_state, verbose=verbose)