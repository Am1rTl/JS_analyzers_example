import subprocess
import requests as r
from flask import Flask, render_template, jsonify

app = Flask(__name__)

def get_extensions_list():
    result = subprocess.run(['code','--list-extensions'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    data = result.stdout
    return data



@app.route('/get_ext_list')
def ext_list():
    extension_list = get_extensions_list()
    extension_list = extension_list.split("\n")
    return jsonify(extension_list)

@app.route('/')
def home():
    return render_template('start.html')

@app.route('/about')
def about():
    return render_template('about_one.html')

@app.route('/about/<ext>')
def about_ext(ext):
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
    return render_template('about_one.html', id=ext, name=name, author=author, img=img)

@app.route('/rules')
def rules():
    return render_template('edir_rule.html')

if __name__ == '__main__':
    app.run(debug=True)
