import requests
import re
import json
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
                          lambda x: x.group(0).encode()
                          .decode('unicode_escape'),
                          match.group(1))
        return json.loads(json_str)
    else:
        return


def login(user_account=None):
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
            if re.search('账号或密码错误', lr.text) is not None:
                print(username + '账号或密码错误！')
            else:
                print(username + '其他登录错误！')
            if user_account is not None:
                set_user_status(user_account, -1)
            return False
        if user_account is not None:
            set_user_status(user_account, 1)
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
                basic = dict(true=contact['id'],
                             name=contact['name'],
                             last_company=contact['company'],
                             last_position=contact['position'],
                             status=0,
                             login=login_id)
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
    basic = dict(true=mm_id,
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
    rid = update(mmdb.SjBasic, basic, mmdb.SjBasic.true == mm_id)
    if rid > 0:
        for work_exp in uinfo['work_exp']:
            parse_work(work_exp, rid)
        for edu in uinfo['education']:
            parse_edu(edu, rid)
    else:
        print('basic表更新失败')


def parse_work(data, rid):
    work_exp = dict(resume=rid,
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
    return insert(mmdb.SjCareer, work_exp)


def parse_edu(data, rid):
    degrees = ['专科', '本科', '硕士', '博士', '博士后', '其他']
    edu = dict(resume=rid,
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
    return insert(mmdb.SjEducation, edu)


def bulk_detail_crawl(n):
    table = mmdb.SjBasic
    basic = query(table, table.status > 0, n)
    for b in basic:
        user_account = get_accounts(b.true)
        if user_account:
            login_id = login(user_account)



def init_basic(basic):
    """
    将联系人列表中的简要信息保存到basic表中
    :param basic:
    :return:
    """
    if not is_exist(mmdb.SjBasic, basic['true']):
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
    return table.update(**values).where(condition).execute()


def is_exist(table, mm_id):
    """
    判断简要信息是否已经爬取
    :param table:
    :param mm_id:
    :return:
    """
    try:
        rid = table.get(table.true == mm_id)
        return rid.id
    except mmdb.DoesNotExist:
        return False


def get_accounts(mm_id=0):
    """
    获取账号
    :param mm_id:
    :return:
    """
    if mm_id > 0:
        try:
            result = mmdb.SjUser.get(mmdb.SjUser.mm == mm_id)
        except mmdb.DoesNotExist:
            return
    else:
        result = mmdb.SjUser.select().where(mmdb.SjUser.status >= 0)
    return result


def query(table, condition, page):
    pnum = 15
    try:
        return table.select().where(condition).paginate(page, pnum)
    except mmdb.DoesNotExist:
        return False


def set_user_status(user_account, status):
    user_account.status = status
    user_account.save()


def crawl():
    p = 1
    login_id = login()
    if login_id > 0:
        total = count_contact(login_id)
        crawl_contact(total, login_id)
        mm_ids = query(mmdb.SjBasic,
                       mmdb.SjBasic.login == login_id and
                       mmdb.SjBasic.status >= 0, p)
        for mm_id in mm_ids:
            crawl_detail(mm_id.true)


if __name__ == '__main__':
    # 爬取联系人列表
    # for account in get_accounts():
    #     username = account.maimai_account
    #     try:
    #         password = decrypt.think_decrypt(account.maimai_password, 'maimai1')
    #         print(username, password)
    #     except Exception:
    #         print("解密出错！")
    #     crawl()
    crawl()
