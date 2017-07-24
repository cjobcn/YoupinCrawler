from flask import Flask, request, jsonify, make_response
import requests

app = Flask(__name__)


@app.route('/hello')
def hello_world():
    return 'Hello World!'


@app.route('/linkedin/login', methods=['POST'])
def lkd_login():
    username = request.args.get('username', '')
    password = request.args.get('password', '')
    if password == '' or username == '':
        response = jsonify(dict(status=-1, error='账号和密码不能为空！'))
    else:
        from linkedin import login
        login.s = requests.session()
        # login.s.proxies = {'http': '123.240.124.97:80'}
        me = login.login(username=username, password=password)
        if me == -1:
            response = jsonify(dict(status=1401,
                                    error='密码或账号错误！'))
        elif me == -2:
            response = jsonify(dict(status=1402,
                                    error='被拒绝登录！'))
        elif me == 2:
            response = jsonify(dict(status=1403,
                                    error='需要输入验证码！'))
        elif me == 3:
            response = jsonify(dict(status=1408,
                                    error='需要授权，请在隐私中关闭两步验证！'))
        else:
            response = jsonify(dict(status=1200,
                                    data=me))
    response = make_response(response)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST'
    return response


@app.route('/linkedin/verify', methods=['POST'])
def lkd_verify():
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
                                        error='验证码无效！'))
            elif me == -2:
                response = jsonify(dict(status=1405,
                                        error='登录超时！'))
            else:
                response = jsonify(dict(status=1200,
                                        data=me))
    response = make_response(response)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST'
    return response

if __name__ == '__main__':
    # app.debug = True
    app.run()
