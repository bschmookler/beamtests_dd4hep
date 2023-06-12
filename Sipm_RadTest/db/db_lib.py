#!/usr/bin/env python3
import os
import sqlite3
import pandas as pd

debug = False
# debug = True

g_db = 'beamtest.db'
g_table = 'SiPM_test'
g_tables = ['irradiation', 'SiPM_test']
g_fields = {
    'SiPM_test': ('test_id', 'SiPM_id', 'test_type', 'source', 'begin_time', 'end_time', 'annealing', 'filename'),
    'irradiation': ('SiPM_id', 'tray', 'row', 'col', 'begin_time', 'end_time', 'flux'),
    }
max_width = {
    'test_id': 7, 
    'SiPM_id': 7, 
    'test_type': 10, 
    'source': 6, 
    'begin_time': 20, 
    'end_time': 20, 
    'annealing': 10, 
    'filename': 20,
    'tray': 4,
    'row': 3,
    'col': 3,
    'flux': 4,
    'tables': 20,
    }
test_type = ['threshold', 'IV', 'waveform']
source = ['dark', 'led', 'cosmic']


def check_table(table):
    if table in g_tables:
        return True
    print(f'''ERROR\tunknown table '{table}'. Known g_tables: {g_tables}''')
    return False

def check_field(table, field):
    if check_table(table):
        if field in g_fields[table]:
            return True
        print(f'''ERROR\tunknown field '{field}' in table '{table}'. Allowed g_fields in {table}: {g_fields[table]}''')
    return False

def check_value(field, value):
    if 'SiPM_id' == field:
        if 1 <= value and value <= 45:
            return True
        else:
            print(f'ERROR\tInvalid SiPM id value: {value}. Allowed range [1, 45]')
    elif 'test_type' == field:
        if value in test_type:
            return True
        else:
            print(f'ERROR\tInvalid test_type: {value}. Allowed values {test_type}')
    elif 'source' == field:
        if value in source:
            return True
        else:
            print(f'ERROR\tInvalid source value: {value}. Allowed values {source}')
    elif 'tray' == field:
        if 1 <= value and value <= 3:
            return True
        else:
            print(f'ERROR\tInvalid tray number: {value}. Allowed range [1, 3]')
    elif 'row' == field:
        if 1 <= value and value <= 5:
            return True
        else:
            print(f'ERROR\tInvalid row number: {value}. Allowed range [1, 5]')
    elif 'col' == field:
        if 1 <= value and value <= 3:
            return True
        else:
            print(f'ERROR\tInvalid col number: {value}. Allowed range [1, 3]')

    return False

''' create a database connection to a SQLite database '''
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn

''' execute the sql statement. Return a cursor object '''
def execute_sql(conn, sql, values=None):
    try:
        c = conn.cursor()
        if values:
            return c.execute(sql, values)
        else:
            return c.execute(sql)
    except sqlite3.Error as e:
        print(e)
        return None

''' query table existance in the db '''
def query_table(conn, table):
    sql = f'''SELECT name FROM sqlite_master WHERE type='table' AND name = 'f{table}';'''
    if debug:
        print(sql)
    result = execute_sql(conn, sql)
    if result.fetchone():
        return True
    else:
        return False

''' formatted output '''
def print_sep_line(fields):
    line = '+'
    for f in fields:
        width = len(f)
        if f in max_width:
            width = max_width[f]
        line += '-'*(width+2)
        line += '+'
    print(line)

def print_header(fields):
    header = '|'
    for f in fields:
        width = len(f)
        if f in max_width:
            width = max_width[f]
        header += ' {value:<{width}} '.format(value=f, width=width)
        header += '|'
    print(header)

def print_record(record):
    if not record:
        return

    row = '|'
    for f in record:
        width = len(f)
        if f in max_width:
            width = max_width[f]
        row += ' {value:<{width}} '.format(value=record[f], width=width)
        row += '|'
    print(row)

''' print query results '''
def show_query(cursor):
    if not cursor:
        return False

    fields = [des[0] for des in cursor.description]

    print_sep_line(fields)
    print_header(fields)
    print_sep_line(fields)
    for row in cursor.fetchall():
        print_record(dict(zip(fields, row)))
        print_sep_line(fields)

''' show all tables in the db '''
def show_tables(conn):
    sql = f'''SELECT name AS tables FROM sqlite_master WHERE type='table';'''
    if debug:
        print(sql)
    result = execute_sql(conn, sql)
    show_query(result)

