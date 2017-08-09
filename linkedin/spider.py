from linkedin import login, contact, model
import yplog
import requests
import time

log = yplog.YPLogger('spider', 'linkedin')


def check_account(status=1):
    # 批量检测所有账户是否正常
    log.info('开始账户检测！')
    if status is None:
        accounts = model.SjUser.select()
    elif type(status) == dict:
        accounts = model.SjUser.select().where(
            model.SjUser.status << status)
    else:
        accounts = model.SjUser.select().where(
            model.SjUser.status == status)
    for account in accounts:
        login.s = requests.session()
        login.check_login(account)
        time.sleep(4)
    log.info('账户检测完毕！')


def crawl_contact(start=1, username=''):
    """
    爬取联系人信息
    :param start:  因为一页页爬取，根据日志，判断开始页
    :param username: 指定用户名进行爬取
    :return:
    """
    log.info('开始爬取联系人！')
    if not username:
        max_count = model.SjUser.select(model.fn.Max(model.SjUser.resume_count)).where(
            ((model.SjUser.status == 1) | (model.SjUser.session == 1)) &
            (model.SjUser.resume_count > model.SjUser.now_count)).scalar()
    else:
        account = model.SjUser.get(model.SjUser.username == username)
        max_count = account.resume_count
    count = 200  # 每页爬取的数量
    for start in range((start-1)*count, max_count, count):
        if not username:
            # 爬取可以正常登登录的或已有session, 并且没有存在未爬取简历的账号，
            accounts = model.SjUser.select().where(
                ((model.SjUser.status == 1) | (model.SjUser.session == 1)) &
                (model.SjUser.resume_count > model.SjUser.now_count))
        else:
            accounts = model.SjUser.select().where(model.SjUser.username == username)
        for account in accounts:
            if login.exist_session(account.username):
                contact_for_account(account, start, count, True)
            else:
                contact_for_account(account, start, count)
        if len(accounts) == 0:
            break
        log.info('第{0}次循环爬取完成'.format(int(start / count) + 1))
        time.sleep(15)
    log.info('所有账户的联系人爬取完毕！')


def contact_for_account(account, start, count, logined=False):
    if account.resume_count < start:
        # 爬取玩所有简历
        account.now_count = account.resume_count
        account.update_time = int(time.time())
        account.save()
        return False
    if logined:
        session_info = login.get_session(account.username, 'login')
        login.s = session_info['session']
        me = session_info['params']
    else:
        login.s = requests.session()
        me = login.login(account)
        # 如果返回值不是字典类型，说明登录失败，修改账号状态
        if type(me) is not dict:
            account.update_time = int(time.time())
            account.status = me
            account.save()
            return False
    if account.session == 0:
        account.update_time = int(time.time())
        account.session = 1
        account.save()
    contact.client_page_id = me['clientPageId']
    contact.csrf_token = me['csrfToken']
    contact.s = login.s
    connection_list = contact.crawl_connections(start, count)
    if not connection_list:
        return False
    exist_count = 0
    for connection in connection_list:
        pub_id = connection['pub']
        linkedin_id = connection['linkedin']
        if not model.is_exist(model.SjBasic, linkedin_id):
            data = contact.crawl_detail(pub_id)
            if not data:
                continue
            model.init_basic(data['basic'])
            for job in data['career']:
                model.insert_work(job, linkedin_id)
            for edu in data['education']:
                model.insert_edu(edu, linkedin_id)
            for project in data['projects']:
                model.insert_project(project, linkedin_id)
            time.sleep(1)
        else:
            exist_count += 1
    # 如果一页的简历都是已爬过的，那么认为全爬取过
    if exist_count == len(connection_list):
        account.now_count = account.resume_count
        account.update_time = int(time.time())
        account.save()


def crawl_detail(pub_id):
    login.s = requests.session()
    me = login.login()
    contact.client_page_id = me['clientPageId']
    contact.csrf_token = me['csrfToken']
    contact.s = login.s
    data = contact.crawl_detail(pub_id)
    return data

if __name__ == '__main__':
    crawl_contact()
