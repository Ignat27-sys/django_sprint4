from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, PostForm, UserForm
from .models import Category, Comment, Post


User = get_user_model()
POSTS_PER_PAGE = 10


def get_published_posts():
    return (
        Post.objects
        .filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
        .select_related('author', 'category', 'location')
        .annotate(comment_count=Count('comments'))
        .order_by('-pub_date')
    )


def paginate(request, queryset):
    paginator = Paginator(queryset, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def get_post_for_detail(user, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'category', 'location'),
        pk=post_id,
    )
    is_public = (
        post.is_published
        and post.pub_date <= timezone.now()
        and post.category is not None
        and post.category.is_published
    )
    if post.author != user and not is_public:
        raise Http404
    return post


def index(request):
    page_obj = paginate(request, get_published_posts())
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, id):
    post = get_post_for_detail(request.user, id)
    comments = post.comments.select_related('author').order_by('created_at')
    context = {
        'post': post,
        'comments': comments,
        'form': CommentForm(),
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    posts = get_published_posts().filter(category=category)
    context = {
        'category': category,
        'page_obj': paginate(request, posts),
    }
    return render(request, 'blog/category.html', context)


def register(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('login')
    return render(
        request,
        'registration/registration_form.html',
        {'form': form},
    )


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    if request.user == profile_user:
        posts = (
            profile_user.posts
            .select_related('author', 'category', 'location')
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
        )
    else:
        posts = get_published_posts().filter(author=profile_user)

    context = {
        'profile': profile_user,
        'page_obj': paginate(request, posts),
    }
    return render(request, 'blog/profile.html', context)


@login_required
def create_post(request):
    form = PostForm(
        request.POST or None,
        request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(
            'blog:profile',
            username=request.user.username,
        )
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, id):
    post = get_object_or_404(Post, pk=id)
    if post.author != request.user:
        return redirect('blog:post_detail', id=post.id)

    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', id=post.id)

    return render(
        request,
        'blog/create.html',
        {'form': form, 'post': post},
    )


@login_required
def delete_post(request, id):
    post = get_object_or_404(Post, pk=id)
    if post.author != request.user:
        return redirect('blog:post_detail', id=post.id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')

    return render(
        request,
        'blog/create.html',
        {'form': PostForm(instance=post), 'post': post},
    )


@login_required
def add_comment(request, id):
    post = get_post_for_detail(request.user, id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', id=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment.objects.select_related('post'),
        pk=comment_id,
        post_id=post_id,
    )
    if comment.author != request.user:
        return redirect('blog:post_detail', id=post_id)

    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', id=post_id)

    context = {
        'form': form,
        'comment': comment,
        'post': comment.post,
    }
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment.objects.select_related('post'),
        pk=comment_id,
        post_id=post_id,
    )
    if comment.author != request.user:
        return redirect('blog:post_detail', id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post_id)

    context = {
        'comment': comment,
        'post': comment.post,
    }
    return render(request, 'blog/comment.html', context)


@login_required
def edit_profile(request):
    form = UserForm(request.POST or None, instance=request.user)
    if form.is_valid():
        user = form.save()
        return redirect('blog:profile', username=user.username)
    return render(request, 'blog/user.html', {'form': form})
