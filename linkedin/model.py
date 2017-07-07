import time
from linkedin.db import *
import yplog

log = yplog.YPLogger('model', __package__)


def init_basic(data):
    """
    将联系人列表中的简要信息保存到basic表中
    :param data:
    :return:
    """
    basic = is_exist(SjBasic, data['linkedin'])
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


def insert_work(data, linkedin_id):
    """
    插入工作经历
    :param data:
    :param linkedin_id:
    :return:
    """
    if is_exist(SjCareer, linkedin_id):
        return False
    data['linkedin'] = linkedin_id
    return insert(SjCareer, data)


def insert_edu(data, linkedin_id):
    if is_exist(SjEducation, linkedin_id):
        return False
    data['linkedin'] = linkedin_id
    return insert(SjEducation, data)


def insert_project(data, linkedin_id):
    if is_exist(SjProject, linkedin_id):
        return False
    data['linkedin'] = linkedin_id
    return insert(SjProject, data)


def is_exist(table, linkedin_id):
    """
    判断信息是否已经爬取(插入前判断)
    :param table:
    :param linkedin_id:
    :return:
    """
    try:
        rid = table.get(table.linkedin == linkedin_id)
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
