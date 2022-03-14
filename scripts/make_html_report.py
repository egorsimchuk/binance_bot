from src.analysis.html_report import make_report
import argparse
import logging
from src.utils.logging import log_format, log_level
logging.basicConfig(format=log_format, level=log_level)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('api_key', type=str, help='Key from binance profile')
    parser.add_argument('api_secret', type=str, help='Secret key from binance profile')
    parser.add_argument('open_file', type=int, nargs='?', default=1, choices=[0,1], help='Open html report after creating')
    args = parser.parse_args()
    make_report(args.api_key, args.api_secret, args.open_file)
