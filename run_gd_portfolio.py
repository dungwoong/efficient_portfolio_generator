import os
import json
import argparse

from pipeline.base_classes import SequentialModule
import pipeline.data_setup as ds
import pipeline.visualization as vis
import pipeline.process_gd_args as pgd
import pipeline.gd_stats as gds


def main(config_file, verbose):
    with open(config_file) as f:
        cfg = json.load(f)

    tickers = cfg['tickers']
    if isinstance(tickers, dict):
        tickers = list(tickers.keys())
    fixed_rates = [(d['label'], d['rate'], d['months']) for d in cfg['fixed_rates']]
    gd_cfg = cfg['gd_cfg']
    output_path = cfg['output_path']

    s = SequentialModule([
        ds.DownloadTickerHistorical('df', 'tickers', tickers, period='5y', interval='1mo'),
        ds.AddFixedRates('df', fixed_rates),
        ds.GetCovExpected('df', 'cov', 'exp', ticker_key='tickers_list'),
        vis.CreateOutputFolder(os.path.join(output_path, 'results'), 'output_path'),
        vis.CreateOutputFolder(os.path.join(output_path, 'eda'), 'output_path_eda'),
        vis.ExpCovPlots('exp', 'cov', 'output_path_eda'),
    ])
    state = dict()
    s.run(state, verbose=verbose)

    with open(os.path.join(output_path, 'config.json'), 'w') as f:
        json.dump(cfg, f, ensure_ascii=True, indent=4)

    # run the GD
    gd_pipe = SequentialModule([
        pgd.CreateGDModule(
            cfg=gd_cfg,
            exp_key='exp',
            cov_key='cov',
            gd_key='gdportfolio',
            losses_key='losses',
            tickers_key='tickers_list',
        ),
        pgd.RunGDModule('gdportfolio', 'losses', 'gdportfolio_results', 'tickers_list'),
        gds.GDVis('gdportfolio_results', 'output_path', 'df'),
        gds.ResultsToJson('output_path', 'gdportfolio_results'),
    ])
    gd_pipe.run(state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Gradient Descent Efficient Portfolio',
        description='Calculates an efficient portfolio with constraints given by the user, '
                    'visualizes statistics of the portfolio',
    )

    parser.add_argument('--config_file', type=str,
                        help='Path to a config file', required=True)
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    main(args.config_file, args.verbose)
