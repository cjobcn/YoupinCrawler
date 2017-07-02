import requests
import time
import maimai_model as mm_model
import maimai_login as mm_login
from logbook import Logger, FileHandler

# 日志
logfile = 'logs/maimai/{0}.log'.format(
    time.strftime("%Y_%m_%d", time.localtime()))
FileHandler(logfile).push_application()
log = Logger('maimai_detail')

s = requests.Session()
login_id = 0


def crawl_detail(mm_id):
    """
    爬取详情
    :param mm_id:
    :return:
    """
    print(str(mm_id) + '的详情爬取开始！')
    log.info(str(mm_id) + '的详情爬取开始！')
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
    rid = mm_model.update(mm_model.SjBasic, basic,
                          mm_model.SjBasic.mm == mm_id)
    if rid > 0:
        for work_exp in uinfo['work_exp']:
            mm_model.insert_work(work_exp, mm_id)
        for edu in uinfo['education']:
            mm_model.insert_edu(edu, mm_id)
        print(str(mm_id) + '的详情爬取结束！')
        log.info(str(mm_id) + '的详情爬取结束！')
    else:
        log.warn(str(mm_id) + 'basic表更新失败')


if __name__ == "__main__":
    mm_login.account = mm_model.get_accounts(18305179926)
    login_id = mm_login.login()
    s = mm_login.s
    current_id = mm_login.account.mm
    mms = mm_model.query(mm_model.SjBasic,
                (mm_model.SjBasic.login == current_id) &
                (mm_model.SjBasic.status == 0) &
                (mm_model.SjBasic.dist == 1))
    if mms is not None:
        current_id = mm_login.login()
        if current_id > 0:
            for mm in mms:
                crawl_detail(mm.mm)
                time.sleep(1)
