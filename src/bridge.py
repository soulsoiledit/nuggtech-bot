import logging
import re
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from typing import NamedTuple, override

from discord import Color
from websockets.asyncio import client
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from websockets.typing import Data

logger = logging.getLogger("discord.nugg")


class Config(NamedTuple):
  token: str

  bridge_channel: int
  log_channel: int

  avatar: str
  name_color: Color
  reply_color: Color


class Server(NamedTuple):
  name: str
  display: str
  joinname: str
  color: Color

  @override
  def __str__(self) -> str:
    return self.name


class MSG(NamedTuple):
  bridge: "Bridge"
  server: "Server"
  message: str

  @override
  def __str__(self) -> str:
    return "{}@{}: {}".format(
      self.server.name,
      self.bridge.name,
      self.message,
    )


@dataclass
class Bridge:
  name: str
  ip: str
  port: int
  password: str
  servers: list[Server]
  websocket: client.ClientConnection | None = None

  uri: str = field(init=False)
  _servers: dict[str, Server] = field(init=False)

  def __post_init__(self):
    self.uri = f"ws://{self.ip}:{self.port}/taurus"
    self._servers = {server.name: server for server in self.servers}

  async def connect(self) -> AsyncGenerator[MSG]:
    async for websocket in client.connect(self.uri):
      await websocket.send(self.password)
      self.websocket = websocket
      logger.info(f"Connected to {self.name}")
      try:
        async for resp in websocket:
          if parsed := self._parse(resp):
            yield parsed
      except ConnectionClosedOK:
        logger.warning(f"Not connected to {self.name}!")
      except ConnectionClosedError:
        logger.warning(f"Lost connection with {self.name}!")
      finally:
        logger.info(f"Closed connection with {self.name}")

  async def close(self):
    if self.websocket:
      await self.websocket.close()

  async def send(self, message: str):
    if self.websocket:
      await self.websocket.send(message)

  # starts a new connection to capture a specific response
  # kinda wasteful..., but taurus makes it very hard otherwise
  async def sendr(
    self,
    command: str,
    accept: Callable[[str], bool] = lambda x: not x.startswith("MSG"),
  ) -> str:
    async for websocket in client.connect(self.uri):
      await websocket.send(self.password)
      await websocket.send(command)

      async for response in websocket:
        response = str(response)

        if not accept(response):
          continue

        logger.debug(f"{self.name}: {response}")
        sp = response.split(maxsplit=1)
        if len(sp) == 1:
          return ""
        return sp[1]
    return ""

  def _parse(self, response: Data) -> MSG | None:
    match = re.fullmatch(
      r"^MSG \[(.*)\] (.*)$",
      str(response),
    )

    if match is None:
      return
    server, message = match.groups()

    return MSG(
      self,
      self._servers[server],
      message,
    )
