from flask import Flask, render_template, jsonify, request, session, redirect, url_for
app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.dbsparta

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있음.
SECRET_KEY = 'apple'

import jwt
import datetime
import hashlib

## HTML을 주는 부분 ##
@app.route('/')
def home():
   return render_template('index.html')

@app.route('/login')
def login():
   return render_template('login.html')

@app.route('/register')
def register():
   return render_template('register.html')

@app.route('/mypage')
def mypage():
    return render_template('mypage.html')

## 로그인을 위한 API ##
# pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장.
@app.route('/api/register', methods=['POST'])
def api_register():
   id_receive = request.form['id_give']
   pw_receive = request.form['pw_give']
   pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

   # 아이디 중복 검사
   result = db.user.find_one({'id': id_receive})
   if result is not None:
      msg = 'Existing user ID. Choose another one.'
      return jsonify({'result': 'fail', 'msg': msg})
   else:
      db.user.insert_one({'id':id_receive,'pw':pw_hash})
      msg = 'Welcome to MyQuotes!'
      return jsonify({'result': 'success', 'msg': msg})

# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급.
@app.route('/api/login', methods=['POST'])
def api_login():
   id_receive = request.form['id_give']
   pw_receive = request.form['pw_give']

   pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
   result = db.user.find_one({'id':id_receive,'pw':pw_hash})

   # 동일한 유저 찾으면 JWT 토큰을 만들어 발급.
   if result is not None:
      payload = {
         'id': id_receive,
         'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
      }
      token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

      return jsonify({'result': 'success','token':token})
   # 찾지 못하면
   else:
      return jsonify({'result': 'fail', 'msg':'Wrong ID/Password'})

# [유저 정보 확인 API]
@app.route('/api/valid', methods=['GET'])
def api_valid():
   token_receive = request.headers['token_give']
   try:
      # token을 시크릿키로 디코딩.
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      # payload 안의 id로 유저정보를 찾습니다.
      userinfo = db.user.find_one({'id':payload['id']},{'_id':0})
      return jsonify({'result': 'success','userID':userinfo['id']})
   except jwt.ExpiredSignatureError:
      # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
      return jsonify({'result': 'fail', 'msg':'Login time exceeded.'})


@app.route('/api/mypage', methods=['GET'])
def api_mypage():
    token_receive = request.headers['token_give']
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
    quotes = list(db.quotes.find({'userID': userinfo['id']}, {'_id': 0}))

    return jsonify({'result': 'success', 'quotes': quotes})

## API 역할을 하는 부분
@app.route('/quote', methods=['POST'])
def write_quote():
    title = request.form.get('title')
    image = request.form.get('image')
    quote = request.form.get('quote')

    token = request.form.get('token')
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})

    doc = {'title': title, 'image': image, 'quote': quote, 'userID': userinfo['id']}
    db.quotes.insert_one(doc)

    return jsonify({'result': 'success', 'msg': 'Your quote is successfully posted!'})


@app.route('/quote', methods=['GET'])
def show_quotes():
    quotes = list(db.quotes.find({}, {'_id': 0}))
    return jsonify({'result': 'success', 'quotes': quotes})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)