from __future__ import annotations
from typing import Any, TYPE_CHECKING
import traceback
import json
import re

from PyQt6.QtCore import QObject

from .http import HTTP
from .websocket import WebSocket, EventSub
from commands import Context
from models import User, Message
import commands

if TYPE_CHECKING:
    from ui import MainWindow
    from models import Streamer


class Client(QObject):
    __cogs__: dict[str, commands.Cog]
    __commands__: dict[str, commands.Command]
    __events__: dict[str, list[commands.Event]]

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._settings = self._load_settings()
        self._client_id = self._settings["client-id"]
        self._token = self._settings["token"]
        self._user_id = None
        self._http = HTTP(self)
        self._ws = WebSocket(self)
        self._eventsub = EventSub(self)
        self.streamer: Streamer = None
        self.__cogs__ = {}
        self.__commands__ = {}
        self.__events__ = {}

    @property
    def window(self):
        return self._window

    def start(self) -> None:
        return self._ws.connect()

    def is_ready(self) -> bool:
        return self._ws._ready

    def _run_command(self, data: dict[str, Any], message: Message):
        args = (
            re.split(r"\s+", params)
            if (params := data["command"].get("botCommandParams"))
            else []
        )
        if "\U000e0000" in args:
            args.remove("\U000e0000")
        self.invoke(data["command"]["botCommand"], message, args)

    def get_command(self, name: str):
        return self.__commands__.get(name)

    def invoke(self, name: str, message: Message, args: list[str]):
        if not (command := self.get_command(name)):
            return
        ctx = Context(self, message, command, args)
        command(ctx)

    def send_message(self, message: str) -> Message | None:
        if not self.streamer or not message:
            return
        self._ws.sendTextMessage(f"PRIVMSG #{self._ws.nick} :{message}\r\n")
        message = Message(0, self, self.streamer, message)
        self.dispatch("on_message", message)
        return message

    def reply(self, message_id: int, message: str) -> None:
        if not self.streamer:
            return
        self._ws.sendTextMessage(
            f"@reply-parent-msg-id={message_id} PRIVMSG #{self._ws.nick} :{message}\r\n"
        )
        message = Message(0, self, self.streamer, message)
        self.dispatch("on_message", message)

    def on_stream_offline(self, _):
        self.streamer.chatters.clear()

    def on_event_error(self, event: commands.Event, error: Exception):
        print(f"Ignoring exception in event {event.name}")
        traceback.print_exception(type(error), error, error.__traceback__)

    def on_command_error(self, ctx: Context, error: Exception):
        print(f"Ignoring exception in command {ctx.command.name}")
        traceback.print_exception(type(error), error, error.__traceback__)

    def add_cog(self, cog: commands.Cog) -> commands.Cog:
        name = cog.__class__.__name__
        if self.__cogs__.get(name):
            raise Exception(f"Cog {name} already exists")
        self.__cogs__[name] = cog
        for command in cog.__commands__.keys():
            if self.__commands__.get(command):
                print(f"Cannot add command {command} as it already exists")
                cog.__commands__.pop(command)
                continue
        self.__commands__.update(cog.__commands__)
        for name, events in cog.__events__.items():
            if not (lst := self.__events__.get(name, [])):
                self.__events__[name] = lst
            lst.extend(events)
        return cog

    def remove_cog(self, cog: commands.Cog) -> None:
        if not self.__cogs__.pop(cog.__class__.__name__, None):
            raise Exception(f"Cog {cog.__class__.__name__} doesn't exist")
        for key in cog.__commands__:
            self.__commands__.pop(key)
        for name, events in cog.__events__.items():
            cli_evnts = self.__events__.get(name)
            for event in events:
                cli_evnts.remove(event)
        cog.unload()

    def dispatch(self, event: str, *args, **kwargs):
        for evnt in self.__events__.get(event, []):
            evnt(*args, **kwargs)

    def fetch_users(self, users: list[int, str]):
        users_data = self._http.fetch_users(users)
        return [User(**data, http=self._http) for data in users_data]

    def create_prediction(
        self, broadcaster_id: int, title: str, options: list[str], length: int = 120
    ):
        return self._http.create_prediction(broadcaster_id, title, options, length)

    def _load_settings(self) -> dict:
        with open("data/settings.json") as f:
            return json.load(f)

    def close(self):
        self._ws.close()
        self._eventsub.close()
