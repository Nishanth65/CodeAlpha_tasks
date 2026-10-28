from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from .models import Profile, Post, Comment, Like, Follow
from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserUpdateForm,
    ProfileUpdateForm,
    PostForm,
    CommentForm
)

# ==========================================
# AUTHENTICATION VIEWS
# ==========================================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('feed')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Ensure Profile exists
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f"Welcome to Social Connect, @{user.username}! Your account has been created.")
            return redirect('feed')
        else:
            messages.error(request, "Please correct the errors below to create your account.")
    else:
        form = UserRegistrationForm()
        
    return render(request, 'social/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('feed')
        
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, @{user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('feed')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()
        
    return render(request, 'social/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


# ==========================================
# FEED & POSTS VIEWS
# ==========================================

@login_required
def feed_view(request):
    feed_type = request.GET.get('tab', 'all')  # 'all' or 'following'
    search_query = request.GET.get('q', '').strip()
    
    # Base queryset with author and profile preloaded
    posts_qs = Post.objects.select_related('author', 'author__profile').prefetch_related('likes', 'comments', 'comments__author', 'comments__author__profile')
    
    if search_query:
        posts_qs = posts_qs.filter(
            Q(content__icontains=search_query) |
            Q(author__username__icontains=search_query) |
            Q(author__first_name__icontains=search_query) |
            Q(author__last_name__icontains=search_query)
        )
    elif feed_type == 'following':
        following_user_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        posts_qs = posts_qs.filter(author_id__in=following_user_ids)

    posts = posts_qs.order_by('-created_at')

    # Find which posts are liked by the current user for efficient rendering
    liked_post_ids = set(
        Like.objects.filter(user=request.user, post__in=posts).values_list('post_id', flat=True)
    )

    # Post creation form
    post_form = PostForm()
    comment_form = CommentForm()

    # Suggested users to follow (exclude current user and already followed users)
    already_following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    already_following_ids.append(request.user.id)
    
    suggested_users = User.objects.exclude(id__in=already_following_ids).select_related('profile')[:5]

    context = {
        'posts': posts,
        'liked_post_ids': liked_post_ids,
        'feed_type': feed_type,
        'search_query': search_query,
        'post_form': post_form,
        'comment_form': comment_form,
        'suggested_users': suggested_users,
    }
    return render(request, 'social/feed.html', context)


@login_required
def create_post_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Your post has been published!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Post published successfully!'})
            return redirect('feed')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('feed')


@login_required
def post_detail_view(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'author__profile').prefetch_related('comments', 'comments__author', 'comments__author__profile'),
        id=post_id
    )
    is_liked = Like.objects.filter(post=post, user=request.user).exists()
    comment_form = CommentForm()

    context = {
        'post': post,
        'is_liked': is_liked,
        'comment_form': comment_form,
    }
    return render(request, 'social/post_detail.html', context)


@login_required
def edit_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Authorization check: only author can edit
    if post.author != request.user:
        messages.error(request, "You are not authorized to edit this post.")
        return redirect('post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Your post was updated successfully!")
            return redirect('post_detail', post_id=post.id)
        else:
            messages.error(request, "Please fix the errors in your post.")
    else:
        form = PostForm(instance=post)

    return render(request, 'social/edit_post.html', {'form': form, 'post': post})


@login_required
@require_POST
def delete_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Authorization check: only author can delete
    if post.author != request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        messages.error(request, "You are not authorized to delete this post.")
        return redirect('feed')

    post.delete()
    messages.success(request, "Post deleted successfully.")
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Post deleted'})
    return redirect('feed')


# ==========================================
# LIKES & COMMENTS VIEWS
# ==========================================

@login_required
@require_POST
def toggle_like_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like_obj = Like.objects.filter(post=post, user=request.user).first()
    
    if like_obj:
        like_obj.delete()
        liked = False
    else:
        Like.objects.create(post=post, user=request.user)
        liked = True

    likes_count = post.likes.count()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': likes_count,
        })
    
    return redirect(request.META.get('HTTP_REFERER', 'feed'))


@login_required
@require_POST
def add_comment_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'author': comment.author.username,
                'author_avatar': comment.author.profile.avatar_url,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%b %d, %Y, %I:%M %p'),
                'comments_count': post.comments.count(),
            })
        messages.success(request, "Comment posted successfully!")
    else:
        messages.error(request, "Failed to post comment. Content cannot be empty.")

    return redirect(request.META.get('HTTP_REFERER', 'post_detail', post_id=post.id))


