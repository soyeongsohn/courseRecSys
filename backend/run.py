from flask import Flask, request, render_template, url_for, flash
from server.forms import UserLoginForm
from werkzeug.utils import redirect
from model.sugang_info import login, logout
from model.course_rec import final_result
import os


template_path = os.path.abspath('../frontend/templates')
static_path = os.path.abspath('../frontend/static')

app = Flask(__name__, template_folder=template_path, static_folder=static_path)
app.config['SECRET_KEY'] = "../secret_key.txt"


@app.route('/', methods=['GET'])
def home(name=None):
    return render_template('index.html', name=name)


@app.route('/', methods=['GET'])
def do_logout():
    logout()
    return render_template('index.html')


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


@app.route('/result', methods=['GET'])
def result(name=None):
    df = final_result()
    if df is not None:
        return render_template('result.html', name=name, tables=[df.to_html(classes='data', index=False).replace('text-align: right;', 'text-align: center;')],  titles=None)
    else:
        return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
