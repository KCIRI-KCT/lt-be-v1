import json
from channels.generic.websocket import AsyncWebsocketConsumer


class DetectionAlertConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming real-time AI detection alerts to clients.
    Subscribes clients to site-specific alert rooms: site_{site_id}_alerts.
    """

    async def connect(self):
        self.site_id = self.scope['url_route']['kwargs'].get('site_id')
        self.room_group_name = f"site_{self.site_id}_alerts"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
                if data.get('type') == 'ping':
                    await self.send(text_data=json.dumps({'type': 'pong'}))
            except Exception:
                pass

    async def alert_message(self, event):
        """
        Handler for event dispatched via group_send with type='alert.message'.
        Broadcasts alert event payload to connected WebSocket client.
        """
        await self.send(text_data=json.dumps(event))
