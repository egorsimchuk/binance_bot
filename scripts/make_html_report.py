from src.analysis.html_report import make_report
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('api_key', type=str, help='Key from binance profile')
    parser.add_argument('api_secret', type=str, help='Secret key from binance profile')
    args = parser.parse_args()
    make_report(args.api_key, args.api_secret)
