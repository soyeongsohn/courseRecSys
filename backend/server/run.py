from flask import Flask, request, render_template, url_for, flash
from forms import UserLoginForm
from werkzeug.utils import redirect
from selenium.common.exceptions import UnexpectedAlertPresentException
from model.sugang_info import login, logout
from model.course_rec import top_n
import os


template_path = os.path.abspath('../../frontend/templates')
static_path = os.path.abspath('../../frontend/static')

app = Flask(__name__, template_folder=template_path, static_folder=static_path)
app.config['SECRET_KEY'] = "../../secret_key.txt"


@app.route('/', methods=['GET'])
def home(name=None):
    return render_template('index.html', name=name)


@app.route('/login', methods=['GET', 'POST'])
def do_login():
    succeed = True
    form = UserLoginForm()
    if request.method == 'POST':
        username = form.username.data
        password = form.password.data
        succeed = login(username, password)
        if succeed == False:
            flash("로그인 정보가 잘못되었습니다.")
            return redirect(url_for('do_login'))
        return redirect(url_for('result'))

    return render_template('login.html', form=form)


"""
해야할 일
1. 로그인 중 로딩 페이지 뜨게 만들기
2. 로그인 실패 시 알림창 뜨게 만들기
3. 결과 페이지에 나가기 버튼 만들고, 나가기 버튼 누르면 로그아웃 함수 실행하고, 페이지 닫게 만들어보기
"""


@app.route('/result', methods=['GET'])
def result(name=None):
    # 결과 어떻게 출력할건지?
    df = top_n()
    return render_template('result.html', name=name, tables=[df.to_html(classes='data')],  titles=df.columns.values)


if __name__ == "__main__":
    app.run()