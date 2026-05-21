from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='teacher_login'),
    path('logout/', views.logout_view, name='teacher_logout'),
    path('feed/', views.feed_view, name='teacher_feed'),
    path('explore/', views.explore_view, name='teacher_explore'),
    path('explore/follow/', views.toggle_follow, name='teacher_toggle_follow'),
    path('post/create/', views.post_create_view, name='teacher_post_create'),
    path('post/<int:post_id>/', views.post_detail_view, name='teacher_post_detail'),
    path('post/<int:post_id>/edit/', views.post_edit_view, name='teacher_post_edit'),
    path('post/<int:post_id>/delete/', views.post_delete_view, name='teacher_post_delete'),
    path('post/<int:post_id>/like/', views.like_view, name='teacher_like'),
    path('post/<int:post_id>/report/', views.report_view, name='teacher_report'),
    path('post/<int:post_id>/save/', views.save_post_view, name='teacher_save_post'),
    path('post/<int:post_id>/comment/', views.comment_view, name='teacher_comment'),
    path('comment/<int:comment_id>/delete/', views.comment_delete_view, name='teacher_comment_delete'),
    path('saved/', views.saved_posts_view, name='teacher_saved_posts'),
    path('profile/edit/', views.edit_profile_view, name='teacher_edit_profile'),
    path('change-password/', views.change_password_view, name='teacher_change_password'),
    path('notifications/', views.notifications_view, name='teacher_notifications'),
    path('chat/', views.chat_view, name='teacher_chat'),
    path('chat/<str:role>/<int:user_id>/', views.chat_detail_view, name='teacher_chat_detail'),
]
