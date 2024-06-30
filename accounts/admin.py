from django.contrib import admin


from accounts.models import *
from posts.models import *
from blockchain.models import *


class SonetAdmin(admin.ModelAdmin):
    list_display = ["Title"]
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Sonet

class UserAdmin(admin.ModelAdmin):
    list_display = ["display_name", 'last_login', 'is_active', 'date_joined', 'slug', 'email']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = User

class UserPubKeyAdmin(admin.ModelAdmin):
    list_display = ["id", 'created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = UserPubKey

class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", 'created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Notification

class WalletAdmin(admin.ModelAdmin):
    list_display = ["id", 'created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Wallet

class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", 'created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Transaction

class PersonAdmin(admin.ModelAdmin):
    list_display = ["LastName", "FirstName", 'GovProfilePage']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = ['LastName']
    class Meta:
        model = Person

class RoleAdmin(admin.ModelAdmin):
    list_display = ["Position", "Person_obj", "Title", "EndDate", 'created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = ['Person_obj', 'Position']
    class Meta:
        model = Role


class PartyAdmin(admin.ModelAdmin):
    list_display = ["Name", 'AltName', 'gov_level', 'Region_obj']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Party

# class RidingAdmin(admin.ModelAdmin):
#     list_display = ["name", 'id']
#     list_display_links = []
#     list_editable = []
#     list_filter = []
#     search_fields = []
#     class Meta:
        # model = Riding

class DistrictAdmin(admin.ModelAdmin):
    list_display = ["Name", 'Region_obj', 'gov_level', 'id']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = District

class RegionAdmin(admin.ModelAdmin):
    list_display = ["Name", 'AbbrName']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Region

class KeyphraseAdmin(admin.ModelAdmin):
    list_display = ["text", 'chamber', 'id']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = ['text']
    class Meta:
        model = Keyphrase

class KeyphraseTrendAdmin(admin.ModelAdmin):
    list_display = ["text", 'total_occurences', 'chamber']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = ['text']
    class Meta:
        model = KeyphraseTrend

class BillAdmin(admin.ModelAdmin):
    list_display = ["NumberCode", "Title", "chamber", 'created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = ['NumberCode']
    class Meta:
        model = Bill

class BillVersionAdmin(admin.ModelAdmin):
    list_display = ["NumberCode", "Version", 'DateTime', 'Current', 'empty']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = ['code']
    class Meta:
        model = BillVersion


class MotionAdmin(admin.ModelAdmin):
    list_display = ['VoteNumber', "DateTime", 'chamber',  'created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Motion


class VoteAdmin(admin.ModelAdmin):
    list_display = ['created', 'vote_number', "PersonOfficialFullName", 'IsVoteYea','IsVoteNay']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Vote

class SprenAdmin(admin.ModelAdmin):
    list_display = ['created', 'type', "DateTime"]
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Spren

class SprenItemAdmin(admin.ModelAdmin):
    list_display = ['created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = SprenItem

class DailyAdmin(admin.ModelAdmin):
    list_display = ['created', "DateTime"]
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Daily

class MeetingAdmin(admin.ModelAdmin):
    list_display = ['chamber', 'Title', 'DateTime', 'created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Meeting

# class DebateItemAdmin(admin.ModelAdmin):
#     list_display = ["Person", "Debate", "EventId", 'created']
#     list_display_links = []
#     list_editable = []
#     list_filter = []
#     search_fields = []
#     class Meta:
#         model = DebateItem

# class QuestionAdmin(admin.ModelAdmin):
#     list_display = ["questioner_name", 'QuestionNumber', "HansardTitle"]
#     list_display_links = []
#     list_editable = []
#     list_filter = []
#     search_fields = []
#     class Meta:
#         model = Question

class CommitteeAdmin(admin.ModelAdmin):
    list_display = ['chamber', 'Title', 'Code']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = ['Title']
    class Meta:
        model = Committee

# class CommitteeMeetingAdmin(admin.ModelAdmin):
#     list_display = ['Title', 'DateTimeStart', 'chamber', "GovernmentNumber", "SessionNumber", 'created', 'Event', 'Code']
#     list_display_links = []
#     list_editable = []
#     list_filter = []
#     search_fields = []
#     class Meta:
#         model = CommitteeMeeting

class StatementAdmin(admin.ModelAdmin):
    list_display = ["id", "Person_obj", 'created', 'DateTime']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Statement

class PostAdmin(admin.ModelAdmin):
    list_display = ['DateTime', 'pointerType', 'pointerId']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = ['pointerType', 'pointerId']
    class Meta:
        model = Post

class TopPostAdmin(admin.ModelAdmin):
    list_display = ['created', 'cycle', 'chamber', 'country']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = TopPost

class ArchiveAdmin(admin.ModelAdmin):
    list_display = ['DateTime', 'created', 'pointerType']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = ['pointerType']
    class Meta:
        model = Post

class InteractionAdmin(admin.ModelAdmin):
    list_display = ['created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Interaction

class UserVoteAdmin(admin.ModelAdmin):
    list_display = ['created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = UserVote

class SavePostAdmin(admin.ModelAdmin):
    list_display = ['created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = SavePost

# class FollowAdmin(admin.ModelAdmin):
#     list_display = ['created']
#     list_display_links = []
#     list_editable = []
#     list_filter = []
#     search_fields = []
#     class Meta:
#         model = Follow

class AgendaAdmin(admin.ModelAdmin):
    list_display = ['DateTime', 'created', 'chamber', 'id']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Agenda

class AgendaTimeAdmin(admin.ModelAdmin):
    list_display = ['DateTime', 'created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = AgendaTime

class AgendaItemAdmin(admin.ModelAdmin):
    list_display = ['DateTime', 'created', 'Text', 'Bill_obj_id']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = AgendaItem
        
class GovernmentAdmin(admin.ModelAdmin):
    list_display = ['gov_level', 'GovernmentNumber', 'SessionNumber', 'StartDate']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Government

class ElectionAdmin(admin.ModelAdmin):
    list_display = ['chamber', 'type', 'end_date']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Election

class UpdateAdmin(admin.ModelAdmin):
    list_display = ['pointerId', 'pointerType', 'blockchainId', 'DateTime']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = ['pointerType', 'pointerId']
    class Meta:
        model = Update

class DataPacketAdmin(admin.ModelAdmin):
    list_display = ['id', 'created']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = DataPacket

class NodeAdmin(admin.ModelAdmin):
    list_display = ['id',]
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Node

class ValidatorAdmin(admin.ModelAdmin):
    list_display = ['id',]
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Validator

class BlockAdmin(admin.ModelAdmin):
    list_display = ['id',]
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Block

class BlockchainAdmin(admin.ModelAdmin):
    list_display = ['id', 'genesisType', 'genesisId']
    list_display_links = []
    list_editable = []
    list_filter = []
    search_fields = []
    class Meta:
        model = Blockchain

admin.site.register(Sonet, SonetAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UserPubKey, UserPubKeyAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction, TransactionAdmin)

admin.site.register(Person, PersonAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Party, PartyAdmin)
# admin.site.register(Riding, RidingAdmin)
admin.site.register(District, DistrictAdmin)
admin.site.register(Region, RegionAdmin)

admin.site.register(Keyphrase, KeyphraseAdmin)
admin.site.register(KeyphraseTrend, KeyphraseTrendAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(BillVersion, BillVersionAdmin)
admin.site.register(Motion, MotionAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Spren, SprenAdmin)
admin.site.register(SprenItem, SprenItemAdmin)
admin.site.register(Daily, DailyAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(Statement, StatementAdmin)
# admin.site.register(Question, QuestionAdmin)
admin.site.register(Committee, CommitteeAdmin)
# admin.site.register(CommitteeMeeting, CommitteeMeetingAdmin)
# admin.site.register(CommitteeItem, CommitteeItemAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(TopPost, TopPostAdmin)
admin.site.register(Archive, ArchiveAdmin)
admin.site.register(Interaction, InteractionAdmin)
admin.site.register(UserVote, UserVoteAdmin)
admin.site.register(SavePost, SavePostAdmin)
# admin.site.register(Follow, FollowAdmin)

admin.site.register(Agenda, AgendaAdmin)
admin.site.register(AgendaTime, AgendaTimeAdmin)
admin.site.register(AgendaItem, AgendaItemAdmin)
admin.site.register(Government, GovernmentAdmin)
admin.site.register(Election, ElectionAdmin)
admin.site.register(Update, UpdateAdmin)

admin.site.register(DataPacket, DataPacketAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(Validator, ValidatorAdmin)
admin.site.register(Block, BlockAdmin)
admin.site.register(Blockchain, BlockchainAdmin)




