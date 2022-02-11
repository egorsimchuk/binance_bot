import pandas as pd
from pathlib import Path
from src.utils.utils import cast_all_to_float


def update_history(df):
    fpath = Path('long_binance_history.csv')
    if fpath.exists():
        old_df = pd.read_csv(fpath)
        cast_all_to_float(old_df)
        new_df = pd.concat([old_df, df]).drop_duplicates().reset_index(drop=True)
    else:
        new_df = df
    new_df.to_csv(fpath, index=False)
    print(f'{fpath} was updated')
    return new_df


def get_data():
    try:
        df = pd.read_csv('binance_history.txt', sep='\t')
    except FileNotFoundError:
        df = pd.read_excel('Export Trade History.xlsx')

    df = df.rename(columns={'Date(UTC)': 'date'})
    df.columns = ['_'.join(c.lower().split()) for c in df.columns]
    # df = df[df['status'] != 'Canceled']
    # df = df[~df['date'].isna()].reset_index(drop=True)
    df['coin'] = df['market'].apply(lambda x: x[:-4])
    cast_all_to_float(df)
    df = update_history(df)
    return df


def calc_report(df):
    fname = Path('means_report.csv')
    groups = df.groupby('coin')
    mean_info = pd.concat(
        [groups['amount'].sum(), groups['price'].mean(), groups['total'].sum()],
        axis=1).reset_index()
    mean_info.columns = ['coin', 'coin_amount', 'mean_price', 'usd_spent']
    mean_info['percentage'] = (mean_info['usd_spent'] / mean_info['usd_spent'].sum() * 100).round(
        1)
    print(mean_info)
    mean_info.to_csv(fname, index=False)
    print(f'report saved: {fname}')


def main():
    df = get_data()
    calc_report(df)


if __name__ == '__main__':
    main()
