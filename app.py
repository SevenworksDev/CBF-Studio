from flask import Flask, render_template, request, redirect, url_for, make_response, abort, send_file, jsonify
from shutil import copyfile
import os

app = Flask(__name__, static_url_path='/assets', static_folder='static')

with open("secret/keys.txt", 'r') as file:
    keys = [line.strip() for line in file]

def check_key(key):
    return len(key) == 20 and key.isalnum()

def check_name(name):
    return name.isalnum() and ' ' not in name

def read_cbf(key, name):
    bot = os.path.join('secret', 'bots', key, f'{name}.cbf')

    if os.path.exists(bot):
        with open(bot, 'r') as file:
            cbf = file.read()
        if not cbf.strip():
            tutorial = os.path.join('secret', 'tutorial.txt')
            with open(tutorial, 'r') as t:
                return t.read()
        return cbf
    else:
        return None

@app.route('/')
def home():
    return render_template('index.html')

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
            os.system(f"mkdir secret/bots/{key}")
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('key', key)
            return response
        else:
            return render_template('register.html', error='Invalid key or key is already registered. Note that keys must be exactly 20 characters and alphanumeric (must not contain special characters).')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'key' in request.cookies and request.cookies['key'] in keys:
        cbf = os.path.join(os.path.dirname(__file__), 'secret', 'bots')
        bot_list = []
        templates = []

        for bot_dir in os.listdir("secret/bots/"):
            bots = os.path.join(cbf, bot_dir)
            if os.path.isdir(bots):
                for name in os.listdir(bots):
                    bot = os.path.join(bots, name)
                    if os.path.isfile(bot) and name.endswith('.cbf'):
                        bot_list.append({'name': name[:-4]})

        template = os.path.join(os.path.dirname(__file__), 'secret', 'templates')
        for tname in os.listdir(template):
            tfile = os.path.join(template, tname)
            if os.path.isfile(tfile) and tname.endswith('.cbf'):
                templates.append({'name': tname[:-4]})

        return render_template('dashboard.html', bots=bot_list, templates=templates)
    else:
        return redirect(url_for('login'))

@app.route('/createbot', methods=['GET', 'POST'])
def create_bot():
    if request.method == 'POST':
        key = request.cookies.get('key')

        if key not in keys:
            abort(403)

        botname = request.form['botname']
        cbf = request.form.get('cbftype', 'cbf')

        if not check_name(botname):
            return render_template('createbot.html', error='Invalid bot name. Bot name must be alphanumeric and not contain spaces.')

        botdir = os.path.join('secret', 'bots', key)
        botfile = os.path.join(botdir, f'{botname}.cbf')

        if os.path.isfile(botfile):
            return render_template('createbot.html', error='Bot already exists in your key by that name.')

        with open(botfile, 'a') as f:
            pass

        return redirect(url_for('dashboard'))
    return render_template('createbot.html', error=None)

@app.route('/bots/<string:name>')
def bots(name):
    key = request.cookies.get('key')
    cbf = read_cbf(key, name)

    if key not in keys:
        abort(403)

    if not os.path.isfile(os.path.join('secret', 'bots', key, f'{name}.cbf')):
        abort(404)

    return render_template('bots.html', name=name, key=key, cbf=cbf)

@app.route('/download/<string:key>/<path:file>')
def download(key, file):
    if request.cookies.get('key') != key:
        abort(403)
    else:
        dir = f'secret/bots/{key}/{file}'
        if not dir.startswith('secret/bots/'):
            abort(403)
        try:
            return send_file(dir, as_attachment=True)
        except FileNotFoundError:
            abort(404)

@app.route('/savebot/<string:name>', methods=['POST'])
def savebot(name):
    key = request.cookies.get('key')
    bot = os.path.join('secret', 'bots', key, f'{name}.cbf')

    if key not in keys:
        abort(403)

    try:
        content = request.json['content']
        with open(bot, 'w') as file:
            file.write(content)
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': 'Error saving bot'}), 500

@app.route('/deletebot/<string:name>')
def delete_bot(name):
    key = request.cookies.get('key')

    if key not in keys:
        abort(403)

    botdir = os.path.join('secret', 'bots', key)
    for file in os.listdir(botdir):
        if file.startswith(name):
            bot = os.path.join(botdir, file)
            os.remove(bot)

    return redirect(url_for('dashboard'))

@app.route('/templates/<string:name>')
def templates(name):
    key = request.cookies.get('key')

    if key not in keys:
        abort(403)

    template = os.path.join(os.path.dirname(__file__), 'secret', 'templates', f'{name}.cbf')
    bot = os.path.join(os.path.dirname(__file__), 'secret', 'bots', key)

    if not os.path.exists(template):
        abort(404)

    botdir = os.path.join(bot, f'{name}.cbf')
    copyfile(template, botdir)

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
