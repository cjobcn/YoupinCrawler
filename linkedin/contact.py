import requests
import yplog
import re
import time
import base64

log = yplog.YPLogger('contact')
s = requests.Session()
client_page_id = 0
csrf_token = ''
home_url = 'https://www.linkedin.com/'


def crawl_cnum():
    summary_url = home_url + 'voyager/api/relationships/connectionsSummary'
    x_li_page_instance = 'urn:li:page:d_flagship3_feed;' + str(client_page_id)
    headers = {'Csrf-Token': csrf_token,
               'X-Requested-With': 'XMLHttpRequest',
               'X-LI-Lang': 'zh_CN',
               'X-li-page-instance': x_li_page_instance,
               'X-LI-Track': '{"clientVersion":"1.0.*","osName":"web","timezoneOffset":8,"deviceFormFactor":"DESKTOP"}',
               'X-RestLi-Protocol-Version': '2.0.0',
               'Accept': 'application/vnd.linkedin.normalized+json',
               }
    csr = s.get(summary_url, headers=headers)
    if csr.status_code == 200:
        n = csr.json()['data'].get('numConnections', 0)
        log.info('联系人数为：' + str(n))
        return n
    else:
        log.warn('获取联系人数失败！')
        return False


def crawl_connections(start=0, count=100):
    connections_url = home_url + '/voyager/api/relationships/connections'
    params = dict(sortType='RECENTLY_ADDED',
                  count=count, start=start)
    x_li_page_instance = 'urn:li:page:d_flagship3_people_connections;{0}'.format(client_page_id)
    # 除去两边的双引号
    # csrfToken = r.cookies["JSESSIONID"][1:-1]
    headers = {'Csrf-Token': csrf_token,
               'X-Requested-With': 'XMLHttpRequest',
               'X-LI-Lang': 'zh_CN',
               'X-li-page-instance': x_li_page_instance,
               'X-LI-Track': '{"clientVersion":"1.0.*","osName":"web","timezoneOffset":8,"deviceFormFactor":"DESKTOP"}',
               'X-RestLi-Protocol-Version': '2.0.0',
               'Accept': 'application/vnd.linkedin.normalized+json',
               }
    cr = s.get(connections_url, headers=headers, params=params)
    if cr.status_code == 200:
        relation_list = []
        for item in cr.json()['included']:
            if 'publicIdentifier' in item:
                if re.match('[a-zA-Z]', item.get('lastName', '')) is not None:
                    name = item.get('lastName', '') + ' ' + item.get('firstName', '')
                else:
                    name = item.get('lastName', '') + item.get('firstName', '')
                relation_list.append(dict(pub=item.get('publicIdentifier', ''),
                                          name=name,
                                          occupation=item.get('occupation', ''),
                                          linkedin=item.get('objectUrn', '').split(':')[-1]))
        log.info('联系人列表:{0}'.format(len(relation_list)))
        return relation_list
    else:
        log.warn('获取联系人列表失败！')
        return False


