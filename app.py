from flask import Flask, render_template, request, redirect, url_for, make_response, abort
import os

app = Flask(__name__, static_url_path='/assets', static_folder='static')

with open("secret/keys.txt", 'r') as file:
    keys = [line.strip() for line in file]

def check_key(key):
    return len(key) == 20 and key.isalnum()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/createbot')
def create_bot():
    return render_template('createbot.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        key = request.form['key']
        if check_key(key) and key in keys:
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('key', key)
            return response
        else:
            return render_template('login.html', error='Invalid key. Note that keys must be exactly 20 characters and alphanumeric (must not contain special characters). If you forgot your key then email mail@sevenworks.eu.org for your key or a key data transfer.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        key = request.form['key']
        if check_key(key) and key not in keys:
            keys.append(key)
            with open("secret/keys.txt", 'a') as file:
                file.write('\n' + key)
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('key', key)
            return response
        else:
            return render_template('register.html', error='Invalid key or key is already registered. Note that keys must be exactly 20 characters and alphanumeric (must not contain special characters).')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'key' in request.cookies and request.cookies['key'] in valid_keys:
        cbf = os.path.join(os.path.dirname(__file__), 'secret', 'bots')
        list = []
        for keys in os.listdir("secret/bots/"):
            bots = os.path.join(cbf, keys)
            if os.path.isdir(bots):
                for name in os.listdir(bots):
                    bot = os.path.join(bots, name)
                    if os.path.isfile(bot) and name.endswith('.cbf'):
                        list.append({'name': name[:-4]})
        return render_template('dashboard.html', list=list)
    else:
        return redirect(url_for('login'))

@app.route('/bots/<string:name>')
def bots(name):
    key = request.cookies.get('key')
    if not os.path.isfile(os.path.join('secret', 'bots', key, f'{name}.cbf')):
        abort(404)
    return render_template('bots.html', name=name)

if __name__ == '__main__':
    app.run(debug=True)
