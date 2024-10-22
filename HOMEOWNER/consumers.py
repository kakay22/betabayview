import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message

class NotificationConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		self.homeowner = self.scope['user'].homeowner
		self.group_name = f'homeowner_{self.homeowner.id}'
		await self.channel_layer.group_add(
			self.group_name,
			self.channel_name
		)
		await self.accept()

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(
			self.group_name,
			self.channel_name
		)

	async def send_notification(self, event):
		message = event['message']
		await self.send(text_data=json.dumps({
			'message': message
		}))


class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # Send existing messages to the client on connection
        messages = Message.objects.all().order_by('sent_time')  # You can filter by user if needed
        for message in messages:
            await self.send(text_data=json.dumps({
                'sender': message.sender,
                'message': message.message,
                'sent_time': message.sent_time.strftime('%Y-%m-%d %H:%M:%S'),
                'profile_picture_url': message.sender.profile_picture.url,  # Adjust according to your model
            }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Handle the case where a new message is sent (if applicable)

        # Broadcast the new message to all connected clients
        await self.send(text_data=json.dumps({
            'sender': text_data_json['sender'],
            'message': message,
            'created_at': text_data_json['created_at'],
            'profile_picture_url': text_data_json['profile_picture_url'],
        }))