import requests
import re
import json
import time
import decrypt
import maimai_model as mmdb
import configparser
from logbook import Logger, FileHandler
import sys

# 日志
logfile = 'logs/maimai/{0}.log'.format(
    time.strftime("%Y_%m_%d", time.localtime()))
FileHandler(logfile).push_application()
log = Logger('maimai')

config = configparser.ConfigParser()
config.read('db.config')

# 当前用户账号信息
account = None
username = config['maimai']['username']
password = config['maimai']['password']
# 会话
s = requests.Session()


def check_login():
    """
    检测当前账号
    :return:
    """
    login_id = login()
    if login_id > 0:
        account.mm = login_id
        account.resume_count = count_contact(login_id)
        account.status = 1
        log.info(username + '账户可用')
    else:
        account.status = login_id
    account.save()


def login():
    """
    模拟登录
    :return: 登录成功返回当前用户的mmid，否则失败码
    """
    login_url = 'https://maimai.cn/login'
    login_data = dict(m=username, p=password, to='', pa='+86')
    lr = s.post(login_url, data=login_data)

    if lr.status_code == 200:
        login_json = json_parse(lr.text)
        if login_json is None:
            if re.search('帐号或密码不正确|账号或密码错误|账号或密码频繁出错', lr.text) is not None:
                log.warn(username + '账号或密码错误！')
                return -1
            else:
                log.warn(username + '其他登录错误！')
                log.warn(lr.url + '\n' + lr.text)
                return -2
        return login_json['data']['mycard']['id']
    else:
        log.warn(username + '被拒绝登录:' + str(lr.status_code))
        log.warn(lr.url + '\n' + lr.text)
        return -3


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
                          lambda x: x.group(0).encode()
                          .decode('unicode_escape'),
                          match.group(1))
        return json.loads(json_str)
    else:
        return


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


def crawl_contact(login_id, total, start=0):
    """
    爬取联系人
    :param total:
    :param login_id:
    :param start:
    :return:
    """
    contact_list_url = 'https://maimai.cn/contact/inapp_dist1_list'
    contact_list_param = dict(jsononly=1)
    for contact_list_param['start'] in range(start, total, 15):
        # 提取好友列表
        clr = s.get(contact_list_url, params=contact_list_param)
        if 'data' not in clr.json():
            log.warn('一次爬取人数超过限制')
            log.warn(clr.text())
            break
        if 'contacts' in clr.json()['data']:
            for contact in clr.json()['data']['contacts']:
                basic = dict(mm=contact['id'],
                             name=contact['name'],
                             last_company=contact['company'],
                             last_position=contact['position'],
                             dist=contact['dist'],
                             status=0,
                             login=login_id)
                init_basic(basic)
        else:
            break


