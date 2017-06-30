import requests
import re
import json
import database
import time
import decrypt
import maimai_model as mmdb
import configparser

config = configparser.ConfigParser()
config.read('db.config')
username = config['maimai']['username']
password = config['maimai']['password']

s = requests.Session()


def json_parse(json_str):
    """
    提取JSON.parse()中的json数据
    :param json_str:
    :return:
    """
    match = re.search('JSON\.parse\(\"(.+)\"\)', json_str, re.S)
    if match is not None:
        # 将\uxxxx格式字符串转码
        json_str = re.sub(r'\\u\w{4}', 
                          lambda x: x.group(0).encode().decode('unicode_escape'),
                          match.group(1))
        return json.loads(json_str)
    else:
        return


def login():
    """
    模拟登录
    :return: 登录者mm_id
    """
    login_url = 'https://maimai.cn/login'
    login_data = dict(m=username, p=password, to='', pa='+86')
    lr = s.post(login_url, data=login_data)

    if lr.status_code == 200:
        login_json = json_parse(lr.text)
        if login_json is None:
            print(username + '账户出错！')
            return False
        return login_json['data']['mycard']['id']
    else:
        print('被拒绝登录！')
        return False


def count_contact(login_id):
    """
    计算联系人总数
    :param login_id: 当前用户的mm_id
    :return:
    """
    detail_url = 'https://maimai.cn/contact/detail/%d' % login_id
    json_only_param = dict(jsononly=1)
    cdr = s.get(detail_url, params=json_only_param)
    return cdr.json()['data']['inapp_d1cnt']


def crawl_contact(total, login_id):
    """
    爬取联系人
    :param total:
    :param login_id:
    :return:
    """
    contact_list_url = 'https://maimai.cn/contact/inapp_dist1_list'
    contact_list_param = dict(jsononly=1)
    i = 0
    while i*15 < total:
        # 提取好友列表
        contact_list_param['start'] = i * 15
        clr = s.get(contact_list_url, params=contact_list_param)
        if 'contacts' in clr.json()['data']:
            for contact in clr.json()['data']['contacts']:
                basic = dict(true_id=contact['id'],
                             name=contact['name'],
                             last_company=contact['company'],
                             last_position=contact['position'],
                             status=0,
                             login_id=login_id)
                init_basic(basic)
            i += 1
        else:
            break
    print('爬取联系人结束！')


def crawl_detail(mm_id):
    json_only_param = dict(jsononly=1)
    detail_url = 'https://maimai.cn/contact/detail/%d' % mm_id
    dr = s.get(detail_url, params=json_only_param)
    if dr.status_code == 200:
        detail = dr.json()
        if 'data' in detail:
            detail = detail['data']
        else:
            print('详情数据缺失')
            return False
    else:
        print('被拒绝获取详情！')
        return False
    card = detail['card']
    uinfo = detail['uinfo']
    basic = dict(true_id=mm_id,
                 name=card.get('name', ''),
                 last_company=card.get('company', ''),
                 last_position=card.get('position', ''),
                 province=card.get('province', ''),
                 city=card.get('city', ''),
                 mobile=uinfo.get('mobile', ''),
                 phone=uinfo.get('phone', ''),
                 email=uinfo.get('email', ''),
                 birthday=uinfo.get('birthday', ''),
                 headline=uinfo.get('headline', ''),
                 status=1
                 )
    rid = update('sj_basic', basic)
    if rid > 0:
        for work_exp in uinfo['work_exp']:
            parse_work(work_exp, rid)
        for edu in uinfo['education']:
            parse_edu(edu, rid)
    else:
        print('basic表更新失败')


