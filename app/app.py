# -'-coding:utf-8-'-
import os
import pprint
import sys
import datetime
from flask import Flask
from pymongo import MongoClient
import json

from flask_restful import reqparse, abort, Api, Resource

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRETS_PATH = os.path.join(BASE_DIR + '/app/secret.json')
secrets = json.loads(open(SECRETS_PATH).read())
print(secrets, "기본 상태 조회")
for key, value in secrets.items():
    setattr(sys.modules[__name__], key, value)

conf_host = getattr(sys.modules[__name__], 'DB-HOST')
conf_user = getattr(sys.modules[__name__], 'DB-USER')
conf_password = getattr(sys.modules[__name__], 'DB-PASSWORD')

connection = MongoClient(conf_host,
                         username=conf_user,
                         password=conf_password,
                         authMechanism='SCRAM-SHA-256')

db = connection.duck
tool = db.tool
posts = db.posts
commentsCollections = db.comments

# ______________________  DB 사용법 메모 _______________________
# post = {"author": "Mike",
#         "text": "My first blog post!",
#         "tags": ["mongodb", "python", "pymongo"],
#         "date": datetime.datetime.utcnow()}
#
# post_id = posts.insert_one(post).inserted_id
#
# pprint.pprint(tool.find_one())
# pprint.pprint(post_id);
#
# pprint.pprint(posts.find_one({"_id": post_id}))
#
# new_posts = [{"author": "Mike",
#               "text": "Another post!",
#               "tags": ["bulk", "insert"],
#               "date": datetime.datetime(2009, 11, 12, 11, 14)},
#              {"author": "Eliot",
#               "title": "MongoDB is fun",
#               "text": "and pretty easy too!",
#               "date": datetime.datetime(2009, 11, 10, 10, 45)}]
# result = posts.insert_many(new_posts)
# result.inserted_ids
# ______________________  DB 사용법 메모 _______________________

pprint.pprint(posts.count_documents({}))

# app.secret_key = "secret key"
app = Flask(__name__)
api = Api(app)


# 가장 간단한 예제
@app.route("/")
def hello():
    return "nothing here"


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


# URL Router에 맵핑한다.(Rest URL정의)

api.add_resource(TodoList, '/todos/')
api.add_resource(Todo, '/todos/<string:todo_id>')

# api.add_resource(Comments, '/Comments/<string:Comments_id>')
api.add_resource(Comment, '/comments/')
api.add_resource(CommentList, '/comments/<string:problem_id>')

# 서버 실행
if __name__ == '__main__':
    app.run(debug=True, port=8000)
