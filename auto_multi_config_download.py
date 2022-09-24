import os
from argparse import ArgumentParser
from glob import glob
from time import sleep


def main():
    ap = ArgumentParser()
    ap.add_argument(
        "--config_dir_path", required=False, default='config/multi/001',
        help="Directory of config files."
    )
    args = vars(ap.parse_args())
    config_file_path_list = sorted(glob('{}/*.yaml'.format(args['config_dir_path'])))
    print(config_file_path_list)
    for config_file_path in config_file_path_list:
        cmd = 'python3 alexa.py --config_file_path {}'.format(config_file_path)
        os.system(cmd)
        sleep(10)


if __name__ == '__main__':
    main()
