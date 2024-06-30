# from django.conf.urls import include, url
from django.urls import path, re_path, include
from . import views as chain_views

from django.views.generic import ListView

urlpatterns = [
    path('declare_node_state', chain_views.declare_node_state_view),
    path('get_broadcast_list', chain_views.get_broadcast_list_view),
    path('get_current_node_list', chain_views.get_current_node_list_view),

    path('receive_data_packet', chain_views.receive_data_packet_view),
    path('receive_posts_for_validating', chain_views.receive_posts_for_validating_view),

    path('receive_data', chain_views.receive_data_view),
    path('request_data', chain_views.request_data_view),

    re_path('get_node_request/(?P<node_id>[\w-]+)', chain_views.get_node_request_view),

]
