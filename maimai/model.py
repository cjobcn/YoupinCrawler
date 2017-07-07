import time
from maimai.db import *
import yplog

log = yplog.YPLogger('model')


def init_basic(data):
    """
    将联系人列表中的简要信息保存到basic表中
    :param data:
    :return:
    """
    basic = is_exist(SjBasic, data['mm'])
    now = int(time.time())
    if not basic:
        data['create_time'] = now
        data['update_time'] = now
        return insert(SjBasic, data)
    elif basic.dist > data['dist']:
        basic.dist = data['dist']
        basic.update_time = now
        return basic.save()
    else:
        return False


def insert_work(data, mm_id):
    """
    插入工作经历
    :param data:
    :param mm_id:
    :return:
    """
    if is_exist(SjCareer, mm_id):
        return False
    work_exp = dict(mm=mm_id,
                    company=data.get('company', ''),
                    position=data.get('position', ''),
                    description=data.get('description', '')
                    )
    if data['start_date'] is not None:
        work_exp['start_time'] = time.mktime(
            time.strptime(data['start_date'], '%Y-%m')) if data['start_date'] != '1970-1' else 0
        if data['end_date'] is None:
            work_exp['end_time'] = 2147483647
        else:
            work_exp['end_time'] = time.mktime(
                time.strptime(data['end_date'], '%Y-%m'))
    return insert(SjCareer, work_exp)


def insert_edu(data, mm_id):
    if is_exist(SjEducation, mm_id):
        return False
    degrees = ['专科', '本科', '硕士', '博士', '博士后', '其他']
    edu = dict(mm=mm_id,
               school=data['school'],
               degree=degrees[data['degree'] if data['degree'] < 5 else 5],
               major=data.get('department', ''),
               description=data.get('description', '')
               )
    if data['start_date'] is not None:
        edu['start_time'] = time.mktime(
            time.strptime(data['start_date'], '%Y-%m')) if data['start_date'] != '1970-1' else 0
        if data['end_date'] is None:
            edu['end_time'] = 2147483647
        else:
            edu['end_time'] = time.mktime(
                time.strptime(data['end_date'], '%Y-%m'))
    return insert(SjEducation, edu)


def is_exist(table, mm_id):
    """
    判断信息是否已经爬取(插入前判断)
    :param table:
    :param mm_id:
    :return:
    """
    try:
        rid = table.get(table.mm == mm_id)
        return rid
    except DoesNotExist:
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
    now = int(time.time())
    values['update_time'] = now
    return table.update(**values).where(condition).execute()


def get_accounts(mm_account=None, condition=True):
    """
    获取账号
    :param mm_account:
    :param condition:
    :return:
    """
    if mm_account is not None:
        try:
            if type(mm_account) == int:
                result = SjUser.get(SjUser.mm == mm_account)
            else:
                result = SjUser.get(SjUser.maimai_account == mm_account)
        except DoesNotExist:
            return
    else:
        result = SjUser.select().where(condition)
    return result


def query(table, condition, page=1):
    pnum = 100
    try:
        return table.select().where(condition).paginate(page, pnum)
    except DoesNotExist:
        return
