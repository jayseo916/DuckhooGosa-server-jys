from rest_framework_mongoengine import serializers
from .models import Tool, Comments


# serializer: 쿼리셋과 모델 인스턴스와 같은 복잡한 데이터를 JSON, XML 또는 다른 컨텐츠의 유형으로 쉽게 변환

class ToolSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Tool
        fields = '__all__'


class CommentsSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Comments
        fields = '__all__'