def parse_work(data, rid):
    work_exp = dict(resume_id=rid,
                    company=data['company'],
                    position=data['position'],
                    description=data['description']
                    )
    if data['start_date'] is not None:
        work_exp['start_time'] = time.mktime(time.strptime(data['start_date'], '%Y-%m'))
        if data['end_date'] is None:
            work_exp['end_time'] = 2147483647
        else:
            work_exp['end_time'] = time.mktime(time.strptime(data['end_date'], '%Y-%m'))
    return insert('sj_career', work_exp)


def parse_edu(data, rid):
    degrees = ['专科', '本科', '硕士', '博士', '博士后', '其他']
    edu = dict(resume_id=rid,
               school=data['school'],
               degree=degrees[data['degree'] if data['degree'] < 5 else 5],
               major=data['department'],
               description=data['description']
               )
    if data['start_date'] is not None:
        edu['start_time'] = time.mktime(time.strptime(data['start_date'], '%Y-%m'))
        if data['end_date'] is None:
            edu['end_time'] = 2147483647
        else:
            edu['end_time'] = time.mktime(time.strptime(data['end_date'], '%Y-%m'))
    return insert('sj_education', edu)


def init_basic(basic):
    """
    将联系人列表中的简要信息保存到basic表中
    :param basic:
    :return:
    """
    if not is_exist('sj_basic', basic['true_id']):
        now = int(time.time())
        basic['create_time'] = now
        basic['update_time'] = now
        return insert('sj_basic', basic)
    else:
        return False


def db_query(func):
    def _db_op(*args):
        conn = database.connection('maimai')
        try:
            with conn.cursor() as cursor:
                res = func(cursor, *args)
                return res
        finally:
            conn.close()
    return _db_op


def insert(table, values):
    """
    将对应的值插入到指定的表中
    :param table:
    :param values:
    :return:
    """
    conn = database.connection('maimai')
    try:
        with conn.cursor() as cursor:
            rid = database.insert(cursor, table, values)
            conn.commit()
            if rid:
                return rid
            else:
                return False
    finally:
        conn.close()


def update(table, values, condition=None):
    """
    更新
    :param table:
    :param values:
    :param condition:
    :return:
    """
    conn = database.connection('maimai')
    try:
        with conn.cursor() as cursor:
            if condition is None:
                condition = 'true_id={0}'.format(values['true_id'])
            values['update_time'] = int(time.time())
            rid = database.update(cursor, table, values, condition)
            conn.commit()
            if rid:
                return rid
            else:
                return False
    finally:
        conn.close()


@db_query
def is_exist(cursor, table, mm_id):
    """
    判断简要信息是否已经爬取
    :param cursor:
    :param table:
    :param mm_id:
    :return:
    """
    query_sql = 'select id from {0} where true_id = {1}'.format(table, mm_id)
    cursor.execute(query_sql)
    rid = cursor.fetchone()
    if rid is not None:
        return rid['id']
    else:
        return False


@db_query
def get_accounts(cursor, mm_id=0):
    """
    获取账号
    :param cursor:
    :param mm_id:
    :return:
    """
    if mm_id > 0:
        result = database.get_accounts(cursor, 'maimai', 'mm_id='+str(mm_id))
    else:
        result = database.get_accounts(cursor, 'maimai')
    return result


@db_query
def query(cursor, sql, page):
    pnum = 15
    cursor.execute(sql + ' limit {0},{1}'.format((page-1)*pnum, pnum))
    return cursor.fetchall()


def crawl():
    p = 1
    login_id = login()
    if login_id > 0:
        # total = count_contact(login_id)
        # crawl_contact(total, login_id)
        mm_ids = query("select true_id from sj_basic where " +
                       "login_id={0} and status=0".format(login_id), p)
        for mm_id in mm_ids:
            crawl_detail(mm_id['true_id'])


if __name__ == '__main__':
    # 爬取联系人列表
    # for account in get_accounts():
    #     username = account['maimai_account']
    #     try:
    #         password = decrypt.think_decrypt(account['maimai_password'], 'maimai1')
    #     except Exception:
    #         print("解密出错！")
    #     crawl()
    crawl()
