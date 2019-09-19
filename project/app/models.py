from mongoengine import Document, EmbeddedDocument, DynamicDocument, fields, StringField, ListField, ReferenceField, \
    EmailField, DateTimeField, EmbeddedDocumentField, BooleanField, UUIDField, IntField, DynamicField
from django.utils import timezone


# 일반적인 도큐먼트 정의
# 커스텀필드 예제
class ToolInput(EmbeddedDocument):
    name = StringField()
    value = DynamicField()


class Tool(Document):
    label = StringField()
    description = StringField()
    inputs = ListField(fields.EmbeddedDocumentField(ToolInput))
    referenceTime = DateTimeField(blank=True, null=True)

    def publish(self):
        self.referenceTime = timezone.now()
        self.save()

    def __str__(self):
        return self.label


# duck 프로젝트 스키마

class Comments(DynamicDocument):
    _id: UUIDField(
        format='hex_verbose',
        primary_key=True,
        unique=True,
        editable=False,
        verbose_name='PK')
    email: StringField()
    comment: StringField()
    label = StringField()
    day = DateTimeField(auto_now=True)

class ChoiceField(EmbeddedDocument):
    text: StringField()
    answer: BooleanField()


class QuestionField(EmbeddedDocument):
    _id: UUIDField(
        format='hex_verbose',
        primary_key=True,
        unique=True,
        editable=False,
        verbose_name='PK')
    type = StringField()
    fileLink = StringField(allow_empty=True)
    fileLink = StringField(allow_empty=True)
    problemText = StringField()
    Choice: ListField(EmbeddedDocumentField(ChoiceField))


class Problems(Document):
    _id: UUIDField(
        format='hex_verbose',
        primary_key=True,
        unique=True,
        editable=False,
        verbose_name='PK')
    email: StringField()
    tags: ListField(child=StringField, allow_empty=False)
    Genre: StringField()
    day = DateTimeField()
    title: StringField()
    background: StringField()
    representImg: StringField()
    Problems: ListField(EmbeddedDocumentField(QuestionField))


class Answer(EmbeddedDocument):
    value: DynamicField()


class Solutions(EmbeddedDocument):
    _id: ReferenceField(Problems)
    solved_date: DateTimeField(auto_now=True)
    answer: ListField(EmbeddedDocumentField(Answer))


class Users(Document):
    email: EmailField(
        primary_key=True,
        unique=True,
    )
    nickname: StringField()
    tier: StringField()
    answerCount: IntField()
    totalProblemCount: IntField()
    solutions: ListField(EmbeddedDocumentField(Solutions))

    # class Blog(DynamicDocument):
    #     owner = ReferenceField(User)
    #     title = fields.StringField(max_length=30)
    #     tags = ListField(StringField())
    #     day = serializers.DateField(initial=datetime.date.today)
    #
    # class User(Document):
    #     username = StringField(max_length=30)
    #     email = EmailField(max_length=30)
    #     friends = ListField(ReferenceField('self'))
    #     extra = DictField()