@login_required
@require_POST
def delete_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Authorization check: only author can delete comment
    if comment.author != request.user and comment.post.author != request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        messages.error(request, "You are not authorized to delete this comment.")
        return redirect('post_detail', post_id=comment.post.id)

    post_id = comment.post.id
    comment.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'comments_count': Comment.objects.filter(post_id=post_id).count()
        })
        
    messages.success(request, "Comment deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'post_detail', post_id=post_id))


# ==========================================
# USER PROFILES & FOLLOW SYSTEM
# ==========================================

@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User.objects.select_related('profile'), username=username)
    profile, _ = Profile.objects.get_or_create(user=profile_user)
    
    posts = Post.objects.filter(author=profile_user).select_related('author', 'author__profile').prefetch_related('likes', 'comments')
    
    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()
    posts_count = posts.count()
    
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    liked_post_ids = set(
        Like.objects.filter(user=request.user, post__in=posts).values_list('post_id', flat=True)
    )

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'posts': posts,
        'liked_post_ids': liked_post_ids,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
        'is_following': is_following,
        'is_self': (request.user == profile_user),
    }
    return render(request, 'social/profile.html', context)


@login_required
def edit_profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile', username=request.user.username)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'social/edit_profile.html', context)


@login_required
@require_POST
def toggle_follow_view(request, username):
    target_user = get_object_or_404(User, username=username)
    
    # Cannot follow oneself
    if target_user == request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'You cannot follow yourself.'}, status=400)
        messages.warning(request, "You cannot follow yourself.")
        return redirect('profile', username=username)

    follow_record = Follow.objects.filter(follower=request.user, following=target_user).first()
    
    if follow_record:
        follow_record.delete()
        is_following = False
        action_msg = f"You unfollowed @{target_user.username}."
    else:
        Follow.objects.create(follower=request.user, following=target_user)
        is_following = True
        action_msg = f"You are now following @{target_user.username}."

    followers_count = Follow.objects.filter(following=target_user).count()
    following_count = Follow.objects.filter(follower=target_user).count()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_following': is_following,
            'followers_count': followers_count,
            'following_count': following_count,
            'message': action_msg
        })
        
    messages.success(request, action_msg)
    return redirect(request.META.get('HTTP_REFERER', 'profile', username=username))


@login_required
def followers_list_view(request, username):
    target_user = get_object_or_404(User, username=username)
    followers = User.objects.filter(following_set__following=target_user).select_related('profile')
    
    current_user_following_ids = set(
        Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    )

    context = {
        'target_user': target_user,
        'users': followers,
        'list_title': f"People following @{target_user.username}",
        'current_user_following_ids': current_user_following_ids,
    }
    return render(request, 'social/user_list.html', context)


@login_required
def following_list_view(request, username):
    target_user = get_object_or_404(User, username=username)
    following = User.objects.filter(followers_set__follower=target_user).select_related('profile')
    
    current_user_following_ids = set(
        Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    )

    context = {
        'target_user': target_user,
        'users': following,
        'list_title': f"People followed by @{target_user.username}",
        'current_user_following_ids': current_user_following_ids,
    }
    return render(request, 'social/user_list.html', context)


@login_required
def explore_users_view(request):
    search_query = request.GET.get('q', '').strip()
    users_qs = User.objects.exclude(id=request.user.id).select_related('profile')
    
    if search_query:
        users_qs = users_qs.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(profile__bio__icontains=search_query)
        )
    
    users = users_qs.annotate(
        followers_num=Count('followers_set')
    ).order_by('-followers_num', 'username')[:30]

    current_user_following_ids = set(
        Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    )

    context = {
        'users': users,
        'search_query': search_query,
        'list_title': "Discover People",
        'current_user_following_ids': current_user_following_ids,
    }
    return render(request, 'social/explore.html', context)
