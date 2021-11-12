from flask import Flask, request, render_template

import os


template_path = os.path.abspath('../../frontend/templates')
static_path = os.path.abspath('../../frontend/static')

app = Flask(__name__, template_folder=template_path, static_folder=static_path)



@app.route('/', methods=['GET'])
def home(name=None):
    return render_template('index.html', name=name)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
# if request.method == 'POST':
# do_the_login()
# else:
# show_the_login_form()


# @app.route('/result/<stdno>', methods=['GET'])
#     def result(stdno):


if __name__ == "__main__":
    app.run()