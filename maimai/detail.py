import requests
import time
from maimai import login, model
import yplog

# 日志
log = yplog.YPLogger('detail', __package__)

s = requests.Session()
login_id = 0
home_url = 'https://maimai.cn/'


def crawl_detail(mm_id):
    """
    爬取详情
    :param mm_id:
    :return:
    """
    log.info('{0}的详情爬取开始！'.format(mm_id))
    json_only_param = dict(jsononly=1)
    detail_url = home_url + 'contact/detail/%d' % mm_id
    dr = s.get(detail_url, params=json_only_param)
    if dr.status_code == 200:
        detail = dr.json()
        if 'data' in detail:
            detail = detail['data']
        else:
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
    rid = model.update(model.SjBasic, basic,
                       model.SjBasic.mm == mm_id)
    if rid > 0:
        for work_exp in uinfo['work_exp']:
            model.insert_work(work_exp, mm_id)
        for edu in uinfo['education']:
            model.insert_edu(edu, mm_id)
        log.info(str(mm_id) + '的详情爬取结束！')
    else:
        log.warn(str(mm_id) + 'basic表更新失败')


if __name__ == "__main__":
    account = model.get_accounts(18933305297)
    login.s = requests.Session()
    login_id = login.login(account)
    s = login.s
    current_id = account.mm
    mms = model.query(model.SjBasic,
                      (model.SjBasic.login == current_id) &
                      (model.SjBasic.status == 0) &
                      (model.SjBasic.dist == 1))
    if mms is not None:
        current_id = login.login(account)
        if current_id > 0:
            for mm in mms:
                crawl_detail(mm.mm)
                time.sleep(1)
