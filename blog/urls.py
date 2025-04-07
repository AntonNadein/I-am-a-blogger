from django.urls import path

from blog import views
from blog.apps import BlogConfig

app_name = BlogConfig.name

urlpatterns = [
    path("", views.ListIndex.as_view(), name="index"),
    path("blog_list/", views.BlogListView.as_view(), name="blog_list"),
    path("detail/<int:pk>/", views.BlogDetailView.as_view(), name="blog_detail"),
    path("create/", views.BlogCreateView.as_view(), name="blog_create"),
    path("update/<int:pk>/", views.BlogUpdateView.as_view(), name="blog_update"),
    path("delete/<int:pk>/", views.BlogDeleteView.as_view(), name="blog_delete"),
    path("topic_detail/<str:title>/", views.TopicDetailView.as_view(), name="topic_detail"),
    path("archive/", views.ListArchive.as_view(), name="archive"),
    path("search_results/", views.BlogSearchView.as_view(), name="search"),
    # Работа с оплатой
    path("payment/<int:pk>/", views.PaymentDetailView.as_view(), name="payment_detail"),
    path("payment_confirmation/<int:pk>/", views.payment_confirmation, name="confirmation"),
]
