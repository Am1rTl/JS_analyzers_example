from functools import lru_cache
import subprocess
import requests as r
import re
from flask import Flask, json, render_template, jsonify, request
from format_logs import get_logs
from strace import update_files_actions
from rule_manager import RuleManager

app = Flask(__name__)

def get_extensions_list():
    result = subprocess.run(['code','--list-extensions'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    data = result.stdout
    return data

@lru_cache(maxsize=None)
def get_ext_info(ext):
    resp = r.get(f"https://marketplace.visualstudio.com/items?itemName={ext}")
    data = resp.text
    try:
        name = data.split("ux-item-name")[2].split(">")[1].split("<")[0]
    except:
        name = "Not found"
    try: 
        author = data.split("ux-item-publisher-link item-banner-focussable-child-item")[1].split(">")[1].split("<")[0]
    except:
        author = "Not found"
    
    try:    
        img = data.split("image-display")[1].split('src="')[1].split('"')[0]
    except:
        img = "Not found"

    # Получаем версию
    try:
        version = data.split('Version</td>')[1].split('">')[1].split('</td>')[0]
    except:
        version = "N/A"

    # Получаем рейтинг
    try:
        rating = data.split('average-rating">')[1].split('</span>')[0].strip()
        rating_count = data.split('rating-count">')[1].split('</span>')[0].strip()
    except:
        rating = "N/A"
        rating_count = "0"

    # Получаем количество установок
    try:
        installs = data.split('installs">')[1].split('</span>')[0].strip()
    except:
        installs = "N/A"

    # Получаем количество загрузок
    try:
        downloads = data.split('downloads">')[1].split('</span>')[0].strip()
    except:
        downloads = "N/A"

    return name, author, img, version, rating, rating_count, installs, downloads

@lru_cache(maxsize=None)
def get_ext_description(ext):
    resp = r.get(f"https://marketplace.visualstudio.com/items?itemName={ext}")
    data = resp.text
    pattern = r'<img src="https:\/\/[^"]+" alt="logo" width="200">'
    try:
        # Получаем полное описание из overview
        overview = data.split('class="overview selected-tab"')[1].split('<div class="itemDetails">')[1].split('<div class="markdown">')[1]
        overview = overview.split('</div>')[0]
        
        # Удаляем изображение иконки из описания
        if 'logo.png' in overview:
            overview = re.sub(pattern, '', overview)
        
        return "", overview
    except:
        return "Description not found", ""

@app.route('/get_ext_list', methods=['POST'])
def ext_list():
    ext_name = request.get_json().get('extensionName')
    resp = r.get(f"https://marketplace.visualstudio.com/search?term={ext_name}&target=VSCode&category=All%20categories&sortBy=Relevance")
    data = resp.text
    with open("resp.txt", 'x') as f:
        f.write(data)
    f.close()
    data = data.split('<span class="item-title" data-bind="text: title">')
    for i in range(0,len(data)):
        data[i] = data[i].split("<")[0]
    
    return jsonify(data)

@app.route('/')
def home():
    extensions = get_extensions_list()
    extensions = extensions.split("\n")
    extensions_ret = {}
    for ext in extensions:
        data = [get_ext_info(ext)]
        if "Not found" not in data[0]:
            extensions_ret[ext] = data
    return render_template('start.html', extensions=extensions_ret)

@app.route('/search_extension', methods=['POST'])
def search_extension():
    data = request.get_json()
    extension_name = data.get('extensionName')
    return jsonify({'message': f'Search for {extension_name} received.'})

@app.route('/about')
def about():
    return render_template('about_one.html')

@app.route('/install_extension/<ext_id>')
def install_extension(ext_id):
    try:
        result = subprocess.run(['code', '--install-extension', ext_id], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              text=True)
        if result.returncode == 0:
            return jsonify({"success": True, "message": "Extension installed successfully"})
        else:
            return jsonify({"success": False, "message": f"Installation failed: {result.stderr}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/about/<ext>')
def about_ext(ext):
    name, author, img, version, rating, rating_count, installs, downloads = get_ext_info(ext)
    short_description, overview = get_ext_description(ext)
    return render_template('about_one.html', 
                         id=ext, 
                         name=name, 
                         author=author, 
                         img=img, 
                         description=short_description,
                         overview=overview,
                         version=version,
                         rating=rating,
                         rating_count=rating_count,
                         installs=installs,
                         downloads=downloads)

@app.route('/rules')
def rules():
    return render_template('edir_rule.html')

@app.route('/logs')
def logs():
    update_files_actions()
    netw = '\n'.join(get_logs())
    with open("process_info.log", 'r') as f:
        log_data = f.read()
        f.close()
    with open("files_read.log", 'r') as f:
        read_files = f.read()
        f.close()
    with open("files_write.log", 'r') as f:
        write_files = f.read()
        f.close()
    return render_template('logs.html', log_data=log_data, netw=netw, read_files=read_files, write_files=write_files)

@app.route('/get_chart_data', methods=['GET'])
def get_chart_data():
    # Read data from process_info.log
    cpu_data = []
    memory_data = []
    with open('process_info.log', 'r') as f:
        for line in f.read().split("\n"):
            parts = line.split(' ')
            if len(parts) == 2:  # Assuming the format is known
                cpu_data.append(int(float(parts[0])))  # Assuming CPU usage is in the first column
                memory_data.append(int(float(parts[1])))
    return jsonify({'cpu': cpu_data, 'memory': memory_data})

@app.route('/set_rule', methods=['GET'])
def set_rule():
    return render_template("configure_rules.html")


@app.route("/save_data", methods=['POST'])
def save_data():
    data = request.json
    with open("rules", "w") as f:
        f.write(json.dumps(data))
    
    # Применить правила
    rule_manager = RuleManager()
    rule_manager.apply_rules()
    
    return "OK"

@app.route('/clear_rules')
def clear_rules():
    with open("rules", "w") as f:
        f.write("{}")
    return "OK"

@app.route('/get_saved_rules')
def get_rules():
    with open("rules", "r") as f:
        data = f.read()
    return data

if __name__ == '__main__':
    app.run(debug=True)
