from peewee import *
import configparser

config = configparser.ConfigParser()
config.read('../db.config')
database = MySQLDatabase(config['maimai']['database'],
                         **dict(config['Mysql']))


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database


class SjBasic(BaseModel):
    name = CharField(null=True)
    mm = IntegerField(db_column='mm_id', unique=True)
    birthday = CharField(null=True)
    province = CharField(null=True)
    city = CharField(null=True)
    mobile = CharField(null=True)
    phone = CharField(null=True)
    email = CharField(null=True)
    last_company = CharField(null=True)
    last_position = CharField(null=True)
    status = IntegerField()
    headline = CharField(null=True)
    create_time = IntegerField()
    update_time = IntegerField()
    login = IntegerField(db_column='login_id', null=True)
    dist = IntegerField()

    class Meta:
        db_table = 'sj_basic'


class SjCareer(BaseModel):
    mm = IntegerField(db_column='mm_id')
    start_time = IntegerField(null=True)
    end_time = IntegerField(null=True)
    company = CharField(null=True)
    position = CharField(null=True)
    description = CharField(null=True)

    class Meta:
        db_table = 'sj_career'


class SjEducation(BaseModel):
    mm = IntegerField(db_column='mm_id')
    school = CharField(null=True)
    degree = CharField(null=True)
    major = CharField(null=True)
    description = CharField(null=True)
    start_time = IntegerField(null=True)
    end_time = IntegerField(null=True)

    class Meta:
        db_table = 'sj_education'


class SjUser(BaseModel):
    cid = IntegerField(null=True)
    resume_count = IntegerField(null=True)
    now_count = IntegerField(null=True)
    username = CharField(db_column='maimai_account', null=True, unique=True)
    password = CharField(db_column='maimai_password', null=True)
    mm = IntegerField(db_column='mm_id', null=True, index=True)
    resume_multi = IntegerField(null=True)
    status = IntegerField(null=True)
    uid = IntegerField()
    create_time = CharField(null=True)

    class Meta:
        db_table = 'sj_user'
