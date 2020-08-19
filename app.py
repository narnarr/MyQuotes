from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbsparta


## HTML을 주는 부분
@app.route('/')
def home():
    return render_template('index.html')

## API 역할을 하는 부분
@app.route('/quote', methods=['POST'])
def write_quote():
    title = request.form.get('title')
    image = request.form.get('image')
    quote = request.form.get('quote')

    doc = {'title': title, 'image': image, 'quote': quote}
    db.quotes.insert_one(doc)

    return jsonify({'result': 'success', 'msg': '성공적으로 저장되었습니다!'})


@app.route('/quote', methods=['GET'])
def show_quotes():
    quotes = list(db.quotes.find({}, {'_id': 0}))
    return jsonify({'result': 'success', 'quotes': quotes})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)