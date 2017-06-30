import pymysql.cursors
import configparser

config = configparser.ConfigParser()
config.read('db.config')


def connection(db):
    """
    连接数据库
    :param db:
    :return:
    """
    if db not in config:
        print("数据库名输入不正确！")
        return
    db_config = dict(config['Mysql'])
    db_config['database'] = db
    db_config['cursorclass'] = pymysql.cursors.DictCursor
    return pymysql.connect(**db_config)


def get_accounts(cursor, db, condition='1=1'):
    """
    获取账号
    :param cursor:
    :param db:
    :param condition:
    :return:
    """
    sql = config[db]['account'] + ' where ' + condition
    cursor.execute(sql)
    accounts = cursor.fetchall()
    return accounts


def get_columns(cursor, table):
    """
    获取字段名
    :param cursor:
    :param table:
    :return:
    """
    sql = 'show columns from ' + table
    cursor.execute(sql)
    columns = [row['Field'] for row in cursor.fetchall()[1:]]
    return columns


def insert_sql(table, values):
    """
    插入的语句
    :param cursor:
    :param table:
    :param values:
    :return:
    """
    columns = values.keys()
    values = ['%(' + column + ')s' for column in columns]
    return 'insert into ' + table + ' (' + ','.join(columns) + \
           ') values (' + ','.join(values) + ')'


def update_sql(table, values, condition):
    columns = values.keys()
    values = [column + '=%(' + column + ')s' for column in columns]
    return 'update ' + table + ' set ' + ','.join(values) + ' where ' + condition


def insert(cursor, table, values):
    sql = insert_sql(table, values)
    cursor.execute(sql, values)
    cursor.execute('SELECT LAST_INSERT_ID() as insert_id')
    insert_id = cursor.fetchone()['insert_id']
    return insert_id


def update(cursor, table, values, condition):
    sql = update_sql(table, values, condition)
    cursor.execute(sql, values)
    cursor.execute("select id from " + table + " where " + condition)
    update_id = cursor.fetchone()['id']
    return update_id


def test():
    db = 'maimai'
    conn = connection(db)
    try:
        with conn.cursor() as cursor:
            result = insert_sql(cursor, 'sj_basic')
            print(result)
    finally:
        conn.close()
