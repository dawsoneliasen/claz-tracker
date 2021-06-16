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
DATE_FORMAT = '%m/%d'
TIME_FORMAT = '%H:%M'


def timesheet_path(project, month):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    timesheet_dir = os.path.join(this_dir, '..', 'timesheets', project)
    timesheet_path = os.path.join(timesheet_dir, f'{month}.csv')
    return timesheet_path
    
def load_timesheet(project, month):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    timesheet_dir = os.path.join(this_dir, '..', 'timesheets', project)
    if not os.path.isdir(timesheet_dir):
        print(f'Creating new timesheet directory timesheets/{project}.')
        os.mkdir(timesheet_dir)
    timesheet_path = os.path.join(timesheet_dir, f'{month}.csv')
    try:
        timesheet = pd.read_csv(timesheet_path)
    except FileNotFoundError:
        print(f'Timesheet not found for {month}. '
              'A new timesheet will be created.')
        timesheet = pd.DataFrame(columns=['date', 'start', 'stop'])
    return timesheet


def save_timesheet(timesheet, project, month):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    timesheet_dir = os.path.join(this_dir, '..', 'timesheets', project)
    if not os.path.isdir(timesheet_dir):
        print(f'Creating new timesheet directory timesheets/{project}.')
        os.mkdir(timesheet_dir)
    timesheet_path = os.path.join(timesheet_dir, f'{month}.csv')
    timesheet.to_csv(timesheet_path, index=False)


def new_session(timesheet, start_time):
    timesheet = timesheet.copy()
    if IN_PROGRESS_FLAG in timesheet['stop'].to_list():
        print('There is an unfinished session.')
        print('Run claz stop to end the session now '
              'or edit the timesheet to fix missed session stop.')
        sys.exit(1)
    new_row = {'date': start_time.strftime(DATE_FORMAT),
               'start': start_time.strftime(TIME_FORMAT),
               'stop': IN_PROGRESS_FLAG}
    timesheet = timesheet.append(new_row, ignore_index=True)
    return timesheet


def end_session(timesheet, stop_time):
    timesheet = timesheet.copy()
    if IN_PROGRESS_FLAG not in timesheet['stop'].to_list():
        print('There is no session in progress.')
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
    print(f'Session duration: {duration.seconds / 3600:.2f} hours.')
    return timesheet


def report(timesheet):
    if IN_PROGRESS_FLAG in timesheet['stop'].to_list():
        print('An unfinished session will be ignored.')
        print('Run claz stop to end the session now '
              'or edit the timesheet to fix missed session stop.')
        timesheet = timesheet[timesheet['stop'] != IN_PROGRESS_FLAG]
    format = '%H:%M'
    diff = (pd.to_datetime(timesheet['stop'], format=format) -
            pd.to_datetime(timesheet['start'], format=format))
    month_total = diff.sum()
    week_total = diff.iloc[-7:].sum()
    print(f'{month_total.days * 24 + month_total.seconds / 3600:.2f} '
          'hours this month.')
    print(f'{week_total.days * 24 + week_total.seconds / 3600:.2f} '
          'hours this week.')
    # TODO: describe the time split between projects this month


def edit(timesheet_path):
    os.system(f'{EDITOR} {timesheet_path}')


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
    if op == 'report':
        report(timesheet)
    if op == 'edit':
        edit(timesheet_path(project, current_month))
    # write the update timesheet
    save_timesheet(timesheet, project, current_month)
