from maimai import login, model, contact, detail
import yplog
import requests
import time
import sys

log = yplog.YPLogger('spider')


def check_account(status=1):
    log.info('开始账户检测！')
    if type(status) == dict:
        accounts = model.SjUser.select().where(
            model.SjUser.status << status)
    else:
        accounts = model.SjUser.select().where(
            model.SjUser.status == status)
    for account in accounts:
        login.s = requests.Session()
        login.check_login(account)
        time.sleep(4)
    log.info('账户检测完毕！')


def crawl_dist1():
    log.info('开始爬取正常用户的好友列表！')
    # 一次获取最高好友数
    max_once = 3000
    try:
        list_start = (int(sys.argv[2]) - 1) * max_once
    except IndexError:
        list_start = 0
    # 获取某个账户或所有正常账户
    try:
        accounts = model.get_accounts(
            condition=model.SjUser.username == sys.argv[3])
    except IndexError:
        accounts = model.get_accounts(condition=model.SjUser.status == 1)
    for account in accounts:
        cn = account.resume_count
        if list_start >= cn:
            continue
        login.s = requests.Session()
        login_id = login.login(account)
        if login_id > 0:
            log.info(account.username + '的好友爬取开始！')
            contact.s = login.s
            contact.login_id = login_id
            if list_start + max_once < cn:
                contact.crawl_contact(max_once, list_start)
            else:
                contact.crawl_contact(cn, list_start)
            log.info(account.username + '的好友爬取结束！')
        time.sleep(10)
    log.info('好友列表爬取完毕！')


def crawl_detail():
    log.info('开始使用正常用户爬取好友详情！')
    # 一次爬取100个，以防账号被封
    for account in model.get_accounts(condition=model.SjUser.status == 1):
        login_id = account.mm
        mms = model.query(model.SjBasic,
                          (model.SjBasic.login == login_id) &
                          (model.SjBasic.status == 0) &
                          (model.SjBasic.dist == 1))
        if mms is not None:
            login.s = requests.Session()
            login_id = login.login(account)
            if login_id > 0:
                detail.s = login.s
                for mm in mms:
                    detail.crawl_detail(mm.mm)
                    time.sleep(1)
        # time.sleep(10)
    log.info('好友详情抓取完毕！')


if __name__ == '__main__':

    if 'check' in sys.argv:
        check_account()

    if 'dist1' in sys.argv:
        crawl_dist1()

    crawl_detail()
