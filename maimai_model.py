from peewee import *
import configparser

config = configparser.ConfigParser()
config.read('db.config')
database = MySQLDatabase('maimai', **dict(config['Mysql']))


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database


class SjBasic(BaseModel):
    birthday = CharField(null=True)
    city = CharField(null=True)
    create_time = IntegerField()
    email = CharField(null=True)
    headline = CharField(null=True)
    last_company = CharField(null=True)
    last_position = CharField(null=True)
    login = IntegerField(db_column='login_id', null=True)
    mobile = CharField(null=True)
    name = CharField(null=True)
    phone = CharField(null=True)
    province = CharField(null=True)
    status = IntegerField()
    true = IntegerField(db_column='true_id')
    update_time = IntegerField()

    class Meta:
        db_table = 'sj_basic'


class SjCareer(BaseModel):
    company = CharField(null=True)
    description = CharField(null=True)
    end_time = IntegerField(null=True)
    position = CharField(null=True)
    resume = IntegerField(db_column='resume_id')
    start_time = IntegerField(null=True)

    class Meta:
        db_table = 'sj_career'


class SjEducation(BaseModel):
    degree = CharField(null=True)
    description = CharField(null=True)
    end_time = IntegerField(null=True)
    major = CharField(null=True)
    resume = IntegerField(db_column='resume_id')
    school = CharField(null=True)
    start_time = IntegerField(null=True)

    class Meta:
        db_table = 'sj_education'


class SjUser(BaseModel):
    cid = IntegerField(null=True)
    create_time = CharField(null=True)
    maimai_account = CharField(null=True, unique=True)
    maimai_password = CharField(null=True)
    mm = IntegerField(db_column='mm_id', null=True, index=True)
    now_count = IntegerField(null=True)
    resume_count = IntegerField(null=True)
    resume_multi = IntegerField(null=True)
    status = IntegerField(null=True)
    uid = IntegerField()

    class Meta:
        db_table = 'sj_user'
