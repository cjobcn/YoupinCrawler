from peewee import *
import configparser

config = configparser.ConfigParser()
config.read('../db.config')
database = MySQLDatabase('linked', **dict(config['Mysql']))


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database


class SjBasic(BaseModel):
    email = CharField(null=True)
    industry = CharField(null=True)
    linkedin = IntegerField(db_column='linkedin_id')
    name = CharField(null=True)
    city = CharField(null=True)
    occupation = CharField(null=True)
    pub = CharField(db_column='pub_id')
    self_str = CharField(null=True)
    skills = CharField(null=True)
    wechat_name = CharField(null=True)
    wechat_qr = CharField(null=True)
    create_time = IntegerField()
    update_time = IntegerField()
    dist = IntegerField()

    class Meta:
        db_table = 'sj_basic'


class SjCareer(BaseModel):
    city = CharField(null=True)
    company = CharField(null=True)
    end_time = IntegerField(null=True)
    linkedin = IntegerField(db_column='linkedin_id')
    position = CharField(null=True)
    start_time = IntegerField(null=True)

    class Meta:
        db_table = 'sj_career'


class SjEducation(BaseModel):
    activity = CharField(null=True)
    degree = CharField(null=True)
    end_time = IntegerField(null=True)
    linkedin = IntegerField(db_column='linkedin_id')
    major = CharField(null=True)
    school = CharField(null=True)
    start_time = IntegerField(null=True)

    class Meta:
        db_table = 'sj_education'


class SjProject(BaseModel):
    description = CharField(null=True)
    end_time = IntegerField(null=True)
    linkedin = IntegerField(db_column='linkedin_id')
    name = CharField(null=True)
    start_time = IntegerField(null=True)

    class Meta:
        db_table = 'sj_project'


class SjUser(BaseModel):
    cid = IntegerField(null=True)
    create_time = CharField(null=True)
    username = CharField(db_column='linked_account', null=True, unique=True)
    password = CharField(db_column='linked_password', null=True)
    lk = IntegerField(db_column='lk_id', index=True, null=True)
    now_count = IntegerField(null=True)
    resume_count = IntegerField(null=True)
    resume_multi = IntegerField(null=True)
    status = IntegerField(null=True)
    uid = IntegerField()

    class Meta:
        db_table = 'sj_user'

