import sys
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from setConfigure import set_secret

set_secret(__name__)

AWS_ACCESS_KEY = getattr(sys.modules[__name__], 'AWS_ACCESS_KEY')
AWS_AUTH_ACCESS_KEY = getattr(sys.modules[__name__], 'AWS_AUTH_ACCESS_KEY')

conn = S3Connection(AWS_ACCESS_KEY, AWS_AUTH_ACCESS_KEY)
bucket = conn.get_bucket('duckhoogosa')


def uploadFile(filename, files):
    k = Key(bucket)
    k.key = filename
    k.set_contents_from_string(files.read())

    # 파일 공개
    k.set_acl('public-read')

    # 업로드 후 url 생성, 유효기간 설정
    return k.generate_url(3600 * 24 * 7)