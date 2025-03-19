from functools import lru_cache
import subprocess
import requests as r
from flask import Flask, render_template, jsonify, request
from format_logs import get_logs

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

    return name, author, img


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

@app.route('/about/<ext>')
def about_ext(ext):
    name, author, img = get_ext_info(ext)
    return render_template('about_one.html', id=ext, name=name, author=author, img=img)

@app.route('/rules')
def rules():
    return render_template('edir_rule.html')

@app.route('/logs')
def logs():
    log_data = '\n'.join(get_logs())
    return render_template('logs.html', log_data=log_data)

if __name__ == '__main__':
    app.run(debug=True)
