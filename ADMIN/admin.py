from django.contrib import admin
from .models import Secretary, Event, Comment, Property, Message, MaintenancePersonnel, AdminNotification, Log, PropertyImage, Announcement, AnnouncementComment, PaymentReminder, ChatbotResponse, Feedback, ChatConversation, ChatFeedback, ChatHistoryMessage, VisitRequest, PropertyModel, EmergencyContact

# Register your models here.
admin.site.register(Secretary)
admin.site.register(Event)
admin.site.register(Comment)
admin.site.register(Property)
admin.site.register(Message)
admin.site.register(MaintenancePersonnel)
admin.site.register(AdminNotification)
admin.site.register(Log)
admin.site.register(PropertyImage)
admin.site.register(AnnouncementComment)
admin.site.register(PaymentReminder)
admin.site.register(ChatbotResponse)
admin.site.register(ChatConversation)
admin.site.register(Feedback)
admin.site.register(ChatFeedback)
admin.site.register(ChatHistoryMessage)
admin.site.register(PropertyModel)
admin.site.register(EmergencyContact)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'content')


@admin.register(VisitRequest)
class VisitRequestAdmin(admin.ModelAdmin):
    list_display = ('visitor_full_name', 'visit_date', 'household_head', 'status', 'created_at')
    list_filter = ('status', 'household_head')
    search_fields = ('visitor_full_name', 'visitor_relation', 'purpose')