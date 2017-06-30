import requests
from bs4 import BeautifulSoup
import html

import configparser

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
csrfToken = soup.find('input', id = 'csrfToken-login')['value']


# 模拟登录
login_data = dict(session_key=username, session_password=password,
                  isJsEnabled='false', loginCsrfParam=loginCsrfParam)
lsr = s.post(login_submit_url, data=login_data)


feed_url = 'http://www.linkedin.com/feed/'
connections_url = 'http://www.linkedin.com/voyager/api/relationships/connections'

fr = s.get(feed_url)
soup = BeautifulSoup(fr.text, 'lxml').\
    find('meta', attrs={'name': 'clientPageInstanceId'})

X_li_page_instance = 'urn:li:page:d_flagship3_people_connections;' + soup['content']
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
    # html反转义
    content = html.unescape(dr.text).encode(dr.encoding).decode()


with open('test.html', 'wb') as f:
    f.write(lsr.text.encode())
