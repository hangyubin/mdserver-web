# coding:utf-8

# ---------------------------------------------------------------------------------
# MW-Linux面板
# ---------------------------------------------------------------------------------
# copyright (c) 2018-∞(https://github.com/midoks/mdserver-web) All rights reserved.
# ---------------------------------------------------------------------------------
# Author: midoks <midoks@163.com>
# ---------------------------------------------------------------------------------

import io
import time

from flask import Blueprint, render_template
from flask import make_response
from flask import Response
from flask import request,g

from admin.common import isLogined
from admin.user_login_check import panel_login_required
from admin import cache,session
from admin import model
import core.mw as mw


blueprint = Blueprint('dashboard', __name__, url_prefix='/', template_folder='../../templates')
@blueprint.route('/')
@panel_login_required
def index():
    return render_template('default/index.html')

# 仅针对webhook插件
@app.route("/hook", methods=['POST', 'GET'])
def webhook():
    # 兼容获取关键数据
    access_key = request.args.get('access_key', '').strip()
    if access_key == '':
        access_key = request.form.get('access_key', '').strip()

    params = request.args.get('params', '').strip()
    if params == '':
        params = request.form.get('params', '').strip()

    input_args = {
        'access_key': access_key,
        'params': params,
    }

    wh_install_path = mw.getServerDir() + '/webhook'
    if not os.path.exists(wh_install_path):
        return mw.returnJson(False, '请先安装WebHook插件!')

    package = mw.getPanelDir() + "/plugins/webhook"
    if not package in sys.path:
        sys.path.append(package)
        
    try:
        import webhook_index
        return webhook_index.runShellArgs(input_args)
    except Exception as e:
        return str(e)

# 安全路径
@blueprint.route('/<path>',endpoint='admin_safe_path',methods=['GET'])
def admin_safe_path(path):
    db_path = model.getOption('admin_path')
    if db_path == path:
        return render_template('default/login.html')

    unauthorized_status = model.getOption('unauthorized_status')
    if unauthorized_status == '0':
        return render_template('default/path.html')
    return Response(status=int(unauthorized_status))


# ---------------------------------------------------------------------------------
# 定义登录入口相关方法
# ---------------------------------------------------------------------------------

# 登录页: 当设置了安全路径,本页失效。
@blueprint.route('/login')
def login():
    signout = request.args.get('signout', '')
    if signout == 'True':
        session.clear()
        session['login'] = False
        session['overdue'] = 0

    db_path = model.getOption('admin_path')
    if db_path == '':
        return render_template('default/login.html')
    else:
        unauthorized_status = model.getOption('unauthorized_status')
        if unauthorized_status == '0':
            return render_template('default/path.html')
        return Response(status=int(unauthorized_status))

# 验证码
@blueprint.route('/code')
def code():
    import utils.vilidate as vilidate
    vie = vilidate.vieCode()
    codeImage = vie.GetCodeImage(80, 4)
    out = io.BytesIO()
    codeImage[0].save(out, "png")
    session['code'] = mw.md5(''.join(codeImage[1]).lower())

    img = Response(out.getvalue(), headers={'Content-Type': 'image/png'})
    return make_response(img)

# 检查是否登录
@blueprint.route('/check_login',methods=['GET','POST'])
def check_login():
    if isLogined():
        return mw.returnData(True,'已登录')
    return mw.returnData(False,'未登录')

# 执行登录操作
@blueprint.route('/do_login', endpoint='do_login', methods=['POST'])
def do_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    code = request.form.get('code', '').strip()

    login_cache_count = 5
    login_cache_limit = cache.get('login_cache_limit')

    if 'code' in session:
        if session['code'] != mw.md5(code):
            if login_cache_limit == None:
                login_cache_limit = 1
            else:
                login_cache_limit = int(login_cache_limit) + 1

            if login_cache_limit >= login_cache_count:
                model.setOption('admin_close', 'yes')
                return mw.returnJson(False, '面板已经关闭!')

            cache.set('login_cache_limit', login_cache_limit, timeout=10000)
            login_cache_limit = cache.get('login_cache_limit')
            login_err_msg = mw.getInfo("验证码错误,您还可以尝试[{1}]次!", (str(login_cache_count - login_cache_limit)))
            mw.writeLog('用户登录', login_err_msg)
            return mw.returnData(False, login_err_msg)

    info = model.getUserByName(username)
    password = mw.md5(password)

    if info['name'] != username or info['password'] != password:
        msg = "<a style='color: red'>密码错误</a>,帐号:{1},密码:{2},登录IP:{3}", (('****', '******', request.remote_addr))

        if login_cache_limit == None:
            login_cache_limit = 1
        else:
            login_cache_limit = int(login_cache_limit) + 1

        if login_cache_limit >= login_cache_count:
            model.setOption('admin_close', 'yes')
            return mw.returnData(False, '面板已经关闭!')

        cache.set('login_cache_limit', login_cache_limit, timeout=10000)
        login_cache_limit = cache.get('login_cache_limit')
        mw.writeLog('用户登录', mw.getInfo(msg))
        return mw.returnData(-1, mw.getInfo("用户名或密码错误,您还可以尝试[{1}]次!", (str(login_cache_count - login_cache_limit))))


    session['login'] = True
    session['username'] = info['name']
    session['overdue'] = int(time.time()) + 7 * 24 * 60 * 60

    return mw.returnJson(1, '登录成功,正在跳转...')
