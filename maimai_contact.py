import requests
import time
import maimai_model as mm_model
import maimai_login as mm_login
import maimai_detail as mm_detail
from logbook import Logger, FileHandler

# 日志
logfile = 'logs/maimai/{0}.log'.format(
    time.strftime("%Y_%m_%d", time.localtime()))
FileHandler(logfile).push_application()
log = Logger('maimai_contact')

s = requests.Session()
login_id = 0


def crawl_contact(total, start=0):
    """
    爬取联系人
    :param total:
    :param start:
    :return:
    """
    contact_list_url = 'https://maimai.cn/contact/inapp_dist1_list'
    contact_list_param = dict(jsononly=1)
    for contact_list_param['start'] in range(start, total, 15):
        # 提取好友列表
        clr = s.get(contact_list_url, params=contact_list_param)
        if parse_contact(clr.json()):
            break


def crawl_search(keyword):
    search_url = 'https://maimai.cn/web/search_center'
    params = dict(type='contact',
                  query=keyword,
                  jsononly=1)
    sr = s.get(search_url, params=params)
    # print(sr.json())
    result = set()
    if 'contacts' in sr.json()['data']:
        for contact in sr.json()['data']['contacts']:
            if 'uid' in contact:
                result.add(contact['uid'])
                # print(contact['uid'])
    parse_contact(sr.json())
    return result


def parse_contact(contact_json):
    if 'data' not in contact_json:
        log.warn('一次爬取人数超过限制')
        log.warn(contact_json)
        return False
    if 'contacts' in contact_json['data']:
        for contact in contact_json['data']['contacts']:
            if 'contact' in contact:
                contact = contact['contact']
                contact['id'] = contact['mmid']
            basic = dict(mm=contact['id'],
                         name=contact['name'],
                         last_company=contact['company'],
                         last_position=contact['position'],
                         dist=contact['dist'],
                         status=0,
                         login=login_id)
            mm_model.init_basic(basic)
        return True
    else:
        return False

if __name__ == '__main__':
    search_keywords = ['点评 数据开发', '点评 hadoop', '美团 数据开发', '美团 hadoop']
    log.info('查询：' + ','.join(search_keywords))
    search_result = set()
    for mm_login.account in mm_model.get_accounts(
            condition=mm_model.SjUser.status > 0):
        mm_login.s = requests.Session()
        login_id = mm_login.login()
        s = mm_login.s
        for search_kw in search_keywords:
            search_result = search_result | crawl_search(search_kw)
        print(search_result)
        log.info(search_result)

        for maimai_basic in mm_model.SjBasic.select().where(
                        (mm_model.SjBasic.mm << search_result) &
                        (mm_model.SjBasic.status == 0)).order_by(mm_model.SjBasic.login):
            account = mm_model.get_accounts(int(maimai_basic.login))
            if account.mm != mm_login.account.mm:
                time.sleep(10)
                mm_login.account = account
                mm_login.s = requests.Session()
                mm_login.login()
            mm_detail.s = mm_login.s
            mm_detail.crawl_detail(maimai_basic.mm)
            time.sleep(1)
