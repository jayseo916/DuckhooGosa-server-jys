# -'-coding:utf-8-'-
import sys
import json
import datetime
import pprint
from flask import Flask, session, request
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_restful import reqparse, abort, Api, Resource
from util import getFileNameFromLink
from scheduleModule import imageScheduleQueue
from oauth2client.contrib.flask_util import UserOAuth2
from requests import get
from functools import wraps
from flask_cors import CORS, cross_origin
import logging

import schedule
import time

# import google.oauth2.credentials
# import googleapiclient.discovery
# import google_auth

from setConfigure import set_secret

set_secret(__name__)

# 환경변수 로드
conf_host = getattr(sys.modules[__name__], 'DB-HOST')
conf_user = getattr(sys.modules[__name__], 'DB-USER')
conf_password = getattr(sys.modules[__name__], 'DB-PASSWORD')

connection = MongoClient(conf_host,
                         username=conf_user,
                         password=conf_password,
                         authSource="duck",
                         authMechanism='SCRAM-SHA-256')

db = connection.duck

# 테스트용 스키마
tool = db.tool
posts = db.posts
# 실제 사용 스키마
commentsCollections = db.comments
problemsCollections = db.problems

app = Flask(__name__)
app.config['TESTING'] = False

cors = CORS(app, origins=["http://localhost:3000"], headers=['Content-Type'],
            expose_headers=['Access-Control-Allow-Origin'], supports_credentials=True)
api = Api(app)
logging.getLogger('flask_cors').level = logging.DEBUG


# # 로그인할때 세션에 집어넣어음.
@app.route('/*', methods=['OPTION'])
def option():
    print("옵션 전체 도메인")
    return "GOOD"


def login_required():
    def _decorated_function(f):
        @wraps(f)
        def __decorated_function(*args, **kwargs):
            print(session, "세션 체크")
            if 'logged_in' in session:
                print("로그인 통과")
                return f(*args, **kwargs)
            else:
                print("세션없음")
                return "NO SESSION ERROR"

        return __decorated_function

    return _decorated_function


@app.route('/login/', methods=['POST', 'OPTION'])
def Login():
    if 'access_token' in request.headers:
        access_token = request.headers['access_token']
        data = get("https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=" + access_token).json()
        if 'user_id' in data:
            email = data['email']
            session['logged_in'] = True
            session['email'] = email
            print("로그인 세션입력됨", session)
            return {'result': True}
        else:
            session.clear()
            return {'result': False, "reason": "Token is not validate"}
    else:
        return {"result": False, "reason": "Req didn't has token"}


@app.route('/logout/', methods=['POST', 'OPTION'])
@login_required()
def Logout():
    print("로그아웃 SEQ", session)
    session.clear()
    return {'result': True}


# app.secret_key = getattr(sys.modules[__name__], 'FN_FLASK_SECRET_KEY')
# app.register_blueprint(google_auth.app)

# json 쪼개는 로직
parser = reqparse.RequestParser()
parser.add_argument('task')
parser.add_argument('email')
parser.add_argument('comment')
parser.add_argument('problem_id')
parser.add_argument('id')
parser.add_argument('representImg')
parser.add_argument('next_problem')
parser.add_argument('load_count')
parser.add_argument('word')
parser.add_argument('genre')

# ________________________참고 구현체 _______________________


def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        abort(404, message="Todo {} doesn't exist".format(todo_id))


