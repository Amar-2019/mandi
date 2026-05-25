from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path('products/', views.product_view, name='product_view'),
    path("village/", views.village_view, name="village"),
    path("mandi/", views.mandi_view, name="mandi"),
    path("villages_list/", views.villages_list_view, name="villages_list"),
    path("mandi_list/", views.mandi_list_view, name="mandi_list"),
    path("route/", views.route, name="get_route"),
    path('submit-products/', views.submit_products, name='submit_products'),
    path('api/submitted-products/', views.get_submitted_products, name='get_submitted_products'),
    # path("route/", views.get_route, name="get_route"),
]
