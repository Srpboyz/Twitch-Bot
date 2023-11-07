from __future__ import annotations
from typing import TYPE_CHECKING

from .user import User

from dateutil.parser import parse

if TYPE_CHECKING:
    from network import HTTP


class BaseEvent:
    def __init__(self, event_name: str) -> None:
        self.event_name = event_name


class Event(BaseEvent):
    def __init__(self, event_name: str, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(event_name)
        streamer = http.client.streamer
        self.chatter = (
            streamer.get_chatter(int(payload["user_id"]))
            if not payload.get("is_anonymous", False)
            else None
        )
        if not self.chatter:
            self.chatter = User.from_user_id(payload["user_id"], streamer, http)
            streamer.add_chatter(self.chatter)
            http.client.dispatch("on_chatter_join", self.chatter)


class StreamOnline(BaseEvent):
    def __init__(self, payload: dict[str, str], _) -> None:
        super().__init__("on_stream_online")
        self.type = payload["type"]


class StreamOffline(BaseEvent):
    def __init__(self, _, __) -> None:
        super().__init__("on_stream_offline")


class FollowEvent(Event):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__("follow_event", payload, http)


class BanEvent(Event):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__("ban_event", payload, http)
        id = int(payload["moderator_user_id"])
        self.moderator = http.client.streamer.get_chatter(id)
        if not self.moderator:
            self.moderator = User.from_user_id(id, http.client.streamer, http)
        self.reason = payload["reason"]
        self.timeout = (
            (parse(payload["ends_at"]) - parse(payload["banned_at"])).seconds
            if not payload["is_permanent"]
            else 0
        )


class RaidEvent(Event):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        payload["user_id"] = payload.pop("from_broadcaster_user_id")
        super().__init__("raid_event", payload, http)
        self.viewers = int(payload["viewers"])


class SubscribeEvent(Event):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__("subscribe_event", payload, http)
        self.tier = payload["tier"]
        self.is_gift = payload.get("is_gift", False)


class GiftSubEvent(SubscribeEvent):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(payload, http)
        self.event_name = "gift_sub_event"
        self.total = payload["total"]
        self.is_anonymous = payload["is_anonymous"]
        self.cummulative_total = (
            payload["cumulative_total"] if not self.is_anonymous else 0
        )
        self.is_gift = True


class ReSubscribeEvent(SubscribeEvent):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__(payload, http)
        self.event_name = "resub_event"
        self.message = payload["message"]["text"]
        self.consecutive_months = payload["cumulative_months"]
        self.streak_months = payload["streak_months"]
        self.duration_months = payload["duration_months"]


class CheersEvent(Event):
    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__("cheers_event", payload, http)
        self.is_anonymous = payload["is_anonymous"]
        self.message = payload["message"]
        self.bits = int(payload["bits"])


class RewardEvent(Event):
    class Reward:
        def __init__(
            self,
            id: str,
            reward_id: str,
            title: str,
            prompt: str,
            cost: int,
            user_input: str,
        ) -> None:
            self.id = id
            self.reward_id = reward_id
            self.title = title
            self.prompt = prompt
            self.cost = int(cost)
            self.user_input = user_input

    def __init__(self, payload: dict[str, str], http: HTTP) -> None:
        super().__init__("reward_event", payload, http)
        self.reward = self.Reward(
            **payload["reward"],
            reward_id=payload["id"],
            user_input=payload["user_input"],
        )
