import json
import asyncio

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import sync_to_async

class PlayerConsumer(WebsocketConsumer):

    def connection_groups(self, **kwargs):
        """
        Called to return the list of groups to automatically add/remove
        this connection to/from.
        """
        return ["lobby"]
 
    def connect(self):
        """
        Perform things on connection start
        """
        print("hhhhhhhhhhhhhhhhhhhhhhh")
        self.accept()
 
    def receive(self, text_data):
        """
        Called when a message is received with either text or bytes
        filled out.
        """
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        self.send(text_data=json.dumps({
            'message': message
        }))
 
 
    def disconnect(self, message, **kwargs):
        """
        Perform things on connection close
        """
        pass
    
    '''
    async def connect(self):

        print("h")

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

     # Receive message from web socket
    async def receive(self, text_data):
        
        # ToDo: Send information to other participants

        # Send message to room group

        a = 0
    
    # Receive message from room group
    async def chat_message(self, event):
        
        # ToDo: Add received data to JSON
        a = 0

    async def send_to_client(self):
        
        # Send message to client
        while (True):
            self.channel_layer.group_send(
                self.room_group_name,
                {
                    #json_to_send
                }
            )
            await asyncio.sleep(0.05)

            # Wait for ... seconds
    '''