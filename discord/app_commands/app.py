import aiohttp
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response, JSONResponse, PlainTextResponse
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from .. import utils
from ..interactions import Interaction
from .tree import CommandTree
from ..http import HTTPClient
import asyncio
from .errors import AppCommandError
from ..interactions import Interaction
import json


class App(FastAPI):
    def __init__(self, application_id, public_key, token, **kwargs):
        super().__init__(**kwargs)
        self.application_id = application_id
        self.verify_key = VerifyKey(bytes.fromhex(public_key))
        self.token = token
        self.tree = CommandTree(app=self)
        self.add_route('/interactions', self.interactions, ['POST'], include_in_schema=False)
        self.add_api_route('/sync', self.sync, methods=['GET'], include_in_schema=False)
        self.router.add_event_handler('startup', self.startup)
        self.router.add_event_handler('shutdown', self.shutdown)

    async def startup(self):
        loop = asyncio.get_running_loop()
        self.http = HTTPClient(loop)
        self.tree._http = self.http
        await self.http.static_login(self.token, get=False)

    async def shutdown(self):
        await self.http._HTTPClient__session.close()

    async def sync(self):
        return PlainTextResponse('\n'.join(repr(i) for i in await self.tree.sync()))

    async def interactions(self, request: Request):
        signature = request.headers.get('X-Signature-Ed25519')
        timestamp = request.headers.get('X-Signature-Timestamp')
        body = await request.body()
        try:
            self.verify_key.verify(str(timestamp).encode() + body, bytes.fromhex(signature))
        except BadSignatureError:
            return Response('invalid request signature', 401)
        data = await request.json()
        interaction = Interaction(data=data, app=self)

        try:
            if data['type'] in (2, 4) and self.tree: # application command and auto complete
                try:
                    await self.tree._call(interaction)
                except AppCommandError as e:
                    await self.tree._dispatch_error(interaction, e)
            elif data['type'] == 3:  # interaction component
                # These keys are always there for this interaction type
                # inner_data = data['data']
                # custom_id = inner_data['custom_id']
                # component_type = inner_data['component_type']
                # self._view_store.dispatch_view(component_type, custom_id, interaction)
                pass
            elif data['type'] == 5:  # modal submit
                # These keys are always there for this interaction type
                # inner_data = data['data']
                # custom_id = inner_data['custom_id']
                # components = inner_data['components']
                pass
        except Exception as e:
            raise e
        else:
            return JSONResponse({'type': 1})