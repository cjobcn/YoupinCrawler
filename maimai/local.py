import yplog
from maimai import model
import sys
import os
import json


# 日志
log = yplog.YPLogger('parse', 'maimai')

maimai_dir = "G:/ShareFolder/maimai/"


def get_login_id(username):
    mm = model.get_accounts(username)
    if mm is not None:
        return mm.mm


def bulk_parse():
    for account in os.listdir(maimai_dir):
        login_id = get_login_id(account)
        detail_dir = maimai_dir + account
        for json_file in os.listdir(detail_dir):
            with open(os.path.join(
                    detail_dir, json_file), 'r',
                    encoding='utf-8') as f:
                try:
                    detail = json.load(f).get('data', '')
                    if detail:
                        parse(detail, login_id)
                except Exception:
                    log.error(json_file + '出错！')


def parse(detail, login_id):
    card = detail['card']
    mm_id = card['id']
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
                 dist=card.get('dist', 1),
                 status=1
                 )
    info = model.is_exist(model.SjBasic, mm_id)
    rid = 0
    if not info:
        basic['login'] = login_id
        rid = model.init_basic(basic)
    else:
        if info.status == 0:
            rid = model.update(model.SjBasic, basic,
                               model.SjBasic.mm == mm_id)
    if rid > 0:
        for work_exp in uinfo.get('work_exp', []):
            model.insert_work(work_exp, mm_id)
        for edu in uinfo.get('education', []):
            model.insert_edu(edu, mm_id)
        log.info(str(mm_id) + '的详情解析结束！')
    else:
        log.info(str(mm_id) + '已存在')


if __name__ == '__main__':
    maimai_dir = "E:/maimai/"
    bulk_parse()
