from flask import Flask, render_template, request, redirect, url_for, make_response, abort, send_file, jsonify
import os, shutil, threading
from zipfile import ZipFile

app = Flask(__name__, static_url_path='/assets', static_folder='static')

with open("secret/keys.txt", 'r') as file: keys = [line.strip() for line in file]
def check_key(key): return len(key) == 20 and key.isalnum() and ' ' not in key
def check_name(name): return name.isalnum() and ' ' not in name
def clean_tmp(): os.system("python clean.py")
threading.Thread(target=clean_tmp).start()

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

def read_pycbf(key, name):
    bot = os.path.join('secret', 'bots', key, f'{name}.pycbf')
    if os.path.exists(bot):
        with open(bot, 'r') as file:
            cbf = file.read()
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
                file.write(key + '\n')
            os.makedirs(os.path.join(os.path.dirname(__file__), 'secret', 'bots', f'{key}'), exist_ok=True)
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('key', key)
            return response
        else:
            return render_template('register.html', error='Invalid key or key is already registered. Note that keys must be exactly 20 characters and alphanumeric (must not contain special characters).')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'key' in request.cookies and request.cookies['key'] in keys:
        key = request.cookies['key']
        bot_list = []
        bot_dir = os.path.join(os.path.dirname(__file__), 'secret', 'bots', key)
        if os.path.exists(bot_dir):
            for name in os.listdir(bot_dir):
                if name.endswith('.cbf'):
                    bot_list.append({'name': name[:-4]})
                elif name.endswith('.pycbf'):
                    bot_list.append({'name': name[:-6]})
                else:
                    pass
        template_dir = os.path.join(os.path.dirname(__file__), 'secret', 'templates')
        templates = [{'name': name[:-4]} for name in os.listdir(template_dir) if name.endswith('.cbf')]
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
        bottype = request.form.get('cbftype', 'cbf')
        if not check_name(botname):
            return render_template('createbot.html', error='Invalid bot name. Bot name must be alphanumeric and not contain spaces.')
        botdir = os.path.join('secret', 'bots', key)
        botfile = os.path.join(botdir, f'{botname}.{bottype}')
        botext = [f[:-4] for f in os.listdir(os.path.join('secret', 'bots', key)) if f.endswith('.cbf')]
        if botname in botext:
            return render_template('createbot.html', error='Bot already exists in your key by that name.')
        if 'cbf' in botext or 'pycbf' in botext:
            return render_template('createbot.html', error='Bot with the same name already exists under different type.')
        with open(botfile, 'a') as f:
            pass
        if bottype == "pycbf":
            with open(botfile, 'w') as f:
                f.write("def bot():\n    comment = read()\n    if comment == '/test':\n        reply('It works!', '0')\n    elif comment == '/hello':\n        reply('Hello!', '0')\n    else:\n        pass\n\nwhile True:\n    bot()\n    time.sleep(2)")
        return redirect(url_for('dashboard'))
    return render_template('createbot.html', error=None)

@app.route('/bots/<string:name>')
def bots(name):
    key = request.cookies.get('key')
    if key not in keys:
        abort(403)
    if os.path.isfile(os.path.join('secret', 'bots', key, f'{name}.cbf')):
        bottype = 'cbf'
        cbf = read_cbf(key, name)
    elif os.path.isfile(os.path.join('secret', 'bots', key, f'{name}.pycbf')):
        bottype = 'pycbf'
        cbf = read_pycbf(key, name)
    else:
        abort(404)
    return render_template('bots.html', name=name, key=key, cbf=cbf, bottype=bottype)

