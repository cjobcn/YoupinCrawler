import requests
from bs4 import BeautifulSoup
import html
from urllib.parse import unquote
import time
import configparser


def parse_time(entity, period):
    up_to_now = 2147483647
    start_time = period[entity['entity']].get('startDate', 0)
    end_time = period[entity['entity']].get('endDate', up_to_now)
    if start_time != 0:
        start_time = int(time.mktime(start_time))
    if end_time != up_to_now:
        end_time = int(time.mktime(end_time))
    entity['start_time'] = start_time
    entity['end_time'] = end_time
    return entity


config = configparser.ConfigParser()
config.read('db.config')
username = config['linkedin']['username']
password = config['linkedin']['password']


home_url = 'https://www.linkedin.com/'
login_url = 'https://www.linkedin.com/uas/login'
login_submit_url = 'https://www.linkedin.com/uas/login-submit'


s = requests.Session()

lr = s.get(login_url)
soup = BeautifulSoup(lr.text, "lxml")
soup = soup.find(id="login")
# 提取loginCsrfParam 和 csrfToken
loginCsrfParam = soup.find('input', id='loginCsrfParam-login')['value']
csrfToken = soup.find('input', id='csrfToken-login')['value']


# 模拟登录
login_data = dict(session_key=username, session_password=password,
                  isJsEnabled='false', loginCsrfParam=loginCsrfParam)
lsr = s.post(login_submit_url, data=login_data)


feed_url = 'http://www.linkedin.com/feed/'
connections_url = 'http://www.linkedin.com/voyager/api/relationships/connections'

fr = s.get(feed_url)
soup = BeautifulSoup(fr.text, 'lxml').\
    find('meta', attrs={'name': 'clientPageInstanceId'})
client_page_id = soup['content']

X_li_page_instance = 'urn:li:page:d_flagship3_people_connections;' + client_page_id
# 除去两边的双引号
# csrfToken = r.cookies["JSESSIONID"][1:-1]
headers = {'Csrf-Token': csrfToken,
           'X-Requested-With': 'XMLHttpRequest',
           'X-LI-Lang': 'zh_CN',
           'X-li-page-instance': X_li_page_instance,
           'X-LI-Track': '{"clientVersion":"1.0.*","osName":"web","timezoneOffset":8,"deviceFormFactor":"DESKTOP"}',
           'X-RestLi-Protocol-Version': '2.0.0',
           'Accept': 'application/vnd.linkedin.normalized+json',
           }
cr = s.get(connections_url, headers=headers)

relation_list = [item['publicIdentifier'] for item in cr.json()['included']
                 if 'publicIdentifier' in item]

for pub_id in relation_list:
    detail_url = home_url + 'in/' + pub_id
    dr = s.get(detail_url)
    # html反转义 和 url解码
    content = unquote(html.unescape(dr.text).encode(dr.encoding).decode())
    profile_url = 'http://www.linkedin.com/voyager/api/identity/profiles/{0}/profileView'.format(pub_id)
    headers['X-li-page-instance'] = 'urn:li:page:d_flagship3_profile_view_base;' + client_page_id
    pr = s.get(profile_url, headers=headers)
    basic = {}
    jobs = []
    education = []
    projects = []
    if pr.status_code == 200:
        pr_json = pr.json()
        basic['skills'] = []
        time_period = {}
        for data in pr_json['included']:
            if data['$type'] == 'com.linkedin.voyager.identity.profile.Profile':
                basic['name'] = data['lastName'] + data['firstName']
                basic['industry'] = data.get('industryName', '')
                basic['location'] = data.get('locationName', '')
                basic['last_position'] = data.get('headline', '')
            if data['$type'] == 'com.linkedin.voyager.identity.profile.Education':
                edu = dict(school=data.get('schoolName', ''),
                           degree=data.get('degreeName', ''),
                           major=data.get('fieldOfStudy', ''),
                           activities=data.get('activities', ''),
                           entity=data.get('entityUrn', '').split(',')[1][0:-1])
                education.append(edu)
            if data['$type'] == 'com.linkedin.voyager.identity.profile.Position':
                job = dict(company=data.get('companyName', ''),
                           city=data.get('locationName', ''),
                           position=data.get('title', ''),
                           entity=data.get('entityUrn', '').split(',')[1][0:-1])
                jobs.append(job)
            if data['$type'] == 'com.linkedin.voyager.identity.profile.Project':
                project = dict(name=data.get('title', ''),
                               description=data.get('description', ''),
                               entity=data.get('entityUrn', '').split(',')[1][0:-1])
                projects.append(project)
            if data['$type'] == 'com.linkedin.voyager.identity.profile.Skill':
                basic['skills'].append(data.get('name', ''))
            if data['$type'] == 'com.linkedin.common.Date':
                time_id = data['$id'].split(',')
                if time_id[1][0:-1] not in time_period:
                    time_period[time_id[1][0:-1]] = {time_id[3]: (data.get('year', 0),
                                                                  data.get('month', 0), 0, 0, 0, 0, 0, 0, 0)}
                else:
                    time_period[time_id[1][0:-1]][time_id[3]] = (data.get('year', 0),
                                                                 data.get('month', 0), 0, 0, 0, 0, 0, 0, 0)
        for i, job in enumerate(jobs):
            jobs[i] = parse_time(job, time_period)
        for i, edu in enumerate(education):
            education[i] = parse_time(edu, time_period)

    contact_url = 'http://www.linkedin.com/voyager/api/identity/profiles/{0}/profileContactInfo'.format(pub_id)
    headers['X-li-page-instance'] = 'urn:li:page:page:d_flagship3_profile_view_base;' + client_page_id
    cr = s.get(contact_url, headers=headers)
    if cr.status_code == 200:
        cr_json = cr.json()
        basic['email'] = cr_json['data'].get('emailAddress', '')

    break


def parse_time(entity, period):
    up_to_now = 2147483647
    start_time = period[entity['entity']].get('startDate', 0)
    end_time = period[entity['entity']].get('endDate', up_to_now)
    if start_time != 0:
        entity['start_time'] = time.mktime(start_time)
    if end_time != up_to_now:
        entity['end_time'] = time.mktime(end_time)
    return entity


# with open('test.html', 'wb') as f:
#     f.write(lsr.text.encode())
