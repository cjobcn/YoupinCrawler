from flask import Flask, request, jsonify, make_response
import requests

app = Flask(__name__)


@app.route('/hello')
def hello_world():
    return 'Hello World!'


@app.route('/linkedin/login', methods=['POST', 'GET'])
def lkd_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
    else:
        username = request.args.get('username', '')
        password = request.args.get('password', '')
    if password == '' or username == '':
        response = jsonify(dict(status=1409, error='账号和密码不能为空！'))
    else:
        from linkedin import login
        login.s = requests.session()
        # login.s.proxies = {'http': '123.240.124.97:80'}
        me = login.login(username=username, password=password)
        if me == -1:
            response = jsonify(dict(status=1401,
                                    error='密码或账号错误！'))
        elif me == -3:
            response = jsonify(dict(status=1402,
                                    error='被拒绝登录或其他未知错误！'))
        elif me == 2:
            response = jsonify(dict(status=1403,
                                    error='请您需要输入验证码！'))
        elif me == 3:
            response = jsonify(dict(status=1408,
                                    error='需要授权，请在隐私中关闭两步验证！'))
        elif me == -2:
            response = jsonify(dict(status=1410,
                                    error='需要重置密码！'))
        else:
            num = get_cnum(login.s, me)
            me['num'] = num
            response = jsonify(dict(status=1200,
                                    data=me))
    response = make_response(response)
    response = cross_site(response)
    return response


@app.route('/linkedin/verify', methods=['POST', 'GET'])
def lkd_verify():
    if request.method == 'POST':
        username = request.form.get('username', '')
        v_code = request.form.get('vCode', '')
    else:
        username = request.args.get('username', '')
        v_code = request.args.get('vCode', '')
    if v_code == '' or username == '':
        response = jsonify(dict(status=1407, error='账号和验证码不能为空！'))
    else:
        from linkedin import login
        sessionInfo = login.get_session(username)
        if not sessionInfo:
            response = jsonify(dict(status=1406,
                                    data='登录出问题，请重新登录！'))
        else:
            login.s = sessionInfo['session']
            verify_params = sessionInfo['params']
            me = login.verify(username, v_code, verify_params)
            if me == -1:
                response = jsonify(dict(status=1404,
                                        error='您的验证码无效！'))
            elif me == -2:
                response = jsonify(dict(status=1405,
                                        error='登录超时！'))
            else:
                num = get_cnum(login.s, me)
                me['num'] = num
                response = jsonify(dict(status=1200,
                                        data=me))
    response = make_response(response)
    response = cross_site(response)
    return response


def cross_site(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://youpinsh.cn'
    response.headers['Access-Control-Allow-Methods'] = 'POST'
    return response


def get_cnum(session, me):
    from linkedin import contact
    contact.s = session
    contact.client_page_id = me['clientPageId']
    contact.csrf_token = me['csrfToken']
    return contact.crawl_cnum()


if __name__ == '__main__':
    # app.debug = True
    app.run()
