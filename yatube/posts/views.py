from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def pagination(posts, request):
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    posts = (
        Post
        .objects
        .select_related('author', 'group')
    )
    context = {
        'posts': posts,
        'page_obj': pagination(posts, request),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = (
        group
        .posts
        .select_related('author')
    )
    context = {
        'group': group,
        'page_obj': pagination(posts, request),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = (
        author
        .posts
        .select_related('group')
    )
    following = request.user.is_authenticated and author.following.exists()
    context = {
        'following': following,
        'author': author,
        'page_obj': pagination(author_posts, request),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, pk):
    post = get_object_or_404(
        Post
        .objects
        .select_related('group', 'author'),
        id=pk
    )
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    form.save()
    return redirect('posts:profile', post.author.username)


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, id=pk)
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})
    form.save()
    return redirect('posts:post_detail', post.pk)


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, id=pk)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post.pk)


@login_required
def follow_index(request):
    followers = request.user.follower.values('author')
    posts = (
        Post
        .objects
        .select_related('author', 'group')
        .filter(author__in=followers)
    )
    context = {
        'posts': posts,
        'page_obj': pagination(posts, request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        follower = Follow.objects.get(user=request.user, author=author)
        follower.delete()
    return redirect('posts:profile', author.username)
