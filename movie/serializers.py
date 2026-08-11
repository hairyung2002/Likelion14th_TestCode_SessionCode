from rest_framework import serializers
from .models import *


class MovieSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    writer = serializers.CharField(source='writer.username', read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)

    comments = serializers.SerializerMethodField(read_only=True)
    tags = serializers.SerializerMethodField(read_only=True)
    image = serializers.ImageField(use_url=True, required=False)

    def get_comments(self, instance):
        serializer = CommentSerializer(instance.comments, many=True)
        return serializer.data

    def get_tags(self, instance):
        tags = instance.tags.all()
        return [tag.name for tag in tags]

    class Meta:
        model = Movie
        fields = ['id', 'writer', 'name', 'content', 'created_at', 'updated_at',
                  'tags', 'image', 'comments', 'click_num']
        # fields = '__all__'
        # fields = ('id', 'name', 'content', 'created_at', 'updated_at')

class MovieListSerializer(serializers.ModelSerializer):
    comments_count = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    
    def get_comments_count(self, instance):
        return instance.comments.count()
    
    def get_tags(self, instance):
        return [
            tag.name
            for tag in instance.tags.all()
        ]
        
    class Meta:
        model = Movie
        fields = [
            "id",
            "name",
            "content",
            "created_at",
            "updated_at",
            "tags",
            "image",
            "comments_count",
        ]

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = [
            'movie', 
            'writer',
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
