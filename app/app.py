# -'-coding:utf-8-'-
import sys
import json
import datetime
from flask import Flask
from pymongo import MongoClient
from flask_restful import reqparse, abort, Api, Resource

#
from authlib.client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery
import google_auth
from setConfigure import set_secret

set_secret(__name__)

#


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
api = Api(app)

app.secret_key = getattr(sys.modules[__name__], 'FN_FLASK_SECRET_KEY')
app.register_blueprint(google_auth.app)


# 구글 연동용으로 카피해놓은 코드. 실제 프로젝트 무관
@app.route('/')
def index():
    if google_auth.is_logged_in():
        user_info = google_auth.get_user_info()
        return '<div>You are currently logged in as ' + user_info['given_name'] + '<div><pre>' + json.dumps(user_info,
                                                                                                            indent=4) + "</pre>"
    return 'You are not currently logged in.'


# json 쪼개는 로직
parser = reqparse.RequestParser()
parser.add_argument('task')
parser.add_argument('email')
parser.add_argument('comment')
parser.add_argument('problem_id')

# ________________________참고 구현체 _______________________

TODOS = {
    'todo1': {'task': 'Make Money'},
    'todo2': {'task': 'Play PS4'},
    'todo3': {'task': 'Study!'},
}


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

class CommentList(Resource):
    def get(self, problem_id):
        result = commentsCollections.find_all({"problem_id": problem_id})
        return TODOS


class Comment(Resource):
    def post(self):
        args = parser.parse_args()
        comment = {
            "email": args.email,
            "problem_id": args.problem_id,
            "comment": args.comment,
            "day": datetime.datetime.utcnow()}
        result_id = commentsCollections.insert_one(comment).inserted_id
        obj = {"_id": str(result_id)}
        return json.dumps(obj), 201


# 이번 구현목표
class Problem(Resource):
    def get(self, problem_id):
        result = problemsCollections.find_all({"problem_id": problem_id})
        return TODOS

    def post(self):
        return "good!"


class ProblemMain(Resource):
    def GET(self):
        return "good!"


class ProblemSearch(Resource):
    def GET(self):
        return "good!"


class ProblemSolution(Resource):
    def POST(self):
        return "good!"


class ProblemEvalation(Resource):
    def POST(self):
        return "good!"


# URL Router에 맵핑한다.(Rest URL정의)
api.add_resource(TodoList, '/todos/')
api.add_resource(Todo, '/todos/<string:todo_id>')

# comments _ POST
api.add_resource(Comment, '/comments/')
# comments _ GET
api.add_resource(CommentList, '/comments/<string:problem_id>')

# problem _ GET
api.add_resource(ProblemMain, '/problems/main')
api.add_resource(ProblemSearch, '/problems/search/<string:tag_word>')
api.add_resource(Problem, '/problems/<string:problem_id>')
# problem _ POST
api.add_resource(ProblemSolution, '/problems/solution')
api.add_resource(ProblemEvalation, '/problems/evalation')
api.add_resource(Problem, '/problems/')

# 서버 실행
if __name__ == '__main__':
    app.run(debug=True, port=8000)
