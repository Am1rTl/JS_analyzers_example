import subprocess
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

@app.route('/rules')
def rules():
    return render_template('edir_rule.html')

if __name__ == '__main__':
    app.run(debug=True)