def crawl_detail(pub_id, dist=1):
    log.info('开始爬取{0}'.format(pub_id))
    profile_url = home_url + '/voyager/api/identity/profiles/{0}/profileView'.format(pub_id)
    x_li_page_instance = 'urn:li:page:d_flagship3_profile_view_base;{0}'.format(client_page_id)
    headers = {'Csrf-Token': csrf_token,
               'X-Requested-With': 'XMLHttpRequest',
               'X-LI-Lang': 'zh_CN',
               'X-li-page-instance': x_li_page_instance,
               'X-LI-Track': '{"clientVersion":"1.0.*","osName":"web","timezoneOffset":8,"deviceFormFactor":"DESKTOP"}',
               'X-RestLi-Protocol-Version': '2.0.0',
               'Accept': 'application/vnd.linkedin.normalized+json',
               }
    basic = {}
    jobs = []
    education = []
    projects = []
    pr = s.get(profile_url, headers=headers)
    if pr.status_code == 200:
        pr_json = pr.json()
        basic['skills'] = []
        basic['dist'] = dist
        time_period = {}
        for data in pr_json['included']:
            if data['$type'] == 'com.linkedin.voyager.identity.profile.Profile':
                if re.match('[a-zA-Z]', data.get('lastName', '')) is not None:
                    name = data.get('lastName', '') + ' ' + data.get('firstName', '')
                else:
                    name = data.get('lastName', '') + data.get('firstName', '')
                basic['name'] = name
                basic['industry'] = data.get('industryName', '')
                basic['city'] = data.get('locationName', '')
                basic['self_str'] = data.get('summary', '')
            elif data['$type'] == 'com.linkedin.voyager.identity.shared.MiniProfile':
                basic['occupation'] = data.get('occupation', '')
                basic['linkedin'] = data.get('objectUrn', '').split(':')[-1]
                basic['pub'] = data.get('publicIdentifier', '')
            elif data['$type'] == 'com.linkedin.voyager.identity.profile.Education':
                edu = dict(school=data.get('schoolName', ''),
                           degree=data.get('degreeName', ''),
                           major=data.get('fieldOfStudy', ''),
                           activity=data.get('activities', ''),
                           entity=data.get('entityUrn', '').split(',')[1][0:-1])
                education.append(edu)
            elif data['$type'] == 'com.linkedin.voyager.identity.profile.Position':
                job = dict(company=data.get('companyName', ''),
                           city=data.get('locationName', ''),
                           position=data.get('title', ''),
                           entity=data.get('entityUrn', '').split(',')[1][0:-1])
                jobs.append(job)
            elif data['$type'] == 'com.linkedin.voyager.identity.profile.Project':
                project = dict(name=data.get('title', ''),
                               description=data.get('description', ''),
                               entity=data.get('entityUrn', '').split(',')[1][0:-1])
                projects.append(project)
            elif data['$type'] == 'com.linkedin.voyager.identity.profile.Skill':
                basic['skills'].append(data.get('name', ''))
            elif data['$type'] == 'com.linkedin.common.Date':
                time_id = data['$id'].split(',')
                if len(time_id) > 3:
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
        for i, edu in enumerate(projects):
            projects[i] = parse_time(edu, time_period)
        basic['skills'] = ','.join(basic['skills'])

    contact_url = home_url + '/voyager/api/identity/profiles/{0}/profileContactInfo'.format(pub_id)
    headers['X-li-page-instance'] = 'urn:li:page:page:d_flagship3_profile_view_base;{0}'.format(client_page_id)
    cr = s.get(contact_url, headers=headers)
    if cr.status_code == 200:
        cr_json = cr.json()
        basic['email'] = cr_json['data'].get('emailAddress', '')
        for item in cr_json['included']:
            if item['$type'] == 'com.linkedin.voyager.identity.profile.WeChatContactInfo':
                basic['wechat_name'] = item.get('name', '')
                qr_url = item.get('qrCodeImageUrl', '')
                qr = s.get(qr_url)
                if qr.status_code == 200:
                    basic['wechat_qr'] = base64.b64encode(qr.content).decode()
    log.info('成功爬取{0}'.format(pub_id))
    return {'basic': basic,
            'career': jobs,
            'education': education,
            'projects': projects}


def parse_time(entity, period):
    up_to_now = 2147483647
    if entity['entity'] in period:
        start_time = period[entity['entity']].get('startDate', 0)
        end_time = period[entity['entity']].get('endDate', up_to_now)
    else:
        start_time = end_time = 0
    del entity['entity']
    if start_time != 0:
        start_time = int(time.mktime(start_time))
    if end_time != up_to_now and end_time != 0:
        end_time = int(time.mktime(end_time))
    entity['start_time'] = start_time
    entity['end_time'] = end_time
    return entity