''' drop a table '''
def drop_table(conn, table):
    if not query_table(conn, table):
        print(f'''table '{table}' doesn't exist''')
        return False
    yesno = input(f'''are you sure you want to drop table '{table}': y[es], n[o]\n''')
    if 'y' == yesno:
        yesno2 = input(f'''confirm dropping table '{table}': y[es], n[o]\n''')
        if 'y' == yesno2:
            sql = f'''DROP TABLE IF EXISTS {table};'''
            if debug:
                print(sql)
            if execute_sql(conn, sql):
                conn.commit()
                return True
        else:
            print('cancel dropping')
            return False
    else:
        print('cancel dropping')
        return False

''' table specific '''
''' create a new table '''
def create_table(conn, table):
    if not check_table(table):
        return False
    if query_table(conn, table):
        print(f'''table '{table}' already exists, will not create it''')
        return False

    sql = ''
    if 'irradiation' == table:
        sql = f''' CREATE TABLE IF NOT EXISTS {table} (
                    SiPM_id integer PRIMARY KEY,
                    tray integer,
                    row integer,
                    col integer,
                    begin_time text,
                    end_time text,
                    flux double
                );'''
    elif 'SiPM_test' == table:
        sql = f''' CREATE TABLE IF NOT EXISTS {table} (
                    test_id integer PRIMARY KEY,
                    SiPM_id integer NOT NULL,
                    test_type text,
                    source text,
                    begin_time text,
                    end_time text,
                    annealing text,
                    filename text
                ); '''

    if debug:
        print(sql)
    if not execute_sql(conn, sql):
        return False
    conn.commit()
    return True

''' query data in the table: return all records as a list'''
def query_records(conn, table, conditions='1=1', col="*"):
    sql = f'''SELECT {col} FROM {table} WHERE {conditions};'''
    if debug:
        print(sql)
    return execute_sql(conn, sql)

def insert_record(conn, table, record):
    if 'irradiation' == table:
        if 'SiPM_id' not in record:
            print(f'''WARNING\tno SiPM_id in the following record, will skip it''')
            print_record(table, record)
            return False
        elif query_records(conn, table, 'SiPM_id', record['SiPM_id']):
            print(f'''WARNING\trecord for SiPM_id={record['SiPM_id']} already exist, will skip it''')
            print_record(table, record)
            return False
    elif 'SiPM_test' == table:
        if 'test_id' in record and query_records(conn, table, 'test_id', record['test_id']):
            print(f'''WARNING\trecord for test_id={record['test_id']} already exist, will skip it''')
            print_record(table, record)
            return False

    result = True
    for f in ('SiPM_id', 'test_type', 'source', 'tray', 'row', 'col'):
        if f in record:
            result &= check_value(f, record[f])
    if not result:
        print(f'ERROR\tinvalid value in the following record, will not insert it')
        print(record, table)
        return False

    columns = ', '.join(record.keys())
    placeholders = ':' + ', :'.join(record.keys())
    sql = f'''INSERT INTO {table}({columns}) VALUES({placeholders});'''
    if debug:
        print(sql)
    execute_sql(conn, sql, record)
    conn.commit()

    return True

''' insert records from a csv file to a table '''
def insert_records(conn, table, filename):
    if not os.path.exists(filename):
        print(f'ERROR\tfile does not exist: {filename}')
        return False
    for i, row in pd.read_csv(filename).iterrows():
        if not insert_record(conn, table, row):
            return False

''' update a record in the table '''
def update_record(conn, table, kvalue, field, value):
    ''' can one update a primary key ??? '''
    key = 'test_id'
    if 'irradiation' == table:
        key = 'SiPM_id'
    sql = f'''UPDATE {table} SET {field} = {value} WHERE {key} = {kvalue};'''
    if debug:
        print(sql)
    if execute_sql(conn, sql):
        conn.commit()
        return True

