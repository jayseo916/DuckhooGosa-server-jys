from django.shortcuts import render

from rest_framework_mongoengine import viewsets as meviewsets
from .serializers import ToolSerializer, CommentsSerializer
from .models import Tool, Comments

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser


# 3단계 지점: 이곳으로 던저진 요청은 => views 에 정의한 ToolViewSet 으로 던진다.

class ToolViewSet(meviewsets.ModelViewSet):
    lookup_field = 'id'
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer


class CommentsViewSet(meviewsets.ModelViewSet):
    lookup_field = 'id'
    queryset = Comments.objects.all()
    serializer_class = CommentsSerializer

# @csrf_exempt
# def get_comments(request, pk):
#     '''
#     Get specipic problem's comments
#     '''
#     try:
#         comments = Comments.objects.get(pk=pk)
#         print("@@GET도착@@")
#     except comments.DoesNotExist:
#         return HttpResponse(status=404)
#
#     if request.method == 'GET':
#         serializer = CommentsSerializer(comments)
#         return JsonResponse(serializer.data)
#
#
# @csrf_exempt
# def post_comments(request):
#     '''
#     Post problems's comments
#     '''
#     if request.method == 'POST':
#         print("@@포스트도착@@")
#         data = JSONParser().parse(request)
#     serializer = CommentsSerializer(data=data)
#     if serializer.is_valid():
#         serializer.save()
#         return JsonResponse(serializer.data, status=201)
#     return JsonResponse(serializer.errors, status=400)


# 클래스방식 - 익숙하지가 않아서 함수방식을 시도중.
# class GetComment(meviewsets.ModelViewSet):
#     lookup_field = 'id'
#     queryset = Comments.objects.all()
#     serializer_class = CommentsSerializer

# def post_list(request):
#     return render(request, 'blog/post_list.html', {})

# class CommentsViewSet(meviewsets.ModelViewSet):
#     lookup_field = 'id'
#     queryset = Tool.objects.all()
#     serializer_class = ToolSerializer
