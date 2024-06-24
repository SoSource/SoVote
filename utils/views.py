
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.template.defaulttags import register
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse

import datetime
from accounts.models import Notification, Interaction, User
from posts.forms import AgendaForm
from posts.models import *
from posts.utils import get_user_sending_data
from blockchain.models import get_signing_data
from scrapers.canada.federal import *
from scrapers.canada.ontario import provincial as ontario_functions
# from utils.models import daily_update,get_all_agendas, get_house_committee_list, set_party_colours, get_all_MPs, get_senators, get_all_bills, get_latest_bills, get_all_house_motions, get_senate_motions, get_federal_candidates, get_latest_house_hansard_or_committee, get_session_house_hansards, get_all_house_hansards, get_senate_hansards, get_house_committee_list, get_latest_senate_committees, get_all_senate_committees
from utils.models import *
from firebase_admin.messaging import Notification as fireNotification
from firebase_admin.messaging import Message as fireMessage
import time
from uuid import uuid4
from django.core import serializers

#----ontario
def get_current_mpps_view(request):
    if request.user.is_superuser:
        ontario_functions.get_current_MPPs()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_ontario_bills_view(request):
    if request.user.is_superuser:
        ontario_functions.get_current_bills()
        # queue = django_rq.get_queue('default')
        # queue.enqueue(ontario_functions.get_current_bills, job_timeout=1000)
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_ontario_agenda_view(request):
    if request.user.is_superuser:
        ontario_functions.get_weekly_agenda()
        return render(request, "utils/dummy.html", {"result": 'Success'})
        
def get_ontario_motions_view(request):
    if request.user.is_superuser:
        ontario_functions.get_all_hansards_and_motions('latest')
        return render(request, "utils/dummy.html", {"result": 'Success'})
  
def get_ontario_hansard_view(request):
    if request.user.is_superuser:
        ontario_functions.get_hansard(None)
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_ontario_latest_hansards_view(request):
    if request.user.is_superuser:
        ontario_functions.get_all_hansards_and_motions('recent')
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_ontario_elections_view(request):
    if request.user.is_superuser:
        ontario_functions.check_elections()
        return render(request, "utils/dummy.html", {"result": 'Success'})


#----federal
def update_agenda_view(request):
    if request.user.is_superuser:
        # daily_update()
        queue = django_rq.get_queue('default')
        queue.enqueue(daily_update, job_timeout=500)
        return render(request, "utils/dummy.html", {"result": 'Success'})

def all_agendas_view(request):
    if request.user.is_superuser:
        get_all_agendas()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_latest_agenda_view(request):
    if request.user.is_superuser:
        get_house_agendas(url='https://www.ourcommons.ca/en/parliamentary-business/')
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_todays_xml_agenda_view(request):
    if request.user.is_superuser:
        get_todays_xml_agenda()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_all_mps_view(request):
    if request.user.is_superuser:
        get_house_persons()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_all_senators_view(request):
    if request.user.is_superuser:
        get_senate_persons()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_latest_bills_view(request):
    if request.user.is_superuser:
        get_house_bills()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_all_bills_view(request, param):
    if request.user.is_superuser:
        get_all_bills(param)
        # queue = django_rq.get_queue('default')
        # queue.enqueue(get_all_bills, param, job_timeout=7200)
        return render(request, "utils/dummy.html", {"result": 'Success'})

def update_bill_view(request, iden):
    b = Bill.objects.filter(id=iden)[0]    
    xml = 'https://www.parl.ca/LegisInfo/en/bill/%s-%s/%s/xml' %(b.ParliamentNumber, b.SessionNumber, b.NumberCode)
    print(xml)
    r2 = requests.get(xml)
    root2 = ET.fromstring(r2.content)
    bills2 = root2.findall('Bill')
    for bill in bills2:
        get_bill(bill)    
    return render(request, "utils/dummy.html", {"result": 'Success'})

def get_latest_house_motions_view(request):
    if request.user.is_superuser:
        get_house_motions()
        return render(request, "utils/dummy.html", {"result": 'Success'})
 
def get_all_house_motions_view(request):
    if request.user.is_superuser:
        get_all_house_motions()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_federal_house_expenses_view(request):
    if request.user.is_superuser:
        get_house_expenses()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_session_senate_motions_view(request):
    if request.user.is_superuser:
        get_senate_motions()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_federal_candidates_view(request):
    if request.user.is_superuser:
        get_federal_candidates(1)
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_latest_house_hansard_view(request):
    if request.user.is_superuser:
        # get_house_hansard_or_committee('hansard', 'latest')
        get_house_debates()
        return render(request, "utils/dummy.html", {"result": 'Success'})
    
