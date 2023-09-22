import os

from flask import Flask

#＜create_app関数の定義＞
def create_app(test_config=None):
    #Flaskのインスタンス化、インスタンス変数appの作成
    app = Flask(__name__, instance_relative_config=True)
    #appが使用する標準設定をいくつか設定します
    app.config.from_mapping(
        #SECRET_KEYの設定
        SECRET_KEY='dev',
        #app.instance_pathに入った場所とflaskr.sqliteを結合したパスを作成
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # もしinstanceフォルダにconfig.pyファイルがあれば、値をそこから取り出して、標準設定を上書きします。
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # instanceディレクトリ作成をtryし、ディレクトリが存在しない場合は作成、既に存在している場合は例外が発生しpassされる
    try:
        os.makedirs(app.instance_path)
    except OSError:
        #例外をキャッチしても特に何も処理を行わずにスルー
        pass

    # helloという単純なページの作成
    @app.route('/hello')
    #＜hello関数の定義＞
    def hello():
        return 'Hello, World!'
    
    #db.pyのinit_app関数が呼び出される。
    from . import db      #db.pyをimport
    db.init_app(app)

    
    from . import auth    #aurh.pyをimport
    #app.register_blueprint()の引数にBlueprint名.bpを指定するとアプリケーションに登録することができます
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    return app