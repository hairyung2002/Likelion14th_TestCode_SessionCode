from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Movie, Comment, Tag
from .serializers import MovieSerializer, MovieListSerializer, CommentSerializer, TagSerializer

from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action

from django.shortcuts import get_object_or_404

from .permissions import IswriterOrReadOnly

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    
    def perform_create(self, serializer):
        movie = serializer.save(writer=self.request.user)
        self.handle_tags(movie)
        
    def perform_update(self, serializer):
        movie = serializer.save()
        self.handle_tags(movie)
        
    def handle_tags(self, movie):
        movie.tags.clear()
        
        words = movie.content.split()
        
        tag_names = {
            word[1:].strip(".,!?")
            for word in words
            if word.startswith("#") and len(word) > 0
        }
        
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            movie.tags.add(tag)
            
    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        return MovieSerializer
    
    @action(
        detail = False,
        methods = ['get'],
    )
    
    def recommend(self, request):
        movie = (
            self.get_queryset()
            .order_by("?")
            .first()
        )
        
        if movie is None:
            return Response(
                {
                    "detail": "등록된 영화가 없습니다."
                },
                status = status.HTTP_404_NOT_FOUND,
            )
            
        serializer = self.get_serializer(movie)
        
        return Response(serializer.data)
    
    @action(methods=['GET'], detail = True)
    def test(self, request, pk=None):
        test_movie = self.get_object()
        test_movie.click_num += 1
        test_movie.save(update_fields=['click_num'])
        return Response()

# @api_view(['GET', 'POST'])
# def movie_list_create(request):
#     if request.method == 'GET':
#         movies = Movie.objects.all()
#         serializer = MovieSerializer(movies, many=True)
#         return Response(data=serializer.data)

#     if request.method == 'POST':
#         serializer = MovieSerializer(data=request.data)
#         if serializer.is_valid(raise_exception=True):
#             movie = serializer.save()

#             content = request.data['content']
#             tags = [word[1:] for word in content.split(' ') if word.startswith('#')]
#             for t in tags:
#                 try:
#                     tag = get_object_or_404(Tag, name=t)
#                 except:
#                     tag = Tag(name=t)
#                     tag.save()
#                 movie.tags.add(tag)

#             movie.save()
#             return Response(data=MovieSerializer(movie).data)


# @api_view(['GET', 'PATCH', 'DELETE'])
# def movie_detail_update_delete(request, movie_id):
#     movie = get_object_or_404(Movie, id=movie_id)

#     if request.method == 'GET':
#         serializer = MovieSerializer(movie)
#         return Response(serializer.data)

#     elif request.method == 'PATCH':
#         serializer = MovieSerializer(instance=movie, data=request.data)
#         if serializer.is_valid():
#             movie = serializer.save()

#             movie.tags.clear()
#             content = request.data.get("content")
#             tags = [word[1:] for word in content.split(' ') if word.startswith('#')]
#             for t in tags:
#                 try:
#                     tag = get_object_or_404(Tag, name=t)
#                 except:
#                     tag = Tag(name=t)
#                     tag.save()
#                 movie.tags.add(tag)

#             movie.save()
#             return Response(data=MovieSerializer(movie).data)

#     elif request.method == 'DELETE':
#         movie.delete()
#         data = {
#             'deleted_movie': movie_id
#         }
#         return Response(data)

# 댓글 디테일 조회, 수정, 삭제
class CommentViewSet(
    viewsets.GenericViewSet, 
    mixins.RetrieveModelMixin, 
    mixins.UpdateModelMixin, 
    mixins.DestroyModelMixin
):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

# 영화 게시물에 있는 댓글 목록 조회, 영화 게시물에 댓글 작성
class MovieCommentViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
):
    serializer_class = CommentSerializer

    def get_queryset(self):
        movie_id = self.kwargs.get("movie_id")
        return Comment.objects.filter(movie_id=movie_id)
    
    def perform_create(self, serializer):
        movie_id = self.kwargs.get("movie_id")
        movie = get_object_or_404(
            Movie,
            id=movie_id,
        )
        
        serializer.save(
            movie=movie,
            writer=self.request.user,
        )


#@api_view(['GET'])
#def find_tag(request, tags_name):
#    tags = get_object_or_404(Tag, name=tags_name)
#
#   if request.method == 'GET':
#      movies = Movie.objects.filter(tags__in=[tags])
#      serializer = MovieSerializer(movies, many=True)
#    return Response(data=serializer.data)

class TagViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    
    lookup_field = 'name'
    lookup_url_kwarg = 'tag_name'
    
    def retrieve(self, request, *args, **kwargs):
        tag_name = kwargs.get("tag_name")
        tag = get_object_or_404(Tag, name=tag_name)
        
        movies = Movie.objects.filter(tags=tag)
        serializer = MovieSerializer(movies, many=True)
        
        return Response(serializer.data)