@app.route('/download/<string:key>/<path:file>')
def download(key, file):
    if request.cookies.get('key') != key:
        abort(403)
    try:
        return send_file(f'secret/bots/{key}/{file}', as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route('/savebot/<string:name>', methods=['POST'])
def savebot(name):
    key = request.cookies.get('key')
    if os.path.isfile(os.path.join('secret', 'bots', key, f'{name}.cbf')):
        bot = os.path.join('secret', 'bots', key, f'{name}.cbf')
    elif os.path.join('secret', 'bots', key, f'{name}.pycbf'):
        bot = os.path.join('secret', 'bots', key, f'{name}.pycbf')
    else:
        abort(404)
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
    botdir = os.path.join(os.path.dirname(__file__), 'secret', 'bots', key)
    if not os.path.exists(template):
        abort(404)
    bot = os.path.join(botdir, f'{name}.cbf')
    shutil.copyfile(template, bot)
    return redirect(url_for('dashboard'))

@app.route('/build/<string:key>/<string:name>', methods=['POST'])
def build(key, name):
    a, b, c = os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), 'secret', 'bots'), os.path.join(os.path.dirname(__file__), 'build', name)
    cbffile = os.path.join(b, key, f'{name}.cbf')
    if not os.path.exists(cbffile):
        return "Bot not found", 404
    os.makedirs(c, exist_ok=True)
    runner = ['cbf.exe', 'run.bat']
    for file in runner:
        runnerdir, tmpdir = os.path.join(a, 'secret', 'runner', file), os.path.join(c, f'{file}')
        os.makedirs(os.path.dirname(tmpdir), exist_ok=True)
        if os.path.exists(runnerdir):
            shutil.copy(runnerdir, tmpdir)
    shutil.copy(cbffile, os.path.join(c, 'bot.cbf'))
    conf = "\n".join(f"{field}->{request.form.get(field)}" for field in ['username', 'password', 'levelID', 'prefix', 'wait'])
    with open(os.path.join(c, 'cbf.config'), 'w') as lol:
        lol.write(conf)
    buildzip = os.path.join(a, 'build', f'{name}_build.zip')
    zipfolder = f'{name}'
    with ZipFile(buildzip, 'w') as z:
        for zfolder, _, zfiles in os.walk(c):
            for zfile in zfiles:
                zpath = os.path.join(zfolder, zfile)
                yooo = os.path.relpath(zpath, c)
                zipfiles = os.path.join(zipfolder, yooo)
                z.write(zpath, zipfiles)
    shutil.rmtree(c)
    return send_file(buildzip, as_attachment=True, download_name=f'{name}_build.zip')

@app.route('/pybuild/<string:key>/<string:name>', methods=['POST'])
def pybuild(key, name):
    a, b, c = os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), 'secret', 'bots'), os.path.join(os.path.dirname(__file__), 'build', name)
    cbffile = os.path.join(b, key, f'{name}.pycbf')
    if not os.path.exists(cbffile):
        return "Bot not found", 404
    os.makedirs(c, exist_ok=True)
    runner = ['pycbf.exe', 'run_py.bat']
    for file in runner:
        runnerdir, tmpdir = os.path.join(a, 'secret', 'runner', file), os.path.join(c, f'{file}')
        os.makedirs(os.path.dirname(tmpdir), exist_ok=True)
        if os.path.exists(runnerdir):
            shutil.copy(runnerdir, tmpdir)
    shutil.copy(cbffile, os.path.join(c, 'bot.pycbf'))
    conf = "\n".join(f"{field}->{request.form.get(field)}" for field in ['username', 'password', 'levelID'])
    with open(os.path.join(c, 'cbf.config'), 'w') as lol:
        lol.write(conf)
    buildzip = os.path.join(a, 'build', f'{name}_build.zip')
    zipfolder = f'{name}'
    with ZipFile(buildzip, 'w') as z:
        for zfolder, _, zfiles in os.walk(c):
            for zfile in zfiles:
                zpath = os.path.join(zfolder, zfile)
                yooo = os.path.relpath(zpath, c)
                zipfiles = os.path.join(zipfolder, yooo)
                z.write(zpath, zipfiles)
    shutil.rmtree(c)
    return send_file(buildzip, as_attachment=True, download_name=f'{name}_build.zip')

if __name__ == '__main__':
    app.run(debug=True)
