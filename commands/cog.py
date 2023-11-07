from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject

from .command import Command
from .event import Event


if TYPE_CHECKING:
    from network import Client


class CogMeta(type):
    __commands__: dict[str, Command]
    __events__: dict[str, list[Event]]

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        commands = {}
        events = {}
        for base in reversed(self.__mro__):
            for value in base.__dict__.values():
                if isinstance(value, Command):
                    commands[value.name] = value
                elif isinstance(value, Event):
                    if not (lst := events.get(value.name, [])):
                        events[value.name] = lst
                    lst.append(value)

        self.__commands__ = commands
        self.__events__ = events
        return self


class CogCore(type(QObject), CogMeta):
    ...


class Cog(QObject, metaclass=CogCore):
    __commands__: dict[str, Command]
    __events__: dict[str, list[Event]]

    def __new__(cls, *args, **kwargs):
        self = super(Cog, cls).__new__(cls)
        for command in self.__commands__.values():
            command._instance = self
        for events in self.__events__.values():
            for event in events:
                event._instance = self

        return self

    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client

    def unload(self):
        ...
