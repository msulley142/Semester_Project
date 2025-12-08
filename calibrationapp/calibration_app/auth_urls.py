from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import SignUpView
from .crudviews import ProfileUpdate


urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('profile/',ProfileUpdate.as_view(), name='profile'),
    path('password_change/',auth_views.PasswordChangeView.as_view(template_name='auth/change_password.html',success_url=reverse_lazy('password_change_done'), ),name='password_change',),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='auth/change_password_done.html'), name='password_change_done',),
]
