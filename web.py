from flask import Flask
from flask import request
from flask import jsonify
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
        return jsonify(dict(status=-1, error='账号和密码不能为空！'))

    from linkedin import login
    login.s = requests.session()
    me = login.login(username=username, password=password)
    if me == -1:
        return jsonify(dict(status=1401,
                            error='密码或账号错误！'))
    elif me == -2:
        return jsonify(dict(status=1402,
                            error='被拒绝登录！'))
    elif me == 2:
        return jsonify(dict(status=1403,
                            error='需要输入验证码！'))
    else:
        return jsonify(dict(status=1200,
                            data=me))


@app.route('/linkedin/verify', methods=['POST'])
def lkd_verify():
    username = request.args.get('username', '')
    v_code = request.args.get('vCode', '')
    if v_code == '' or username == '':
        return jsonify(dict(status=1407, error='账号和验证码不能为空！'))
    from linkedin import login
    sessionInfo = login.get_session(username)
    if not sessionInfo:
        return jsonify(dict(status=1406,
                            data='登录出问题，请重新登录！'))
    login.s = sessionInfo['session']
    verify_params = sessionInfo['params']
    me = login.verify(username, v_code, verify_params)
    if me == -1:
        return jsonify(dict(status=1404,
                            error='验证码无效！'))
    elif me == -2:
        return jsonify(dict(status=1405,
                            error='登录超时！'))
    else:
        return jsonify(dict(status=1200,
                            data=me))

if __name__ == '__main__':
    # app.debug = True
    app.run()
