import sqlite3

#clickモジュールをインポートすることで、独自のflaskコマンドを作成することが出来ます。
import click
from flask import current_app
from flask import g
"""-----------------------------------------------------------メモ-----------------------------------------------------------------------
・appはFlaskのインスタンスである
・カラムとはデータベースに入っているデータの「項目」のこと
・Python のプログラムは、コマンドラインから直接呼ばれるか、import文で他のプログラムから参照されて呼ばれます。その区別を__name__で行うことができます。
→つまり、if __name__ == '__main__':＜でコマンドラインから直接呼ばれた場合の処理を記述する＞
--------------------------------------------------------------------------------------------------------------------------------------"""

#＜get_db関数の定義＞
def get_db():
    """「g」はリクエスト毎に生成されるユニークなオブジェクトとなります。
      つまりリクエストの中で初めてDB接続要求があった場合、新たにDBコネクションを生成し、
      同じリクエストの中で複数回接続要求があった場合、最初に生成したオブジェクトを使いまわします。
    """
    if "db" not in g:
        #sqlite3.connectによって、current_app.config['DATABASE']で取得した、'DATABASE'キーに設定されたデータベースに接続します。
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
            # ↑ 現在実行しているFlaskアプリケーションの設定値'DATABASE'を取り出します。
            #  appを自分のプロジェクトのモジュール内でimportすると、循環importの問題に陥りやすくなるため直接参照するのではなく、その時点の活動を処理しているアプリケーションを指すプロキシになるcurrent_appを使用できます。
            # ↑ detect_typesをsqlite3.PARSE_DECLTYPESとしておくことで、戻り値のカラムの型を読み取ることが出来るようになります。
        )
        g.db.row_factory = sqlite3.Row
        # ↑ row_factoryにsqlite3.Rowをセットしておくことで、問い合わせの結果にカラム名でアクセス出来るようになります。

    return g.db
#＜close_db関数の定義＞gオブジェクトから'db'を取り出し、それが空でなければ（接続があれば）、切断します。
def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()

#＜init_db関数の定義＞get_dbのインスタンス化、インスタンス変数dbの作成？
def init_db():
    db = get_db()

    #open_resource()でflaskrディレクトリ内のファイルを開きます。そして次の行で開いたファイルをutf-8でデコードして読み込み実行します。
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


#ターミナルで「init-db」と入力されたら　　　　　　　　　　　　　　　　　　　※click.command()は、ターミナルから使用できるコマンドを定義する
@click.command("init-db")
#＜init_db_command関数の定義＞init_db関数を実行して、「Initialized the database.」と表示する
def init_db_command():
    init_db()
    click.echo("Initialized the database.")


#＜init_app関数の定義＞close_db関数とinit_db_command関数をアプリケーションに登録する
def init_app(app):
    #teardown_appcontext関数は、レスポンスを返した後に自動的に引数の関数を呼び出します。
    app.teardown_appcontext(close_db)
    #app.cli.add_commandにinit_db_commandをセットすることで、flaskコマンドから呼び出すことが出来るようになります。
    app.cli.add_command(init_db_command)

"""---------------------------「flask --app flaskr init-db」を打ち込んだ際の挙動を示すと以下のような順で処理が進みます----------------------
1.  __init__.pyが起動し、create_appメソッドが呼び出される。
2.  db.pyモジュールのinit_appメソッドが呼び出される。
3.  __init__.pyの処理が終了後、'init-db'コマンドと紐づけられたinit_db_commandが呼び出される
4.  init_db_commandメソッドからinit_dbメソッドが呼び出され、データベースの接続と、schema.sqlの実行が行われる。
5.  init_dbメソッドの処理が終了すると、文字列'Initialized the database.'が出力され、DB接続を切断し終了。
--------------------------------------------------------------------------------------------------------------------------------------"""