from django.urls import path
from . import views
app_name = 'property'  # <--- Add this line!
urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('sell/', views.sell, name='sell'),
    path('buyer/<int:pk>/', views.buyer_detail, name='buyer_detail'),  # ✅ pk add பண்ணு
    path('tenant/<int:pk>/', views.tenant_detail, name='tenant_detail'),  # ✅ pk add பண்ணு
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('buyer-posts/', views.buyer_posts_list, name='buyer_posts_list'),  # ✅ NEW
    path('tenant-posts/', views.tenant_posts_list, name='tenant_posts_list'),  # ✅ NEW
    path('logout/', views.logout_view, name='logout'),
    path('rent_dashboard/', views.rent_dashboard, name='rent_dashboard'),
    path('create-house/', views.create_house, name='create_house'),
    path('pay-bill/', views.pay_bill, name='pay_bill'),
    path('api/transaction/', views.save_transaction, name='save_transaction'),
]