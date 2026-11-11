"""Calendar, join and holdout contracts; no original data needed."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stderr
import io
import pandas as pd
from replay.housing import calendar_future, reconcile_inventory, purged_split


class HousingReplayTests(unittest.TestCase):
    def test_cli_rejects_output_alias_of_any_source_before_reading(self):
        from replay.housing import main
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'private.csv'
            dates = pd.date_range('2000-01-31', '2025-03-31', freq='ME')
            frame = pd.DataFrame([{'RegionID': '1', **{d.strftime('%Y-%m-%d'): 100 + i for i, d in enumerate(dates)}}])
            frame.to_csv(source, index=False)
            before = source.read_bytes()
            alias = Path(folder) / 'report.json'
            alias.symlink_to(source)
            args = ['housing', '--prices', str(source), '--inventory', str(source), '--sales', str(source), '--output', str(alias)]
            with patch('sys.argv', args), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    main()
            self.assertEqual(source.read_bytes(), before)

    def test_calendar_target_does_not_substitute_next_available_row(self):
        df = pd.DataFrame({'RegionID': ['1', '1', '1'],
                           'date': pd.to_datetime(['2020-01-31', '2020-03-31', '2020-04-30']),
                           'value': [10., 30., 40.]})
        out = calendar_future(df, 2)
        self.assertEqual(out.iloc[0]['future_value'], 30.)
        self.assertTrue(pd.isna(out.iloc[1]['future_value']))

    def test_future_match_is_region_specific(self):
        df = pd.DataFrame({'RegionID': ['1', '2', '1', '2'],
                           'date': pd.to_datetime(['2020-01-31', '2020-01-31', '2022-01-31', '2022-01-31']),
                           'value': [10., 100., 20., 120.]})
        out = calendar_future(df, 24)
        self.assertEqual(out.iloc[0]['future_value'], 20.)
        self.assertEqual(out.iloc[1]['future_value'], 120.)

    def test_duplicate_region_month_is_rejected(self):
        df = pd.DataFrame({'RegionID': ['1', '1'], 'date': pd.to_datetime(['2020-01-31'] * 2), 'value': [1., 2.]})
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            calendar_future(df, 24)

    def test_inventory_sales_join_uses_keys_not_row_position(self):
        inv = pd.DataFrame({'RegionID': ['1', '2', '3'], 'date': pd.to_datetime(['2020-01-31'] * 3), 'inventory': [100., 200., 300.]})
        sales = pd.DataFrame({'RegionID': ['2', '1', '4'], 'date': pd.to_datetime(['2020-01-31'] * 3), 'sales': [20., 10., 0.]})
        out = reconcile_inventory(inv, sales).set_index('RegionID')
        self.assertEqual(out.loc['1', 'inventory_sales_ratio'], 10.)
        self.assertEqual(out.loc['2', 'inventory_sales_ratio'], 10.)
        self.assertTrue(pd.isna(out.loc['3', 'inventory_sales_ratio']))
        self.assertTrue(pd.isna(out.loc['4', 'inventory_sales_ratio']))
        self.assertEqual(len(out), 4)

    def test_zero_sales_is_not_replaced_by_one(self):
        inv = pd.DataFrame({'RegionID': ['1'], 'date': pd.to_datetime(['2020-01-31']), 'inventory': [100.]})
        sales = pd.DataFrame({'RegionID': ['1'], 'date': pd.to_datetime(['2020-01-31']), 'sales': [0.]})
        out = reconcile_inventory(inv, sales)
        self.assertEqual(out.iloc[0]['comparison_state'], 'ZERO_SALES')
        self.assertTrue(pd.isna(out.iloc[0]['inventory_sales_ratio']))

    def test_nonfinite_financial_input_is_not_comparable(self):
        inv = pd.DataFrame({'RegionID': ['1'], 'date': pd.to_datetime(['2020-01-31']), 'inventory': [float('inf')]})
        sales = pd.DataFrame({'RegionID': ['1'], 'date': pd.to_datetime(['2020-01-31']), 'sales': [10.]})
        out = reconcile_inventory(inv, sales)
        self.assertEqual(out.iloc[0]['comparison_state'], 'INVALID_NONFINITE')
        self.assertTrue(pd.isna(out.iloc[0]['inventory_sales_ratio']))

    def test_calendar_lag_never_borrows_future_or_other_region(self):
        from replay.housing import _lag
        df = pd.DataFrame({'RegionID': ['1', '1', '2'],
                           'date': pd.to_datetime(['2020-01-31', '2021-01-31', '2021-01-31']),
                           'value': [10., 100., 999.]})
        lag = _lag(df, 12)
        self.assertTrue(pd.isna(lag.iloc[0]))
        self.assertEqual(lag.iloc[1], 10.)
        self.assertTrue(pd.isna(lag.iloc[2]))

    def test_train_labels_do_not_cross_test_origin(self):
        df = pd.DataFrame({'date': pd.to_datetime(['2018-01-31', '2019-01-31', '2021-01-31']),
                           'target_date': pd.to_datetime(['2020-01-31', '2021-01-31', '2023-01-31'])})
        train, test, purged = purged_split(df, '2021-01-31')
        self.assertEqual(len(train), 1)
        self.assertEqual(len(test), 1)
        self.assertEqual(purged, 1)
        self.assertLess(train['target_date'].max(), test['date'].min())

    def test_scaler_statistics_are_not_changed_by_heldout_features(self):
        from replay.housing import build_model
        train = pd.DataFrame({'log_value': [1., 2., 3.], 'return12': [.1, .2, .3], 'return24': [.2, .3, .4]})
        model = build_model(); model.fit(train, [.1, .2, .3])
        self.assertEqual(model.named_steps['scale'].mean_[0], 2.)
        held = train.iloc[:1].copy(); held['log_value'] = 1000000.
        model.predict(held)
        self.assertEqual(model.named_steps['scale'].mean_[0], 2.)


if __name__ == '__main__':
    unittest.main()
