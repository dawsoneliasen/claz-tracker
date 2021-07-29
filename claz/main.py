"""
CLAZ
Simple time management.
"""


import argparse
import datetime as dt
import os
import sys

import pandas as pd


EDITOR = os.environ.get('EDITOR', 'vim')

IN_PROGRESS_FLAG = 'IN PROGRESS'
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M'


def print_header(msg):
    """Print a message in bold."""
    bold = '\033[1m'
    reset_bold = '\033[0m'
    print(f'{bold}{msg}{reset_bold}')


def print_okay(msg):
    """Print a message in green."""
    green = '\033[92m'
    reset_color = '\033[0m'
    print(f'{green}{msg}{reset_color}')


def print_error(msg):
    """Print a message in red."""
    red = '\033[91m'
    reset_color = '\033[0m'
    print(f'{red}{msg}{reset_color}')


def print_warning(msg):
    """Print a message in yellow."""
    yellow = '\033[93m'
    reset_color = '\033[0m'
    print(f'{yellow}{msg}{reset_color}')

def timesheet_path(project, month):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    timesheet_dir = os.path.join(this_dir, '..', 'timesheets', project)
    timesheet_path = os.path.join(timesheet_dir, f'{month}.csv')
    return timesheet_path


def load_timesheet(project, month):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    timesheet_dir = os.path.join(this_dir, '..', 'timesheets')
    if not os.path.isdir(timesheet_dir):
        prompt = f'Create new timesheet directory at {timesheet_dir}? [y/n] '
        response = input(prompt)
        if response == 'y':
            os.mkdir(timesheet_dir)
        else:
            sys.exit(1)
    project_timesheet_dir = os.path.join(timesheet_dir, project)
    if not os.path.isdir(project_timesheet_dir):
        prompt = ('Create new project timesheet directory at '
                  f'{project_timesheet_dir}? [y/n] ')
        response = input(prompt)
        if response == 'y':
            os.mkdir(project_timesheet_dir)
        else:
            sys.exit(1)
    timesheet_path = os.path.join(project_timesheet_dir, f'{month}.csv')
    try:
        timesheet = pd.read_csv(timesheet_path)
    except FileNotFoundError:
        prompt = (f'Timesheet not found for {month}. '
                  'Create new timesheet? [y/n] ')
        response = input(prompt)
        if response == 'y':
            timesheet = pd.DataFrame(columns=['date', 'start', 'stop'])
        else:
            sys.exit(1)
    return timesheet


def save_timesheet(timesheet, project, month):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    timesheet_dir = os.path.join(this_dir, '..', 'timesheets', project)
    if not os.path.isdir(timesheet_dir):
        prompt = f'Create new timesheet directory timesheets/{project}? [y/n] '
        response = input(prompt)
        if response == 'y':
            os.mkdir(timesheet_dir)
        else:
            sys.exit(1)
    timesheet_path = os.path.join(timesheet_dir, f'{month}.csv')
    timesheet.to_csv(timesheet_path, index=False)


def new_session(timesheet, start_time):
    timesheet = timesheet.copy()
    if IN_PROGRESS_FLAG in timesheet['stop'].to_list():
        msg = ('There is an unfinished session.\n'
               'Run claz stop to end the session now '
               'or edit the timesheet to fix missed session stop.')
        print_error(msg)
        sys.exit(1)
    new_row = {'date': start_time.strftime(DATE_FORMAT),
               'start': start_time.strftime(TIME_FORMAT),
               'stop': IN_PROGRESS_FLAG}
    timesheet = timesheet.append(new_row, ignore_index=True)
    return timesheet


def end_session(timesheet, stop_time):
    timesheet = timesheet.copy()
    if IN_PROGRESS_FLAG not in timesheet['stop'].to_list():
        print_error('There is no session in progress.')
        sys.exit(1)
    in_progress_row = (timesheet['stop'] == IN_PROGRESS_FLAG)
    timesheet.loc[in_progress_row, 'stop'] = stop_time.strftime(TIME_FORMAT)
    session_stop = dt.datetime.strptime(
        timesheet.loc[in_progress_row, 'stop'].iloc[0],
        TIME_FORMAT
    )
    session_start = dt.datetime.strptime(
        timesheet.loc[in_progress_row, 'start'].iloc[0],
        TIME_FORMAT
    )
    duration = session_stop - session_start
    print_okay(f'Session duration: {duration.seconds / 3600:.2f} hours.')
    return timesheet


def report(project, timesheet):
    print_header(project)
    if IN_PROGRESS_FLAG in timesheet['stop'].to_list():
        msg = ('An unfinished session will be ignored.\n'
               'Run claz stop to end the session now '
               'or edit the timesheet to fix missed session stop.')
        print_warning(msg)
        timesheet = timesheet[timesheet['stop'] != IN_PROGRESS_FLAG]
    diff = timesheet.copy()
    diff['date'] = pd.to_datetime(timesheet['date'], format=DATE_FORMAT)
    diff = diff.set_index('date')
    diff = (pd.to_datetime(diff['stop'], format=TIME_FORMAT) -
            pd.to_datetime(diff['start'], format=TIME_FORMAT))
    daily = diff.groupby(pd.Grouper(freq='D')).sum()
    weekly = diff.groupby(pd.Grouper(freq='7D')).sum()
    month_total = daily.sum()
    oneweekago = dt.date.today() - dt.timedelta(days=7)
    week_total = daily.loc[oneweekago:dt.date.today()].sum()
    print(f'{month_total.days * 24 + month_total.seconds / 3600:.2f} '
          'hours this month.')
    print(f'{(week_total.days * 24) + (week_total.seconds / 3600):.2f} '
          'hours this week.')
    # TODO: describe the time split between projects this month


def edit(timesheet_path):
    return os.system(f'{EDITOR} {timesheet_path}')


def main():
    # get current date and time
    now = dt.datetime.now()
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('operation')
    parser.add_argument('project')
    args = parser.parse_args()
    op = args.operation
    project = args.project
    if op not in ['start', 'stop', 'report', 'edit']:
        msg = 'Specify either "start", "stop", "report" or "edit"'
        raise argparse.ArgumentError(msg)
    # get current year and month as a string
    current_month = now.strftime('%y-%m').lower()
    # open timesheet file
    timesheet = load_timesheet(project, current_month)
    # perform operation
    if op == 'start':
        timesheet = new_session(timesheet, now)
    if op == 'stop':
        timesheet = end_session(timesheet, now)
        report(project, timesheet)
    if op == 'report':
        report(project, timesheet)
    if op == 'edit':
        exit_code = edit(timesheet_path(project, current_month))
        sys.exit(exit_code)
    # write the update timesheet
    save_timesheet(timesheet, project, current_month)
