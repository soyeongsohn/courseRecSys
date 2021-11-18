from flask import Flask, request, render_template, url_for, flash
from forms import  UserLoginForm
from werkzeug.utils import redirect
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
    form = UserLoginForm()
    if request.method == 'POST':
        if len(form.username.data) == 0:
            error = "아이디를 입력해주세요"
            flash(error)
        if len(form.password.data) == 0:
            error = "비밀번호를 입력해주세요"
            flash(error)
        elif login(form.username.data, form.password.data):
            return redirect(url_for('result'))

    return render_template('login.html', form=form)


@app.route('/result', methods=['GET'])
def result(name=None):
    # 결과 어떻게 출력할건지?
    return render_template('result.html', name=name)


if __name__ == "__main__":
    app.run()