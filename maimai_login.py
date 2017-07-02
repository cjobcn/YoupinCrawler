import requests
import re
import json
import time
import decrypt
import maimai_model as mm_model
from logbook import Logger, FileHandler


# 日志
logfile = 'logs/maimai/{0}.log'.format(
    time.strftime("%Y_%m_%d", time.localtime()))
FileHandler(logfile).push_application()
log = Logger('maimai_login')

s = requests.Session()
account = None


def login():
    """
    模拟登录
    :return: 登录成功返回当前用户的mmid，否则失败码
    """
    username = account.maimai_account
    password = decrypt.think_decrypt(account.maimai_password, 'maimai1')
    print(username, password)
    login_url = 'https://maimai.cn/login'
    login_data = dict(m=username,
                      p=password,
                      to='', pa='+86')
    lr = s.post(login_url, data=login_data)

    if lr.status_code == 200:
        login_json = json_parse(lr.text)
        if login_json is None:
            if re.search('帐号或密码(不正确|错误|频繁出错)', lr.text) is not None:
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
        log.info(account.maimai_account + '账户可用')
    else:
        account.status = login_id
    account.save()


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

if __name__ == '__main__':

    # 批量检测所有账户是否正常
    print('开始账户检测！')
    log.info('开始账户检测！')
    for account in mm_model.SjUser.select():
        s = requests.Session()
        check_login()
        time.sleep(4)
    print('账户检测完毕！')
    log.info('账户检测完毕！')
