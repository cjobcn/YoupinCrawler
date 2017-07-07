import yplog
import decrypt
import requests
from bs4 import BeautifulSoup
import re
import html
from urllib.parse import unquote
import json
from linkedin import contact

log = yplog.YPLogger('login')
s = requests.Session()


def login(account):
    """
    模拟登录
    :param account:
    :return:
    """
    login_url = 'https://www.linkedin.com/uas/login'
    login_submit_url = 'https://www.linkedin.com/uas/login-submit'
    lr = s.get(login_url)
    if lr.status_code == 200:
        soup = BeautifulSoup(lr.text, "lxml")
        soup = soup.find(id="login")
        # 提取loginCsrfParam 和 csrfToken
        loginCsrfParam = soup.find('input', id='loginCsrfParam-login')['value']
        csrfToken = soup.find('input', id='csrfToken-login')['value']
    else:
        log.warn("""访问登录页面被拒绝:{0}
        {1}""".format(lr.status_code, lr.text))
        return -3
    # 模拟登录
    try:
        username = account.username
        password = decrypt.think_decrypt(account.password, 'linkedin1')
    except AttributeError:
        import configparser
        config = configparser.ConfigParser()
        config.read('../db.config')
        username = config['linkedin']['username']
        password = config['linkedin']['password']
    log.info('{0}准备登录'.format(username))
    login_data = dict(session_key=username, session_password=password,
                      isJsEnabled='false', loginCsrfParam=loginCsrfParam)
    lsr = s.post(login_submit_url, data=login_data)
    if lsr.status_code == 200:
        if re.search('There were one or more errors in your submission', lsr.text):
            log.warn('{0}账户或密码错误！'.format(username))
            return -1
        if re.search('Sign-In Verification', lsr.text):
            log.warn('{0}需要验证！'.format(username))
            return 2
        soup = BeautifulSoup(lsr.text, 'lxml'). \
            find('meta', attrs={'name': 'clientPageInstanceId'})
        client_page_id = soup['content']
        text = unquote(html.unescape(lsr.text).encode(lsr.encoding).decode())
        soup = BeautifulSoup(text, "lxml")
        soup = soup.find('code', text=re.compile(r'"com.linkedin.voyager.common.Me"'))
        me = json.loads(soup.get_text())
        linkedin_id = pub_id = 0
        for item in me['included']:
            if item['$type'] == 'com.linkedin.voyager.identity.shared.MiniProfile':
                linkedin_id = item.get('objectUrn', '').split(':')[-1]
                pub_id = item['publicIdentifier']
                break
        log.info('{0}登录成功'.format(username))
        return {'clientPageId': client_page_id,
                'csrfToken' :csrfToken,
                'linkedin': linkedin_id,
                'pub_id': pub_id}
    else:
        log.warn("""登录请求被拒绝:{0}
                {1}""".format(lr.status_code, lr.text))
        return -2


def check_login(account):
    """
    检测当前账号
    :return:
    """
    log.info(account.username + '账户检测')
    me = login(account)
    if type(me) == dict:
        account.lk = me['linkedin']
        contact.s = s
        contact.client_page_id = me['clientPageId']
        contact.csrf_token = me['csrfToken']
        account.resume_count = contact.crawl_cnum()
        account.status = 1
        log.info(account.username + '账户可用')
    else:
        account.status = me
    account.save()
