"""Chat channels module with plugin architecture."""

from tradeclaw.channels.base import BaseChannel
from tradeclaw.channels.manager import ChannelManager

__all__ = ["BaseChannel", "ChannelManager"]