def get_session_house_hansards_view(request):
    if request.user.is_superuser:
        get_session_house_hansards()
        return render(request, "utils/dummy.html", {"result": 'Success'})
    
def get_all_house_hansards_view(request):
    if request.user.is_superuser:
        get_all_house_hansards()
        return render(request, "utils/dummy.html", {"result": 'Success'})
    
def get_latest_house_committees_view(request):
    if request.user.is_superuser:
        get_house_hansard_or_committee('committee', 'period')
        # get_latest_house_committee_hansard_and_list()
        return render(request, "utils/dummy.html", {"result": 'Success'})
        
def get_latest_house_committees_work_view(request):
    if request.user.is_superuser:
        get_committee_work('latest')
        return render(request, "utils/dummy.html", {"result": 'Success'})
        
def get_latest_house_committee_list_view(request):
    if request.user.is_superuser:
        get_house_committee_list('latest')
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_latest_senate_committees_view(request, item):
    if request.user.is_superuser:
        get_latest_senate_committees(item)
        return render(request, "utils/dummy.html", {"result": 'Success'})
    
def get_all_senate_committees_view(request):
    if request.user.is_superuser:
        get_all_senate_committees()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def get_all_senate_hansards_view(request):
    if request.user.is_superuser:
        get_senate_debates()
        return render(request, "utils/dummy.html", {"result": 'Success'})


#----utils

# from django.views.decorators.csrf import csrf_exempt

# @csrf_exempt
# def stream_view(request):
#     print('streamview')
#     from django.http import StreamingHttpResponse

#     def stream_generator():
#         for i in range(10):
#             yield f"data: Chunk {i}\n\n"
#             time.sleep(1)  # Simulate delay for streaming

