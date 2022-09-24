import os
import yaml
from argparse import ArgumentParser


def main():
    ap = ArgumentParser()
    ap.add_argument(
        "--config_file_path", required=False, default='config/multi/multi_example.yaml',
        help="Directory of config files."
    )
    args = vars(ap.parse_args())
    with open(args['config_file_path'], 'r') as f:
        multi_args = yaml.safe_load(f)
    os.makedirs(multi_args['save_dir_path'], exist_ok=True)
    account_list = multi_args['accounts']
    session_list = multi_args['sessions']
    for account in account_list:
        for session in session_list:
            session = session.copy()
            profile = account['profile']
            session_name = session['session_name']
            file_name = '{}-{}'.format(profile, session_name)
            session['session_name'] = '{}_{}'.format(profile, session_name)
            session.update(account)
            with open(os.path.join(multi_args['save_dir_path'], '{}.yaml'.format(file_name)), 'w') as f:
                yaml.dump(session, f)


if __name__ == '__main__':
    main()