''' delete a record in a table using primary key values '''
def delete_record(conn, table, kvalue):
    key = 'test_id'
    if 'irradiation' == table:
        key = 'SiPM_test'
    conditions = f'{keyg} = {kvalue}'
    result = query_records(conn, table, conditions)
    if not result:
        print('WARNING\tindicated record does not exist in table {table}')
        return False
    show_query(result)
    yesno = input(f'''are you sure you want to delete above record in table '{table}': y[es], n[o]\n''')
    if 'y' == yesno:
        yesno2 = input(f'confirm deleting record ({key} = {kvalue}) in table {table}: y[es], n[o]\n')
        if 'y' == yesno2:
            sql = f'DELETE FROM {table} WHERE {key} = {kvalue};'
            if debug:
                print(sql)
            if execute_sql(conn, sql):
                print('INFO\tsuccessfully delete the record')
                conn.commit()
                return True
        else:
            print('cancel deletion')
            return False
    else:
        print('cancel deletion')
        return False

''' insert records to a table '''
def insert_to_table(conn, table):
    mode = int(input('please select the insert mode: 1 [csv file], 2 [manual input]\n'))
    if 1 == mode:
        filename = input('please input the file path: ')
        if not insert_records(conn, table, filename):
            return False
    elif 2 == mode:
        print(f'''please input the following g_fields for table '{table}':''')
        values = {}
        if 'irradiation' == table:
            values['SiPM_id'] = int(input('SiPM id [1-45]: '))
            values['tray'] = int(input('tray [1-3]: '))
            values['row'] = int(input('row [1-5]: '))
            values['col'] = int(input('col [1-3]: '))
            values['begin_time'] = input('begin_time: ').strip()
            values['end_time'] = input('end_time: ').strip()
            values['flux'] = input('flux')
        elif 'SiPM_test' == table:
            values['SiPM_id'] = int(input('SiPM id [1-45]: '))
            values['test_type'] = input(f'test type {[i for i in test_type]}: ')
            values['source'] = input(f'source {[i for i in source]}: ')
            values['begin_time'] = input('begin_time: ').strip()
            values['end_time'] = input('end_time: ').strip()
            values['annealing'] = input('annealing: ')
            values['filename'] = input('filename: ')
        if not insert_record(conn, values, table):
            return False
    else:
        print(f'ERROR\tunrecognised mode {mode}')
        return False
    return True

''' update a record in the table '''
def update(conn, table):
    key = 'test_id'
    if 'irradiation' == table:
        key = 'SiPM_id'
    kvalue = int(input(f'select the record [{key}] that you want to update: '))
    conditions = f'{key} = {kvalue}'
    result = query_records(conn, table, conditions)
    if not result.fetchone():
        print(f'''ERROR\tindicated record ({key} = {kvalue}) does not exist in table '{table}' ''')
        return False

    print('record before updating:')
    show_query(result)

    field_prompt = f'1[{g_fields[table][1]}]'
    for i in range(2, len(g_fields[table])):
        field_prompt += f', {i}[{g_fields[table][i]}]'
    index = int(input(f'which field you want to update: {field_prompt}: '))
    if index < 1 or index >= len(g_fields[table]):
        print(f'ERROR\tinvalid index {index}')
        return False
    field = g_fields[table][index]
    value = input(f'''updated value for {field}: ''')
    update_record(conn, table, kvalue, field, value)

    print('record after updating:')
    show_query(query_records(conn, table, conditions))

def export_records(conn, table):
    out_name = input('what is the output file name: ')
    if os.path.exists(out_name):
        print('ERROR\t{out_name} already exists, please backup it')
        return False
    db_df = pd.read_sql_query(f'SELECT * from {table};', conn)
    db_df.to_csv(out_name, index=False)

if __name__ == '__main__':
    conn = create_connection(g_db)
    if not conn:
        print('Error! cannot create the database connection.')
        exit()

    ''' command loop '''
    command = None
    while command != 'q':
        line = input('c[reate table], S[how all g_tables], s[how], i[nsert], u[pdate], e[xport to cvs], d[elete record], D[elete table], q[uit]\n').strip()
        val = line.split()
        command = val[0]
        table = g_table
        if (len(val) > 1):
            table = val[1].strip()
        if table not in g_tables:
            print(f'''ERROR\tunknown table '{table}'. Known g_tables [{g_tables}]''')
            continue

        if command == 'c':
            table = input(f'please input the table name [{g_tables}]: ').strip()
            create_table(conn, table)
        elif command == 'S':
            show_tables(conn)
        elif command == 's':
            show_query(query_records(conn, table))
        elif command == 'i':
            insert_to_table(conn, table)
        elif command == 'u':
            update(conn, table)
        elif command == 'e':
            export_records(conn, table)
        elif command == 'd':
            delete_record(conn, table)
        elif command == 'D':
            drop_table(conn, table)

    conn.close()