#     response = StreamingHttpResponse(stream_generator(), content_type='text/event-stream')
#     response['Cache-Control'] = 'no-cache'
#     return response
def view(request):
    def stream_generator():
        t_start = datetime.datetime.now()
        stream = ollama.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': prompt}],
            stream=True,
        )
        totes = ''
        for chunk in stream:
            x = chunk['message']['content']
            totes = totes + x
            yield x
        t_end = datetime.datetime.now() - t_start
    response = StreamingHttpResponse(stream_generator(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

def is_sonet_view(request):
    print()
    try:
        x = get_user_sending_data(Sonet.objects.first())
    except:
        x = 'None'
    return JsonResponse({'message' : 'is_sonet', 'sonet' : x})

def get_network_data_view(request):
    print('get_supported_chains_view')
    earthU = Update.objects.filter(pointerType='Region', data__icontains='"is_supported": true', Region_obj__ParentRegion_obj=None)[0]
    # print(earthU)
    # print(earthU.Region_obj)
    # print(earthU.Region_obj.__dict__)
    regions = {'Earth':{'type':earthU.Region_obj.nameType,'id':earthU.Region_obj.id,'children':[]}}
    def get_children(parent, children_list):
        children = Update.objects.filter(pointerType='Region', Region_obj__ParentRegion_obj=parent.Region_obj).order_by('Region_obj__Name')
        # children = Update.objects.filter(pointerType='Region', data__icontains='"is_supported": true', Region_obj__ParentRegion_obj=parent.Region_obj)
        for child in children:
            try:
                gov = Government.objects.filter(Region_obj=child.Region_obj)[0]
                govData = {gov.gov_level:{'type':'Government','id':gov.id,'children':[]}}
            except:
                govData = None
            data = {child.Region_obj.Name:{'type':child.Region_obj.nameType,'id':child.Region_obj.id,'children':[]}}
            if govData:
                data[child.Region_obj.Name]['children'].append(govData)
            children_list.append(data)
            new_list = data[child.Region_obj.Name]['children']
            xlist = get_children(child, new_list)
            new_list = data[child.Region_obj.Name]['children'] = xlist
        return children_list

    xlist = get_children(earthU, regions['Earth']['children'])
    # print()
    regions['Earth']['children'] = xlist
    # print(regions)
    # json_data = serializers.serialize('json', [obj])
    # print(json_data)
    # special chains will consist of 'New' 'Transactions' and 'SoMeta'
    return JsonResponse({'specialChains' : None, 'regionChains' : regions, 'sonet' : get_user_sending_data(Sonet.objects.first())})
    
def clear_all_app_cache_view(request):
    if request.user.is_superuser:
        print('run notify')
        from firebase_admin.messaging import Notification as fireNotification
        from firebase_admin.messaging import Message as fireMessage
        from fcm_django.models import FCMDevice
        bill = Bill.objects.all().order_by('-LatestBillEventDateTime')[0]
        link = bill.get_absolute_url().replace('file://', '')
        # if link[0] == '/':
        #     link = 'https://sovote.ca' + link
        FCMDevice.objects.send_message(fireMessage(data={"clearCache":"True"}))
        # from accounts.models import User
        # for u in User.objects.all():
        #     # print(u)
        #     fcm_devices = FCMDevice.objects.filter(user=u)

        #     for device in fcm_devices:
        #         try:
        #             # print(device)
        #             device.send_message(fireMessage(notification=fireNotification(title='test1', body='body1'), data={"click_action" : "FLUTTER_NOTIFICATION_CLICK","link" : link}))
        #             # print('away')
        #         except Exception as e:
        #             print(str(e))
        return render(request, "utils/dummy.html", {"result": 'Success'})

def set_party_colours_view(request):
    if request.user.is_superuser:
        set_party_colours()
        return render(request, "utils/dummy.html", {"result": 'Success'})

def build_database_view(request):
    if request.user.is_superuser:
        # build_database()
        return render(request, "utils/database_builder.html")

def initial_setup_view(request):
    earth, pearthU, earthData, earth_is_new = get_model_and_update('Region', Name='Earth', nameType='Planet', modelType='planet')
    na, naU, naData, na_is_new = get_model_and_update('Region', Name='North America', nameType='Continent', modelType='continent', ParentRegion_obj=earth)
    ca, caU, caData, ca_is_new = get_model_and_update('Region', Name='Canada', nameType='Country', modelType='country', ParentRegion_obj=na)
    us, usU, usData, us_is_new = get_model_and_update('Region', Name='USA', nameType='Country', modelType='country', ParentRegion_obj=na)
    earthData['is_supported'] = True
    naData['is_supported'] = True
    caData['is_supported'] = True
    usData['is_supported'] = True
    save_obj_and_update(earth, pearthU, earthData, earth_is_new)
    save_obj_and_update(na, naU, naData, na_is_new)
    save_obj_and_update(ca, caU, caData, ca_is_new)
    save_obj_and_update(us, usU, usData, us_is_new)
    return JsonResponse({'message' : 'initial setup complete'})

def tester_queue_view(request):
    if request.user.is_superuser:
        # tester_queue()
        # obj = Agenda()
        # fields = obj._meta.fields
        # data = []
        # for f in fields:
        #     data.append(str(f.name))
        # print(data)
        
        def remove_tags(text):
            try:
                TAG_RE = re.compile(r'<[^>]+>')
                text = TAG_RE.sub('', text).replace('"', "'").replace('\n', '').strip()
                text = ''.join(text.splitlines())
                text = unidecode(text)
                return text
            except:
                return None

        'post_id: ppxpp6bb0a48ac60a409ba4d7ed3c239ec506qqxqq'

        sum_start_time = datetime.datetime.now()
        print(sum_start_time)
        prompt = 'Hello'
        json_data = {'prompt':prompt}



        import ollama

        from posts.utils import get_token_count, makeText

        
        # t_start = datetime.datetime.now()
        # stream = ollama.chat(
        #     model='llama3',
        #     messages=[{'role': 'user', 'content': 'Hello'}],
        #     stream=True,
        # )
        # # totes = ''
        # for chunk in stream:
        #     x = chunk['message']['content']
        #     # totes = totes + x
        #     print(x)
        #     # yield x
        # t_end = datetime.datetime.now() - t_start
        # print(t_end)
        b = BillVersion.objects.exclude(TextHtml=None).filter(NumberCode='S-11')[0]
        # for v in versions:
        #     print(v.NumberCode)
        #     x = remove_tags(v.TextHtml)
        #     print(get_token_count(x, "cl100k_base"))
        #     print()
        # print(f'Bill {b.Bill_obj.NumberCode} - {b.Bill_obj.Title}')
        s = Statement.objects.all().order_by('-Content')[0]
        print(s.id)
        print(get_token_count(s.Content))
        print()
        print(s.Content)

        # aaa = b.TextHtml
        # words = remove_tags(aaa)
        # print('len:', len(words))

        # fail
        # debate = Meeting.objects.filter(chamber='House', meeting_type='Debate')[0]
        # print(debate.DateTime)
        # topic = 'Federal-provincial-territorial relations'
        # # search = ['%s'%(topic)]
        # search = ['Federal-provincial-territorial relations']
        # posts = Post.objects.filter(Statement_obj__Meeting_obj=debate).filter(Q(Statement_obj__Terms_array__overlap=search)|Q(Statement_obj__keyword_array__overlap=search))
        # print('count', posts.count())
        # rx = [p for p in posts[1:5]]
        # print(rx)
        # random.shuffle(rx)
        # print(rx)
        # idens = []
        # for p in posts:
        #     idens.append(p.Statement_obj.id)
        #     num_tokens, text = makeText([p])
        #     print('n', num_tokens)
        # print(idens)
        # rx = [posts[0]]
        content = b.TextHtml
        master_text = remove_tags(content)
        words = master_text
        total_tokens = get_token_count(master_text)
        print('total_tokens',total_tokens)
        # time.sleep(3)
        # print()
        # print(words)
        # print()

        # print('ll',len(posts[5:6]))
        # print('total tokes', num_tokens)
        # w = "Read the following text with post_id(92546): %s |END| Tell me the post_id " %(words)
        # num_tokens = get_token_count(words, "cl100k_base")
        # print(text)

        # period = 0
        # period = master_text.find('.') + 1
        # print('period', period)
        # words = text[:period]
        # print()
        # print(text[period-10:period])
        # print(text[period:period+10])
        # print('words', len(words))
        # num_tokens = get_token_count(words, "cl100k_base")
        # print('num_tokens', num_tokens)
        # print('len text', len(text))


        # period = text[period+1:].find('.')
        # print('period2', period)
        # words = text[:period]
        # fail
        # print(text[300:500])
        # print(text[415:500])
        # q = 50
        # x = period
        def func(text):
            def reduce(text, period):
                print('start reduce')
                # num_tokens = 0
                period = 0
                x = period + 1
                num_tokens = get_token_count(text[:x])
                print(f'words len:{len(text)}, period:{period}, num_toks:{num_tokens}')
                while num_tokens < 1900 and period < len(text) and x != 0:
                    x = text[period:].find('.') + 1
                    new_period = period + x

                    num_tokens = get_token_count(text[:new_period])
                    period = new_period
                if period == 0:
                    print(f'words len:{len(text)}, new_period:{period}, num_toks:{num_tokens}')
                    print()
                    return text, period
                else:
                    print(f'words len:{len(text[:period])}, new_period:{period}, num_toks:{num_tokens}')
                    print()
                    # print(text[:period])
                    # print()
                    return text[:period], period
            
            def generate(words, promptPosition):
                print('start generate')
                if promptPosition == 'A':
                    w = f'''The following is a snippet of a proposed bill, read the text: {words} |END| Summarize the important parts from the preceeding text to a young but smart audience, be honest and fair, address the points of the text, take note of anything suspicious or controversial. Summarize it into bullet points. Do not introduce the summary, do not say 'Here's a summary...', just say it. Do not go over 2 bullets.'''

                elif promptPosition == 'B':
                    w = f'''The following are bullet points from a proposed bill, read the bullets: {words} |END| Summarize the important parts from the preceeding text to a young but smart audience, be honest and fair, address the points of the text, take note of anything suspicious or controversial. Summarize it into bullet points. Do Not say anything other than the summary. Do not introduce the summary, do not say 'Here's a summary...', just say it. Do not go over 5 bullets.'''

                elif promptPosition == 'C':
                    w = f'''The following are bullet points from a proposed bill, read the bullets: {words} |END| Summarize the important parts from the preceeding text to a young but smart audience, be honest and fair, address the points of the text, take note of anything suspicious or controversial. Do Not say anything other than the summary. Do not introduce the summary, do not say 'Here's a summary...', just say it. Do not go over 5 paragraphs.'''

                t_start = datetime.datetime.now()
                stream = ollama.chat(
                    model='llama3',
                    messages=[{'role': 'user', 'content': w}],
                    stream=True,
                )
                totes = ''
                for chunk in stream:
                    x = chunk['message']['content']
                    totes = totes + x
                    # print(x)
                    # yield x
                t_end = datetime.datetime.now() - t_start
                print(t_end)
                # print(f'Bill {b.Bill_obj.NumberCode} - {b.Bill_obj.Title}')
                print()
                print(totes)
                # print(len(totes))
                # print(idens)
                num_tokens = get_token_count(totes)
                print('num_tokens', num_tokens)
                print('total_tokens',total_tokens)
                print()
                return totes
            

            # period = master_text.find('.') + 1
            # print('period', period)
            # words = master_text[:period]
            # print('words', len(words))
            # num_tokens = get_token_count(words, "cl100k_base")
            # print('num_tokens', num_tokens)
            total_sum = ''
            # print('len text', len(master_text))
            loops = 0
            period = 0
            word_addition = 0
            while word_addition < len(master_text) and loops < 250:
                print()
                print('loop', loops)
                # print('master len', len(master_text[period:]))
                # print('period',period)
                loops += 1
                words, new_period = reduce(master_text[period:], period)
                period += new_period
                word_addition += len(words)
                print('word_addition',word_addition, len(master_text))
                word_tokens = get_token_count(words)
                if word_tokens > 50:
                    # total_sum = total_sum + 'xxxx xxxx '
                    total_sum = total_sum + generate(words, 'A')
                else:
                    total_sum = total_sum + words
                sum_tokens = get_token_count(total_sum)
                print('sum_tokens', sum_tokens)
                if sum_tokens > 1950:
                    print('summarizing the summaries')
                    print(total_sum)
                    print()
                    total_sum = generate(total_sum, 'B')
            
            print()
            print('-----total summs-----')
            print(total_sum)
            print()
            print('----final gen----')
            print()
            final_sum = generate(total_sum, 'C')
            

        print('-----', datetime.datetime.now() - sum_start_time)

        return render(request, "utils/dummy.html", {"result": 'Success'})

def daily_summarizer_view(request):
    if request.user.is_superuser:
        daily_summarizer(None)
        # queue = django_rq.get_queue('default')
        # queue.enqueue(send_notifications, job_timeout=500)
        return render(request, "utils/dummy.html", {"result": 'Success'})

def run_notifications_view(request):
    if request.user.is_superuser:
        send_notifications('Sozed')
        # queue = django_rq.get_queue('default')
        # queue.enqueue(send_notifications, job_timeout=500)
        return render(request, "utils/dummy.html", {"result": 'Success'})

def add_test_notification_view(request):
    if request.user.is_superuser:
        # print('test notification')

        sozed = User.objects.get(username='Sozed')
        sozed.alert('%s-%s' %(datetime.datetime.now(), 'test notify'), None, 'test body')

        # request.user.alert('new test notification', '/', 'test body')
        return render(request, "utils/dummy.html", {"result": 'Success'})

def remove_notification_view(request, iden):
    n = Notification.objects.filter(id=iden, user=request.user)[0]
    n.new = False
    n.save()
    return render(request, "utils/dummy.html", {"result": 'Success'})

def calendar_widget_view(request):
    print('cal widget')
    if request.method == 'POST':
        data = request.POST['date']
        # print(data)
        # a = data.find('date=')+len('date=')
        date = datetime.datetime.strptime(data, '%Y-%m-%d')
        # print(date)
        agenda = Agenda.objects.filter(date_time__gte=date).order_by('date_time')[0]
        agendaItems = AgendaItem.objects.filter(agendaTime__agenda=agenda).select_related('agendaTime').order_by('position')
        form = AgendaForm()   
        try:
            theme = request.COOKIES['theme']
        except:
            theme = 'day'
        context = {
            "theme": theme,
            "agenda":agenda,
            "agendaItems":agendaItems,
            'agendaForm': form,
        }
        return render(request, "utils/agenda_widget.html", context)

def mobile_share_view(request, iden):
    print('mobile share')
    post = Post.objects.filter(id=iden)[0]
    link = post.get_absolute_url()
    if link[0] == '/':
        link = 'https://SoVote.org' + link
    shareTitle = post.get_title() + ' ' + link
    print(shareTitle)
    try:    
        fcmDeviceId = request.COOKIES['fcmDeviceId']
        print(fcmDeviceId)
        device = FCMDevice.objects.filter(user=request.user, registration_id=fcmDeviceId)[0]
        device.send_message(fireMessage(data={"share" : "True", "shareTitle":shareTitle}))
    except Exception as e:
        print(str(e))
    return render(request, "utils/dummy.html", {"result": 'Success'})

def share_modal_view(request, iden):
    post = Post.objects.filter(id=iden)[0]
    context = {
        'title': 'Share Post',
        'post': post,
    }
    return render(request, "utils/share_modal.html", context)


@register.filter
def to_percent(num1, num2):
    try:
        percent = (num1 + num2) / num1
    except:
        percent = '-'
    return percent

def post_insight_view(request, iden):
    post = Post.objects.filter(id=iden)[0]
    context = {
        'title': 'Insight',
        'post': post,
    }
    return render(request, "utils/post_insight.html", context)

def post_more_options_view(request, iden):
    post = Post.objects.filter(id=iden)[0]
    try:
        interaction = Interaction.objects.filter(User_obj=request.user, Post_obj=post)[0]
    except:
        interaction = None
    context = {
        'title': 'More Options',
        'post': post,
        'interaction':interaction,
    }
    return render(request, "utils/post_more_options.html", context)

def verify_post_view(request, iden):

    post = Post.objects.filter(id=iden)[0]
    context = {
        'title': 'Verify Me',
        'post': post,
    }
    return render(request, "utils/verify_post.html", context)

def deep_link_android_asset_view(request):
    return render(request, "json/deep_link_android_asset.html", content_type="application/json")

def deep_link_iphone_asset_view(request):
    return render(request, "json/deep_link_iphone_asset.html", content_type="application/json")

def continue_reading_view(request, iden):
    # print(iden)
    topic = request.GET.get('topic', '')
    # print(topic)
    if 'statement-' in iden:
        Id = iden.replace('statement-', '')
        hansard = Statement.objects.get(id=Id)
        context = {'h':hansard, 'topicList':topic}
    # elif 'commi-' in iden:
    #     Id = iden.replace('c-', '')
    #     committee = CommitteeItem.objects.get(id=Id)
    #     context = {'c':committee, 'topicList':topic}
    return render(request, "utils/read_more.html", context)

def show_all_view(request, iden, item):
    if iden[0] == 'h':
        Id = iden[2:]
        # print(Id)
        hansard = Hansard.objects.get(id=Id)
        if item == 'terms':
            setlist = hansard.list_all_terms()
        else:
            setlist = hansard.list_all_people()
        context = {'hansard':hansard,'setlist':setlist, 'item':item}
    if iden[0] == 'c':
        Id = iden[2:]
        # print(Id)
        committee = Committee.objects.get(id=Id)
        if item == 'terms':
            setlist = committee.list_all_terms()
        else:
            setlist = committee.list_all_people()
        context = {'committee':committee,'setlist':setlist, 'item':item}
    return render(request, "utils/show_all.html", context)


def committee_reprocess(request, organization, parliament, session, iden):
    print('committee reprocess')
    # organization = None
    if organization == 'senate':
        c = CommitteeMeeting.objects.exclude(committee__Organization='House').filter(ParliamentNumber=parliament, SessionNumber=session, id=iden).select_related('committee', 'committee__chair__person')[0]
        if 'Subcommittee' in c.committee.Title:
            title = 'Senate Committee'
        else:
            title = 'Senate Committee'
    else:
        c = CommitteeMeeting.objects.exclude(committee__Organization='Senate').filter(ParliamentNumber=parliament, SessionNumber=session, id=iden).select_related('committee', 'committee__chair__person')[0]
        title = 'House Committee'
    get_senate_committee_transcript(c)
    return render(request, "utils/dummy.html", {'result':'success'})
    
def hansard_reprocess(request, organization, parliament, session, iden):
    print('hansard reprocess')
    # organization = None
    if organization == 'senate':
        h = Hansard.objects.filter(Organization='Senate', ParliamentNumber=parliament, SessionNumber=session, id=iden)[0]
        title = 'Senate Hansard %s' %(str(h.Title))
    else:
        h = Hansard.objects.filter(Organization='House of Commons', ParliamentNumber=parliament, SessionNumber=session, pub_iden=iden)[0]
        title = 'House %s' %(str(h.Title))
    add_senate_hansard(h.gov_page, True)
    return render(request, "utils/dummy.html", {'result':'success'})