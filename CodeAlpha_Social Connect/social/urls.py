from django.urls import path
from . import views

urlpatterns = [
    # Feed & Discovery
    path('', views.feed_view, name='feed'),
    path('explore/', views.explore_users_view, name='explore'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Posts
    path('post/create/', views.create_post_view, name='create_post'),
    path('post/<int:post_id>/', views.post_detail_view, name='post_detail'),
    path('post/<int:post_id>/edit/', views.edit_post_view, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post_view, name='delete_post'),

    # Interactions: Likes & Comments
    path('post/<int:post_id>/like/', views.toggle_like_view, name='toggle_like'),
    path('post/<int:post_id>/comment/', views.add_comment_view, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment_view, name='delete_comment'),

    # User Profile & Follows
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/follow/', views.toggle_follow_view, name='toggle_follow'),
    path('profile/<str:username>/followers/', views.followers_list_view, name='followers_list'),
    path('profile/<str:username>/following/', views.following_list_view, name='following_list'),
]
