from django.urls import path , re_path
from . import consumers

websocket_urlpatterns = [
	path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
	re_path(r'ws/owner_messages/$', consumers.MessageConsumer.as_asgi())
]