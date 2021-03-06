#_  __
# | |/ /___ ___ _ __  ___ _ _ ®
# | ' </ -_) -_) '_ \/ -_) '_|
# |_|\_\___\___| .__/\___|_|
#              |_|
#
# Keeper Commander
# Copyright 2019 Keeper Security Inc.
# Contact: ops@keepersecurity.com
#


import argparse
import logging
import requests

from contextlib import contextmanager
from .. import api
from . import imp_exp
from ..commands.base import raise_parse_exception, suppress_exit, user_choice, Command
from .importer import Attachment as ImportAttachment


def register_commands(commands):
    commands['import'] = RecordImportCommand()
    commands['export'] = RecordExportCommand()


def register_command_info(aliases, command_info):
    for p in [import_parser, export_parser]:
        command_info[p.prog] = p.description


import_parser = argparse.ArgumentParser(prog='import', description='Import data from local file to Keeper')
import_parser.add_argument('--display-csv', '-dc', dest='display_csv', action='store_true',  help='display Keeper CSV import instructions')
import_parser.add_argument('--display-json', '-dj', dest='display_json', action='store_true',  help='display Keeper JSON import instructions')
import_parser.add_argument('--format', dest='format', choices=['json', 'csv', 'keepass'], required=True, help='file format')
import_parser.add_argument('-s', '--shared', dest='shared', action='store_true', help='import folders as Keeper shared folders')
import_parser.add_argument('-p', '--permissions', dest='permissions', action='store', help='default shared folder permissions: manage (U)sers, manage (R)ecords, can (E)dit, can (S)hare, or (A)ll, (N)one')
import_parser.add_argument('filename', type=str, help='file name')
import_parser.error = raise_parse_exception
import_parser.exit = suppress_exit


export_parser = argparse.ArgumentParser(prog='export', description='Export data from Keeper to local file')
export_parser.add_argument('--format', dest='format', choices=['json', 'csv', 'keepass'], required=True, help='file format')
export_parser.add_argument('filename', type=str, nargs='?', help='file name or console output if omitted (except keepass)')
export_parser.error = raise_parse_exception
export_parser.exit = suppress_exit


csv_instructions = '''CSV Import Instructions

File Format:
Folder,Title,Login,Password,Website Address,Notes,Custom Fields

• To specify subfolders, use backslash "\\" between folder names
• To make a shared folder specify the name or path to it in the 7th field

Example 1: Create a regular folder at the root level with 2 custom fields
My Business Stuff,Twitter,marketing@company.com,123456,https://twitter.com,These are some notes,,API Key,5555,Date Created, 2018-04-02

Example 2: Create a shared subfolder inside another folder with edit and re-share permission
Personal,Twitter,craig@gmail.com,123456,https://twitter.com,,Social Media#edit#reshare

To load the sample data:
import --format=csv sample_data/import.csv
'''

json_instructions = '''JSON Import Instructions

Example JSON import file can be found in sample_data/import.json.txt.

The JSON file supports creating records, folders and shared folders.

Within shared folders, you can also automatically assign user or team permissions.

To load the sample file into your vault, run this command:
import --format=json sample_data/import.json.txt
'''


class KeeperAttachment(ImportAttachment):
    def __init__(self, params, record_uid,):
        ImportAttachment.__init__(self)
        self.params = params
        self.record_uid = record_uid

    @contextmanager
    def open(self):
        rq = {
            'command': 'request_download',
            'file_ids': [self.file_id],
        }
        api.resolve_record_access_path(self.params, self.record_uid, path=rq)

        rs = api.communicate(self.params, rq)
        if rs['result'] == 'success':
            dl = rs['downloads'][0]
            if 'url' in dl:
                with requests.get(dl['url'], stream=True) as rq_http:
                    yield rq_http.raw


class ImporterCommand(Command):
    def execute_args(self, params, args, **kwargs):
        if args.find('--display-csv') >= 0 or args.find('-dc') >= 0:
            print(csv_instructions)
        elif args.find('--display-json') >= 0 or args.find('-dj') >= 0:
            print(json_instructions)
        else:
            Command.execute_args(self, params, args, **kwargs)


class RecordImportCommand(ImporterCommand):
    def get_parser(self):
        return import_parser

    def execute(self, params, **kwargs):
        file_format = kwargs['format'] if 'format' in kwargs else None
        filename = kwargs['filename'] if 'filename' in kwargs else None
        shared = kwargs.get('shared') or False
        manage_users = False
        manage_records = False
        can_edit = False
        can_share = False
        if file_format and filename:
            permissions = kwargs.get('permissions')
            if shared and not permissions:
                permissions = user_choice('Default shared folder permissions: manage (U)sers, manage (R)ecords, can (E)dit, can (S)hare, or (A)ll, (N)one', 'uresan', show_choice=False, multi_choice=True)
            if permissions:
                chars = set()
                chars.update([x for x in permissions.lower()])
                if 'a' in chars:
                    manage_users = True
                    manage_records = True
                    can_edit = True
                    can_share = True
                else:
                    if 'u' in chars:
                        manage_users = True
                    if 'r' in chars:
                        manage_records = True
                    if 'e' in chars:
                        can_edit = True
                    if 's' in chars:
                        can_share = True

            logging.info('Processing... please wait.')
            imp_exp._import(params, file_format, filename, shared=shared,
                            manage_users=manage_users, manage_records=manage_records,
                            can_edit=can_edit, can_share=can_share)
        else:
            logging.error('Missing argument')


class RecordExportCommand(ImporterCommand):
    def get_parser(self):
        return export_parser

    def execute(self, params, **kwargs):
        file_format = kwargs['format'] if 'format' in kwargs else None
        filename = kwargs['filename'] if 'filename' in kwargs else None
        if format:
            logging.info('Processing... please wait.')
            imp_exp.export(params, file_format, filename)
        else:
            logging.error('Missing argument')
