import requests
import time
from maimai import login, model, detail
import yplog

# 日志
log = yplog.YPLogger('contact', __package__)

s = requests.Session()
login_id = 0
home_url = 'https://maimai.cn/'


def crawl_contact(total, start=0):
    """
    爬取联系人
    :param total:
    :param start:
    :return:
    """
    contact_list_url = home_url + 'contact/inapp_dist1_list'
    contact_list_param = dict(jsononly=1)
    for contact_list_param['start'] in range(start, total, 15):
        # 提取好友列表
        clr = s.get(contact_list_url, params=contact_list_param)
        if not parse_contact(clr.json()):
            break


def crawl_search(keyword):
    search_url = home_url + 'web/search_center'
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
            model.init_basic(basic)
        return True
    else:
        return False

if __name__ == '__main__':
    search_keywords = ['点评 数据开发', '点评 hadoop', '美团 数据开发', '美团 hadoop']
    log.info('查询：' + ','.join(search_keywords))
    search_result = set()
    for account in model.get_accounts(
            condition=model.SjUser.status == 1):
        login.s = requests.Session()
        login_id = login.login(account)
        if login_id > 0:
            s = login.s
            for search_kw in search_keywords:
                search_result = search_result | crawl_search(search_kw)
            log.info(search_result)

            for mm_basic in model.SjBasic.select().where(
                            (model.SjBasic.mm << search_result) &
                            (model.SjBasic.status == 0)).order_by(model.SjBasic.login):
                login_account = model.get_accounts(int(mm_basic.login))
                if account.mm != login_account.mm:
                    time.sleep(10)
                    # 切换账户
                    login.s = requests.Session()
                    login.login(account)
                detail.s = login.s
                detail.crawl_detail(mm_basic.mm)
                time.sleep(1)
        else:
            time.sleep(30)
