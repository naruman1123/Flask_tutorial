import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

""" ・'auth'と名付けられたBlueprintを作成
    ・Blueprintは定義された場所を知る必要があるため、第二引数に__name__を指定しています。
    ・url_prefixの値は、Blueprintと関連のあるURLの先頭につけられます。
"""
bp = Blueprint('auth', __name__, url_prefix='/auth')

"""----------------------------------------------------Register (ユーザ登録)-----------------------------------------------------------------------------------------------------------"""
#@bp.routeはURL /registerとregister関数を関連づけます
@bp.route('/register', methods=('GET', 'POST'))#登録画面ではGETリクエストもPOSTリクエストもあり得るので、第二引数のmethodsにはタプルで'GET', 'POST'を設定
#＜register関数の定義＞
def register():
    if request.method == 'POST':#リクエストメソッドが’POST’の場合、
        username = request.form['username']#ユーザが入力したフォームからusernameを取り出す
        password = request.form['password']#ユーザが入力したフォームからpasswordを取り出す
        db = get_db()#　　もしも検証が成功した場合は、新しいユーザのデータをデータベースに挿入します。
        error = None

        if not username:# ユーザ名が空だった場合
            error = 'Username is required.'
        elif not password:# パスワードが空だった場合
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    #db.execut内の？はプレースホルダと呼ばれ、usernameと置き換えられます。これにより、SQLインジェクションを防ぐことができます。
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    #セキュリティのために、パスワードは決してデータベースへ平文で格納しない
                    #generate_password_hash()を使用してパスワードを安全にハッシュし、そのハッシュ値を格納する
                    (username, generate_password_hash(password)),
                )
                #generate_password_hash()ではデータを変更するため、変更を保存するためにdb.commit()を後で呼び出す必要がある
                db.commit()
            #もしusernameが既に存在している場合、sqlite3.IntegrityErrorが起こり、もう一つの検証エラーとしてユーザに示されるはずです。
            except db.IntegrityError:
                error = f"User {username} is already registered."
            #ユーザ情報を格納した後、ログインページへリダイレクト
            else:
                return redirect(url_for("auth.login"))

        #もし検証が失敗した場合は、エラーをユーザへ示します。flash()は、テンプレートを変換（render）するときに取得可能なメッセージを格納します。
        flash(error)
    #Blueprintのurl_prefixに'/auth'を設定したので、/registerの前に/authがついて/auth/registerにリクエストを受け取った際に、戻り値を返す
    return render_template('auth/register.html')

"""----------------------------------------------------Login-----------------------------------------------------------------------------------------------------------"""

@bp.route('/login', methods=('GET', 'POST'))
#＜login関数の定義＞
def login():
    if request.method == 'POST':# ユーザからのリクエストがPOSTだった場合
        username = request.form['username']
        password = request.form['password']
        db = get_db() # DBに接続
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):# パスワードが誤っていた場合(入力したパスワードをハッシュ化して比較)
            error = 'Incorrect password.'

        if error is None:# 何もエラーがなかった場合
            session.clear()
            session['user_id'] = user['id']# 問題がなければ新しいセッションににidを格納
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

"""--------------------------------------リクエスト毎にユーザがログイン状態か否かを判定---------------------------------------------------------------"""
#どのURLがリクエストされたかに関わらず、viewの関数の前に実行する関数を登録します
@bp.before_app_request
#＜load_logged_in_user関数の定義＞
def load_logged_in_user():
    user_id = session.get('user_id')#ユーザidがsessionに格納されているかチェック

    #もしユーザidが（セッションに）ない場合、もしくはそのidが（データベースに）存在しない場合、g.userはNoneになります。
    if user_id is None:
        g.user = None
    #データベースからユーザのデータを取得し、それをリクエストの期間中は存続するg.userへ格納
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

"""------------------------------------------------------logout-------------------------------------------------------------------------------------"""
#logoutではユーザidをsessionから取り除く必要があります。そうするとload_logged_in_userは以降のリクエストでユーザ情報を読み込まなくなります。
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

"""--------------------------------------------記事の投稿と削除のためのユーザのログイン状態について確認する--------------------------------------------------------------------------"""
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
