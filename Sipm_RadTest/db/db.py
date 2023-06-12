#!/usr/bin/env python3
import sys
import argparse

from db_lib import *

debug = False
# debug = True

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand', required=True)

    ''' insert command '''
    parser_insert = subparsers.add_parser('insert', help='Insert record from a csv file')
    parser_insert.add_argument('--file',    dest='insert_csv_file',  help='which csv file to read from')
    parser_insert.add_argument('--table',   dest='insert_table', default='SiPM_test', choices=g_tables, help='which table to operate on (default: SiPM_test)')
    parser_insert.add_argument('--test_id', dest='insert_test_id', help='unique id of each record; will be assigned by the system if not specifie')
    parser_insert.add_argument('--SiPM_id',     dest='insert_SiPM_id', required=True, help='id of the SiPM that is tested')
    parser_insert.add_argument('--test_type',   dest='insert_test_type', choices=test_type, required=True, help='type of the test')
    parser_insert.add_argument('--source',      dest='insert_source', choices=source, required=True, help='source of the beam that shine on the SiPM')
    parser_insert.add_argument('--begin_time',  dest='insert_begin_time')
    parser_insert.add_argument('--end_time',    dest='insert_end_time')
    parser_insert.add_argument('--annealing',   dest='insert_annealing')
    parser_insert.add_argument('--filename',    dest='insert_filename', required=True, help='name of the resulted data file')

    ''' query command '''
    parser_list = subparsers.add_parser('query', help='query related record')
    parser_list.add_argument('--table', dest='query_table', default='SiPM_test', choices=g_tables, help='table you want to query (default SiPM_test)')
    parser_list.add_argument('--fields', dest='query_fields', default='*', help='what you want to grep')
    parser_list.add_argument('--condition', dest='query_condition', default='1=1', help='filters')

    args = parser.parse_args()

    conn = create_connection(g_db)
    if not conn:
        print('Error! cannot create the database connection.')
        exit()

    if args.subcommand == 'insert':
        if args.insert_file:
            insert_to_table1(conn, table, args.insert_file)
        else:
            record = {}
            if args.insert_test_id:
                record['test_id'] = args.insert_test_id
            record['SiPM_id'] = args.insert_SiPM_id
            record['test_type'] = args.insert_test_type
            record['source'] = args.insert_source
            if args.insert_begin_time:
                record['begin_time'] = args.insert_begin_time
            if args.insert_end_time:
                record['begin_time'] = args.insert_end_time
            if args.insert_annealing:
                record['annealing'] = args.insert_annealing
            record['filename'] = args.insert_filename
            insert_record(conn, args.insert_table, record)
    elif args.subcommand == 'query':
        table = args.query_table
        fields = args.query_fields
        show_query(query_records(conn, table, args.query_condition, args.query_fields))

    conn.close()
        
