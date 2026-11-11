"""Calendar-safe joins and a bounded metro-level chronological baseline."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def _unique(frame: pd.DataFrame):
    if frame.duplicated(['RegionID', 'date']).any():
        raise ValueError('duplicate region/month keys')


def calendar_future(frame: pd.DataFrame, months: int) -> pd.DataFrame:
    if months < 1:
        raise ValueError('positive calendar horizon required')
    _unique(frame)
    out = frame.copy()
    out['target_date'] = (out['date'].dt.to_period('M') + months).dt.to_timestamp('M')
    target = frame[['RegionID', 'date', 'value']].rename(columns={'date': 'target_date', 'value': 'future_value'})
    return out.merge(target, on=['RegionID', 'target_date'], how='left', validate='many_to_one', sort=False)


def reconcile_inventory(inventory: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    _unique(inventory); _unique(sales)
    out = inventory.merge(sales, on=['RegionID', 'date'], how='outer', validate='one_to_one', indicator=True)
    out['comparison_state'] = np.select(
        [out['_merge'].eq('left_only'), out['_merge'].eq('right_only'),
         out['inventory'].isna() | out['sales'].isna(),
         ~np.isfinite(out['inventory']) | ~np.isfinite(out['sales']), out['sales'].eq(0),
         out['sales'].lt(0) | out['inventory'].lt(0)],
        ['MISSING_SALES', 'MISSING_INVENTORY', 'MISSING_VALUE', 'INVALID_NONFINITE', 'ZERO_SALES', 'INVALID_NEGATIVE'],
        default='COMPARABLE')
    out['inventory_sales_ratio'] = out['inventory'].div(out['sales']).where(out['comparison_state'].eq('COMPARABLE'))
    return out.drop(columns='_merge')


def purged_split(frame: pd.DataFrame, test_start: str):
    cutoff = pd.Timestamp(test_start)
    candidate = frame['date'].lt(cutoff)
    safe = candidate & frame['target_date'].lt(cutoff)
    test = frame['date'].ge(cutoff)
    return frame.loc[safe].copy(), frame.loc[test].copy(), int((candidate & ~safe).sum())


def monthly_long(path: Path, value_name: str, region_ids=None) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={'RegionID': str})
    if 'RegionType' in frame:
        frame = frame.loc[frame['RegionType'].ne('country')]
    if region_ids is not None:
        frame = frame.loc[frame['RegionID'].isin(region_ids)]
    dates = [c for c in frame if re.fullmatch(r'\d{4}-\d{2}-\d{2}', c)]
    if not dates:
        raise ValueError('no monthly date columns')
    out = frame.melt(id_vars='RegionID', value_vars=dates, var_name='date', value_name=value_name)
    out['date'] = pd.to_datetime(out['date']).dt.to_period('M').dt.to_timestamp('M')
    out[value_name] = pd.to_numeric(out[value_name], errors='raise')
    _unique(out)
    return out


def _lag(frame: pd.DataFrame, months: int) -> pd.Series:
    lookup = frame[['RegionID', 'date', 'value']].copy()
    lookup['date'] = (lookup['date'].dt.to_period('M') + months).dt.to_timestamp('M')
    return frame[['RegionID', 'date']].merge(lookup, on=['RegionID', 'date'], how='left', validate='one_to_one')['value']


def price_metrics(actual, prediction):
    return {'rows': len(actual), 'mae_source_currency': float(np.mean(np.abs(actual-prediction))),
            'median_absolute_percentage_error': float(np.median(np.abs(actual-prediction)/actual)*100),
            'root_mean_squared_log_error': float(np.sqrt(np.mean((np.log(actual)-np.log(prediction))**2)))}


def build_model() -> Pipeline:
    return Pipeline([('scale', StandardScaler()), ('ridge', Ridge(alpha=1.0))])


def evaluate(prices_path: Path, inventory_path: Path, sales_path: Path,
             max_regions: int = 50, test_start: str = '2021-01-31') -> dict:
    if max_regions < 1:
        raise ValueError('positive region limit required')
    all_prices = monthly_long(prices_path, 'value')
    regions = sorted(all_prices['RegionID'].unique(), key=lambda x: int(x))[:max_regions]
    prices = all_prices.loc[all_prices['RegionID'].isin(regions)].reset_index(drop=True)
    positive = prices['value'].gt(0) & np.isfinite(prices['value'])
    prices = prices.loc[positive].reset_index(drop=True)
    prices['lag12'] = _lag(prices, 12).to_numpy()
    prices['lag24'] = _lag(prices, 24).to_numpy()
    features = calendar_future(prices, 24)
    features['log_value'] = np.log(features['value'])
    features['return12'] = np.log(features['value']/features['lag12'])
    features['return24'] = np.log(features['value']/features['lag24'])
    features['target_log_return'] = np.log(features['future_value']/features['value'])
    columns = ['log_value', 'return12', 'return24']
    eligible = np.isfinite(features[columns+['target_log_return']]).all(axis=1) & features['future_value'].gt(0)
    complete = features.loc[eligible].copy()
    train, test, purged = purged_split(complete, test_start)
    if len(train) < 20 or len(test) < 20:
        raise ValueError('insufficient chronological train/test rows')
    if train['target_date'].max() >= test['date'].min():
        raise AssertionError('training target reaches the test-origin period')
    model = build_model()
    model.fit(train[columns], train['target_log_return'])
    predicted = test['value'].to_numpy()*np.exp(model.predict(test[columns]))
    inv = monthly_long(inventory_path, 'inventory', regions)
    sales = monthly_long(sales_path, 'sales', regions)
    ratios = reconcile_inventory(inv, sales)
    comparable = ratios.loc[ratios['comparison_state'].eq('COMPARABLE'), 'inventory_sales_ratio']
    return {'analysis_date_local': '2026-11-10',
            'scope': 'New bounded metro-level benchmark; not a rerun of the original neighborhood XGBoost or ROI scenarios',
            'cohort': 'First region IDs in numeric order, country excluded; deterministic convenience sample',
            'regions': len(regions), 'maximum_regions': max_regions,
            'retained_price_rows': len(prices), 'eligible_rows': len(complete),
            'ineligible_feature_or_target_rows': len(features)-len(complete),
            'horizon_calendar_months': 24, 'features': columns,
            'split': {'test_start': test_start, 'train_rows': len(train), 'test_rows': len(test),
                      'purged_rows': purged, 'train_first_origin': str(train['date'].min().date()),
                      'train_last_origin': str(train['date'].max().date()),
                      'train_last_target': str(train['target_date'].max().date()),
                      'test_first_origin': str(test['date'].min().date()),
                      'test_last_origin': str(test['date'].max().date()),
                      'test_last_target': str(test['target_date'].max().date()),
                      'target_overlap': False},
            'models': {'unchanged_value_baseline': price_metrics(test['future_value'].to_numpy(), test['value'].to_numpy()),
                       'fixed_ridge': price_metrics(test['future_value'].to_numpy(), predicted)},
            'selection': 'Ridge alpha=1 fixed in advance; no test tuning. StandardScaler fit only on training rows.',
            'inventory_sales': {'unit': 'inventory divided by monthly sales count; not days',
                     'comparison_states': {str(k): int(v) for k,v in ratios['comparison_state'].value_counts().items()},
                     'comparable_median_ratio': float(comparable.median()) if len(comparable) else None},
            'input_sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest() for name,path in
                            [('metro_zhvi',prices_path), ('metro_inventory',inventory_path), ('metro_sales',sales_path)]},
            'limits': ['Historical revised snapshot, not point-in-time data vintages or real-time forecasting.',
                       'Same metros appear across time; no unseen-geography validation.',
                       'Overlapping test horizons create dependent errors; no independent confidence interval claimed.',
                       'No investment recommendation or validated ROI/income claim.'],
            'environment': {'python':platform.python_version(), **{n:importlib.metadata.version(n)
                          for n in ['numpy','pandas','scikit-learn','scipy','joblib','threadpoolctl','cloudpickle','narwhals']}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prices', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--sales', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-regions', type=int, default=50)
    parser.add_argument('--test-start', default='2021-01-31')
    args = parser.parse_args()
    if args.output.resolve() in {p.resolve() for p in [args.prices, args.inventory, args.sales]}:
        parser.error('Output must differ from every source CSV, including symlink aliases')
    result = evaluate(args.prices,args.inventory,args.sales,args.max_regions,args.test_start)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'output':str(args.output),'regions':result['regions'],'split':result['split']}))


if __name__ == '__main__':
    main()
