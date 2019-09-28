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
usersCollections = db.users

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
            # if 'logged_in' in session:
            print("로그인 통과, 현재 무조건 통과시키는 상태")
            return f(*args, **kwargs)
            # else:
            #     print("세션없음")
            #     return "NO SESSION ERROR"

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
        content['nickName'] = "아무개 G"
        content['ratingNumber'] = 0
        content['tryCount'] = 0
        content['okCount'] = 0
        content['tags'] = ["테스트"]
        for problem in content['problems']:
            problem['tryCount'] = 0
            problem['okCount'] = 0
        pprint.pprint(content)
        result_id = problemsCollections.insert_one(content).inserted_id
        obj = {"_id": str(result_id)}
        return json.dumps(obj)


class ProblemMain(Resource):
    def post(self):
        args = parser.parse_args()
        sortedproblem = problemsCollections.find().sort('date', -1). \
            limit(10 + int(args['next_problem'])). \
            skip(int(args['next_problem']))
        result = []
        for v in sortedproblem:
            v['_id'] = str(v['_id'])
            result.append(v)
        return json.dumps(result), 201

    @login_required()
    def get(self):
        return "good!"


class ProblemSearch(Resource):
    @login_required()
    def get(self):
        return "good!"


class ProblemSolution(Resource):
    @login_required()
    def post(self):
        content = request.get_json()
        original = problemsCollections.find_one(ObjectId(content['problem_id']))
        original_answers = [];
        for problem in original['problems']:
            print(problem,'프로블램')
            arr = [];
            if 'subjectAnswer' in problem:
                print(problem['subjectAnswer'], "주관식 답 집어넣음")
                original_answers.append(problem['subjectAnswer'])
                continue

            for index, choice in enumerate(problem['choice']):
                print(choice[0],"?왜 딕셔너리가 아닌가?")
                if choice[0]['answer'] == 'true':
                    print(index, "객관식 답 넣음")
                    arr.append(index)
            original_answers.append(arr)

        print("완성된 답변 리스트", original_answers)
        try_count = len(original_answers)
        right_count = 0

        for i, answer in enumerate(content["answer"]):
            print(answer, original_answers, "정답매기기 단계")
            if answer == original_answers[i]:
                right_count = right_count + 1
                print('맞춘코스', right_count, try_count, answer, original_answers[i])
                problemsCollections.update_one({"_id": ObjectId(content['problem_id'])},
                                               {'$inc': {"problems." + str(i) + ".okCount": 1,
                                                         "problems." + str(i) + ".tryCount": 1}})
            else:
                print('틀린코스', right_count, try_count, answer, original_answers[i])
                problemsCollections.update_one({"_id": ObjectId(content['problem_id'])}, {'$inc':
                                                                                              {"problems." + str(
                                                                                                  i) + ".tryCount": 1}})

        problemsCollections.update_one({"_id": ObjectId(content['problem_id'])},
                                       {'$inc': {"okCount": right_count, "tryCount": try_count}})

        original = problemsCollections.find_one(ObjectId(content['problem_id']))
        response_obj = {"_id": content['problem_id'],
                        "okCount": right_count,
                        "tryCount": len(content['answer']),
                        "commentCount": commentsCollections.count_documents({"problem_id": content['problem_id']}),
                        "totalProblem": original['tryCount'],
                        "totalOkProblem": original['okCount'],
                        "checkProblem": original['problems']
                        }
        solution_obj = {
            "problem_id": content['problem_id'],
            "solved_date": content['date'],
            "answer": content['answer'],
            "accuracy": round((right_count / try_count) * 100, 2)
        }
        user_obj = {
            "email": content['email'],
            "nickname": None,
            "img": None,
            "tier": None,
            "answerCount": 0,
            "totalProblemCount": 0,
            "solution": []
        }

        user_check_result = usersCollections.find_one({"email": content['email']})
        print(user_check_result)
        if user_check_result is None:
            usersCollections.insert_one(user_obj)
            result = usersCollections.update_one({"email": content['email']},
                                                 {"$push": {"solution": solution_obj}})
            pprint.pprint(result)
            print("결과1")
        else:
            print(solution_obj, '발작적 솔루션 제출')
            result = usersCollections.update_one({"email": content['email']},
                                                 {'$push': {'solution': solution_obj}})
            pprint.pprint(result)
            print("결과2")

        return json.dumps(response_obj)


# 값판정해서 클라이언트내려주기
# 사용자콜렉션에 반영해주기
# 문제메타 정보 업데이트하기

# okCount: this.state.resultData.okCount,
# tryCount: this.state.resultData.tryCount,
# commentCount: this.state.resultData.commentCount,
# problemId: this.state.resultData.problemId,
# checkProblem: this.state.resultData.checkProblem,
# totalProblem: this.state.resultData.totalProblem


class ProblemEvalation(Resource):
    @login_required()
    def post(self):
        return "good!"


# URL Router에 맵핑한다.(Rest URL정의)

# comments _ POST
api.add_resource(Comment, '/comment')
# comments _ GET
api.add_resource(CommentList, '/comment/<string:problem_id>')

# problem _ GET
api.add_resource(ProblemMain, '/problem/main')
api.add_resource(ProblemSearch, '/problem/search/<string:tag_word>')

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
