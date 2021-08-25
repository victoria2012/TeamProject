"""semi_project_pop_ URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import path
from django.views.generic import TemplateView


from pop import views

urlpatterns = [

    path('', views.index, name='index'),
    path('graph_kq11', views.graph_kq11, name='graph_kq11'),
    # path('graph_kq11', TemplateView.as_view(template_name='graph_kq11.html'),name='graph_kq11'),
    path('graph_ks11', views.graph_ks11, name='graph_ks11'),
    path('index2', views.index2, name='index2'),
    path('company_info', views.company_info, name='company_info'),
    path('stock_realtime', views.stock_realtime, name='stock_realtime'),
    path('keyword', views.keyword, name='keyword'),


]