class Todo(Resource):
    def get(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        return TODOS[todo_id]

    def delete(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        del TODOS[todo_id]
        return '', 204

    def put(self, todo_id):
        args = parser.parse_args()
        task = {'task': args['task']}
        TODOS[todo_id] = task
        return task, 201


class TodoList(Resource):
    def get(self):
        pprint.pprint(TODOS)
        return TODOS

    def post(self):
        args = parser.parse_args()
        todo_id = 'todo%d' % (len(TODOS) + 1)
        TODOS[todo_id] = {'task': args['task']}
        return TODOS[todo_id], 201


# __________________________________________________
@app.route("/")
def helloroute():
    return "hello"


class CommentList(Resource):
    @login_required()
    def get(self, problem_id):
        result = commentsCollections.find_all({"problem_id": problem_id})
        return result


class Comment(Resource):
    @login_required()
    def post(self):
        args = parser.parse_args()
        comment = {
            "email": args.email,
            "problem_id": args.problem_id,
            "comment": args.comment,
            "day": datetime.datetime.utcnow()}
        result_id = commentsCollections.insert_one(comment).inserted_id
        obj = {"_id": str(result_id)}
        return json.dumps(obj)


class ProblemGet(Resource):
    @login_required()
    def get(self, problem_id):
        result = problemsCollections.find_one(ObjectId(problem_id))
        result['_id'] = str(result['_id'])
        return result


class Problem(Resource):
    @login_required()
    def post(self):
        args = parser.parse_args()
        obj = {"link": args['representImg'], "filename": getFileNameFromLink(args['representImg'])}
        imageScheduleQueue.append(obj)
        content = request.get_json()
        pprint.pprint(content)
        result_id = problemsCollections.insert_one(content).inserted_id
        obj = {"_id": str(result_id)}
        return json.dumps(obj)

class ProblemMain(Resource):
    def post(self):
        args = parser.parse_args()
        count = problemsCollections.count()
        if count < int(args['next_problem']):
            return json.dumps([])
        sortedproblem = problemsCollections.find().sort('date', -1).skip(int(args['next_problem']))\
            .limit(5)
        result = []
        for v in sortedproblem:
            v['_id'] = str(v['_id'])
            result.append(v)
        return json.dumps(result)

    @login_required()
    def GET(self):
        return "good!"


class ProblemSearch(Resource):     #제목 OR 검색
    # @login_required()
    def post(self):
        args = parser.parse_args()
        problemsCollections.drop_index('*')
        count = problemsCollections.count()
        word = args['word']
        if count < int(args['next_problem']):
            return json.dumps([])
        problemsCollections.create_index([('title', 'text')])
        sortedproblem = problemsCollections.find({"$text": {"$search": word}}).sort('date', -1).skip(int(args['next_problem'])) \
            .limit(5)
        result = []
        for v in sortedproblem:
            v['_id'] = str(v['_id'])
            result.append(v)
        return json.dumps(result)

class ProblemGenre(Resource):     #장르검색
    # @login_required()
    def post(self):
        args = parser.parse_args()
        problemsCollections.drop_index('*')
        count = problemsCollections.count()
        word = args['genre']
        print('인덱스', problemsCollections.index_information())
        print(word)
        print(type(word))
        if count < int(args['next_problem']):
            return json.dumps([])
        problemsCollections.create_index([('genre', 'text')])
        sortedproblem = problemsCollections.find({"$text": {"$search": word}}).sort('date', -1).skip(int(args['next_problem'])) \
            .limit(5)
        result = []
        for v in sortedproblem:
            v['_id'] = str(v['_id'])
            result.append(v)

        return json.dumps(result)





# class ProblemSearch(Resource):     #제목 and 검색
#     # @login_required()
#     def post(self):
#         args = parser.parse_args()
#         # count = problemsCollections.count()
#         count = 13
#         word = args['word']
#         start = int(args['start'])
#         listword = word.split()
#         if count < int(args['next_problem']):
#             return json.dumps([])
#         problemsCollections.create_index([('title', 'text')])
#         # 검색
#         array = []
#         flag = 1
#         add = 0  #더한 갯수
#         while start < count or len(array) < 3:
#             sortedproblem = list(problemsCollections.find({"$text": {"$search": listword[0]}}).sort('date', -1).skip(start).limit(start + 10))
#             for problem in enumerate(sortedproblem):   #한개씩 살펴볼 문제
#                 for word in enumerate(listword):  #존재해야 하는 단어 목록
#                     if word[1] not in problem[1]['title']:
#                         flag = 0
#                         print('타이틀', problem[1]['title'])
#                         print('검색단어', word[1])
#                         break
#                 if flag is 0:
#                     continue
#                 else:
#                     print('넣을문제', problem[1])
#                     add = problem[0] + 1
#                     array.append(problem[1])
#
#                 if len(array) is 3:
#                     break
#
#             if len(array) is 3:
#                 start = start + add
#                 break
#             else:
#                 start = start + 10
##################################################################
#         print(array)
#
#         # sortedproblem.create_index([('title', 'text')])
#         # listword.remove(listword[0])
#         # for x in listword:
#         #     sortedproblem = sortedproblem.collation({"$text": {"$search": x}})
#
#         # sortedproblem.sort('date', -1).skip(int(args['next_problem'])).limit(3)
#         result = []
#         # for v in sortedproblem:
#         #     v['_id'] = str(v['_id'])
#         #
#         #     result.append(v)
#         return json.dumps(result)


class ProblemSolution(Resource):
    @login_required()
    def POST(self):
        return "good!"


class ProblemEvalation(Resource):
    @login_required()
    def POST(self):
        return "good!"


# URL Router에 맵핑한다.(Rest URL정의)

# comments _ POST
api.add_resource(Comment, '/comment')
# comments _ GET
api.add_resource(CommentList, '/comment/<string:problem_id>')

# problem _ POST
api.add_resource(ProblemMain, '/problem/main')
api.add_resource(ProblemSearch, '/problem/search')
api.add_resource(ProblemGenre, '/problem/genre')

# problem _ POST
api.add_resource(ProblemSolution, '/problem/solution')
api.add_resource(ProblemEvalation, '/problem/evalation')


# problem - GET, POST
api.add_resource(ProblemGet, '/problem/<string:problem_id>')
api.add_resource(Problem, '/problem')

# 서버 실행
if __name__ == '__main__':
    app.secret_key = getattr(sys.modules[__name__], 'FN_FLASK_SECRET_KEY')
    app.run(debug=True, port=8000)
    print("앱켜짐")
