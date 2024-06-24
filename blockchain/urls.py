# from django.conf.urls import include, url
from django.urls import path, re_path, include
from . import views as chain_views

from django.views.generic import ListView

urlpatterns = [
    # # url(r'^mps_update/$', util_views.get_all_mps)
    # path('daily_update', util_views.update_agenda_view),
    # path('all_agendas', util_views.all_agendas_view),
    # path('get_latest_agenda', util_views.get_latest_agenda_view),
    # path('set_party_colours', util_views.set_party_colours_view),
    # # path('test_notification', util_views.test_notify_view),
    path('declare_node_state', chain_views.declare_node_state_view),
    path('get_broadcast_list', chain_views.get_broadcast_list_view),


    re_path('get_node_request/(?P<node_id>[\w-]+)', chain_views.get_node_request_view),


    # re_path('continue_reading/(?P<iden>[\w-]+)', util_views.continue_reading_view),
    # re_path('show_all/(?P<iden>[\w-]+)/(?P<item>[\w-]+)', util_views.show_all_view),
    
    # #----ontario
    # path('mpps_update', util_views.get_current_mpps_view),
    # path('ontario/current_bills', util_views.get_ontario_bills_view),
    # path('ontario/get_weekly_agenda', util_views.get_ontario_agenda_view),
    # path('ontario/get_motions', util_views.get_ontario_motions_view),
    # path('ontario/get_hansard', util_views.get_ontario_hansard_view),
    # path('ontario/get_latest_hansards', util_views.get_ontario_latest_hansards_view),
    # path('ontario/check_elections', util_views.get_ontario_elections_view),

    # #----federal
    # path('mps_update', util_views.get_all_mps_view),
    # path('senators_update', util_views.get_all_senators_view),
    # path('get_federal_candidates', util_views.get_federal_candidates_view),
    # path('get_federal_house_expenses', util_views.get_federal_house_expenses_view),

    # path('get_todays_xml_agenda', util_views.get_todays_xml_agenda_view),
    
    # path('get_latest_house_motions', util_views.get_latest_house_motions_view),
    # path('get_all_house_motions', util_views.get_all_house_motions_view),
    # path('get_session_senate_motions', util_views.get_session_senate_motions_view),

    # # path('get_todays_bills', util_views.get_todays_bills_view),
    # path('get_latest_bills', util_views.get_latest_bills_view),
    # re_path('update_bill/(?P<iden>\d+)', util_views.update_bill_view),
    # re_path('get_all_bills/(?P<param>[\w-]+)', util_views.get_all_bills_view),

    # path('get_latest_house_hansard', util_views.get_latest_house_hansard_view),
    # path('get_session_house_hansards', util_views.get_session_house_hansards_view),
    # path('get_all_house_hansards', util_views.get_all_house_hansards_view),
    # path('get_all_senate_hansards', util_views.get_all_senate_hansards_view),
    
    # path('get_latest_house_committee_list', util_views.get_latest_house_committee_list_view),
    # path('get_latest_house_committees_work', util_views.get_latest_house_committees_work_view),
    # path('get_latest_house_committees', util_views.get_latest_house_committees_view),
    # # path('get_latest_senate_committees', util_views.get_latest_senate_committees_view),
    # re_path('get_latest_senate_committees/(?P<item>[\w-]+)', util_views.get_latest_senate_committees_view),
    # path('get_all_senate_committees', util_views.get_all_senate_committees_view),
    # re_path('reprocess/(?P<organization>[\w-]+)-committee/(?P<parliament>\d+)/(?P<session>\d+)/(?P<iden>[\w-]+)', util_views.committee_reprocess),
    # re_path('reprocess/(?P<organization>[\w-]+)-debate/(?P<parliament>(.*))/(?P<session>(.*))/(?P<iden>\d+)', util_views.hansard_reprocess),

    # #----utils
    # path('is_sonet', util_views.is_sonet_view),
    # path('get_network_data', util_views.get_network_data_view),

    # re_path('mobile_share/(?P<iden>(.*))', util_views.mobile_share_view),
    # re_path('share_modal/(?P<iden>(.*))', util_views.share_modal_view),
    # re_path('post_insight_modal/(?P<iden>(.*))', util_views.post_insight_view),
    # re_path('post_more_options_modal/(?P<iden>(.*))', util_views.post_more_options_view),
    # re_path('verify_post_modal/(?P<iden>(.*))', util_views.verify_post_view),
    # path('build_database', util_views.build_database_view),
    # path('tester1', util_views.tester_queue_view),
    # path('daily_summarizer', util_views.daily_summarizer_view),
    # path('test_notify', util_views.clear_all_app_cache_view),
    # path('run_notifications', util_views.add_test_notification_view),

    # path('django-rq/', include('django_rq.urls')),

    # # path('stream/', util_views.stream_view, name='stream'),


]