def crawl_detail(mm_id):
    """
    爬取详情
    :param mm_id:
    :return:
    """
    json_only_param = dict(jsononly=1)
    detail_url = 'https://maimai.cn/contact/detail/%d' % mm_id
    dr = s.get(detail_url, params=json_only_param)
    if dr.status_code == 200:
        detail = dr.json()
        if 'data' in detail:
            detail = detail['data']
        else:
            print(str(mm_id) + '详情数据缺失!')
            log.warn(str(mm_id) + '详情数据缺失!')
            return False
    else:
        log.warn(str(mm_id) + '被拒绝获取详情: ' + str(dr.status_code))
        log.warn(dr.url + '\n' + dr.text)
        return False
    card = detail['card']
    uinfo = detail['uinfo']
    basic = dict(mm=mm_id,
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
    rid = update(mmdb.SjBasic, basic, mmdb.SjBasic.mm == mm_id)
    if rid > 0:
        for work_exp in uinfo['work_exp']:
            insert_work(work_exp, mm_id)
        for edu in uinfo['education']:
            insert_edu(edu, mm_id)
        print(str(mm_id) + '的详情爬取结束！')
        log.info(str(mm_id) + '的详情爬取结束！')
    else:
        log.warn(str(mm_id) + 'basic表更新失败')


def insert_work(data, mm_id):
    work_exp = dict(mm=mm_id,
                    company=data['company'],
                    position=data['position'],
                    description=data['description']
                    )
    if data['start_date'] is not None:
        work_exp['start_time'] = time.mktime(
            time.strptime(data['start_date'], '%Y-%m'))
        if data['end_date'] is None:
            work_exp['end_time'] = 2147483647
        else:
            work_exp['end_time'] = time.mktime(
                time.strptime(data['end_date'], '%Y-%m'))
    return insert(mmdb.SjCareer, work_exp)


def insert_edu(data, mm_id):
    degrees = ['专科', '本科', '硕士', '博士', '博士后', '其他']
    edu = dict(mm=mm_id,
               school=data['school'],
               degree=degrees[data['degree'] if data['degree'] < 5 else 5],
               major=data['department'],
               description=data['description']
               )
    if data['start_date'] is not None:
        edu['start_time'] = time.mktime(
            time.strptime(data['start_date'], '%Y-%m'))
        if data['end_date'] is None:
            edu['end_time'] = 2147483647
        else:
            edu['end_time'] = time.mktime(
                time.strptime(data['end_date'], '%Y-%m'))
    return insert(mmdb.SjEducation, edu)


def init_basic(basic):
    """
    将联系人列表中的简要信息保存到basic表中
    :param basic:
    :return:
    """
    if not is_exist(mmdb.SjBasic, basic['mm']):
        now = int(time.time())
        basic['create_time'] = now
        basic['update_time'] = now
        return insert(mmdb.SjBasic, basic)
    else:
        return False


def insert(table, values):
    """
    将对应的值插入到指定的表中
    :param table:
    :param values:
    :return:
    """
    return table.insert(**values).execute()


def update(table, values, condition=None):
    """
    更新
    :param table:
    :param values:
    :param condition:
    :return:
    """
    now = int(time.time())
    values['update_time'] = now
    return table.update(**values).where(condition).execute()


def is_exist(table, mm_id):
    """
    判断简要信息是否已经爬取
    :param table:
    :param mm_id:
    :return:
    """
    try:
        rid = table.get(table.mm == mm_id)
        return rid.id
    except mmdb.DoesNotExist:
        return False


def get_accounts(mm_id=0, condition=True):
    """
    获取账号
    :param mm_id:
    :param condition:
    :return:
    """
    if mm_id > 0:
        try:
            result = mmdb.SjUser.get(mmdb.SjUser.mm == mm_id)
        except mmdb.DoesNotExist:
            return
    else:
        result = mmdb.SjUser.select().where(condition)
    return result


def query(table, condition, page=1):
    pnum = 100
    try:
        return table.select().where(condition).paginate(page, pnum)
    except mmdb.DoesNotExist:
        return


if __name__ == '__main__':
    if 'check' in sys.argv:
        # 批量检测所有账户是否正常
        print('开始账户检测！')
        log.info('开始账户检测！')
        for account in mmdb.SjUser.select():
            s = requests.Session()
            username = account.maimai_account
            password = decrypt.think_decrypt(account.maimai_password, 'maimai1')
            print(username, password)
            check_login()
            time.sleep(1)
        print('账户检测完毕！')
        log.info('账户检测完毕！')

    if 'dist1' in sys.argv:
        # 爬取正常用户的好友列表
        print('开始爬取正常用户的好友列表！')
        log.info('开始爬取正常用户的好友列表！')
        # 一次获取最高好友数
        max_once = 3000
        try:
            list_start = (int(sys.argv[2])-1) * max_once
        except IndexError:
            list_start = 0
        for account in get_accounts(condition=mmdb.SjUser.status > 0):
            s = requests.Session()
            username = account.maimai_account
            password = decrypt.think_decrypt(account.maimai_password, 'maimai1')
            # print(username, password)
            cn = account.resume_count
            if list_start >= cn:
                break
            current_id = login()
            if current_id > 0:
                if list_start + max_once < cn:
                    crawl_contact(current_id, max_once, list_start)
                else:
                    crawl_contact(current_id, cn, list_start)
            time.sleep(5)
            print(username + '的好友爬取结束！')
            log.info(username + '的好友爬取结束！')
        print('好友列表爬取完毕！')
        log.info('好友列表爬取完毕！')

    if 'detail' in sys.argv:
        # 使用正常用户爬取好友详情
        print('开始使用正常用户爬取好友详情！')
        log.info('开始使用正常用户爬取好友详情！')
        for account in get_accounts(condition=mmdb.SjUser.status > 0):
            s = requests.Session()
            username = account.maimai_account
            password = decrypt.think_decrypt(account.maimai_password, 'maimai1')
            print(username, password)
            current_id = account.mm
            if current_id > 0:
                mms = query(mmdb.SjBasic,
                            (mmdb.SjBasic.login == current_id) &
                            (mmdb.SjBasic.status == 0) &
                            (mmdb.SjBasic.dist == 1))
                if mms is not None:
                    login()
                    for mm in mms:
                        crawl_detail(mm.mm)
                        time.sleep(1)
        print('好友详情抓取完毕！')
        log.info('好友详情抓取完毕！')
