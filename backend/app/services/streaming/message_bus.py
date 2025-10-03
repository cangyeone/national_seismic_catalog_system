from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Protocol

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    """Metadata returned after a message is published to the bus."""

    topic: str
    partition: int | None = None
    offset: int | None = None
    headers: Dict[str, str] | None = None


class MessageBus(Protocol):
    """Abstract interface for streaming message buses such as Kafka."""

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def publish(self, topic: str, key: str | None, value: Dict[str, Any]) -> PublishResult: ...

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
        *,
        group_id: str | None = None,
    ) -> None: ...


class InMemoryMessageBus:
    """Fallback message bus used for local development and testing."""

    def __init__(self) -> None:
        self._topics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._started = False

    async def start(self) -> None:  # pragma: no cover - trivial
        self._started = True

    async def stop(self) -> None:  # pragma: no cover - trivial
        self._topics.clear()
        self._subscribers.clear()
        self._started = False

    async def publish(self, topic: str, key: str | None, value: Dict[str, Any]) -> PublishResult:
        if not self._started:
            await self.start()
        async with self._lock:
            messages = self._topics[topic]
            messages.append({"key": key, "value": value})
            offset = len(messages) - 1
        await asyncio.gather(
            *[subscriber(value) for subscriber in list(self._subscribers.get(topic, []))]
        )
        return PublishResult(topic=topic, partition=0, offset=offset)

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
        *,
        group_id: str | None = None,
    ) -> None:
        if not self._started:
            await self.start()
        async with self._lock:
            self._subscribers[topic].append(handler)


class KafkaMessageBus:
    """Kafka-backed implementation that can be enabled in production deployments."""

    def __init__(
        self,
        bootstrap_servers: str,
        *,
        security_protocol: str | None = None,
        sasl_mechanism: str | None = None,
        sasl_username: str | None = None,
        sasl_password: str | None = None,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.security_protocol = security_protocol
        self.sasl_mechanism = sasl_mechanism
        self.sasl_username = sasl_username
        self.sasl_password = sasl_password
        self._producer = None
        self._consumer_tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        if self._producer is not None:
            return
        try:
            from aiokafka import AIOKafkaProducer  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("aiokafka is required for KafkaMessageBus") from exc

        config: Dict[str, Any] = {"bootstrap_servers": self.bootstrap_servers}
        if self.security_protocol:
            config["security_protocol"] = self.security_protocol
        if self.sasl_mechanism:
            config["sasl_mechanism"] = self.sasl_mechanism
        if self.sasl_username:
            config["sasl_plain_username"] = self.sasl_username
        if self.sasl_password:
            config["sasl_plain_password"] = self.sasl_password

        self._producer = AIOKafkaProducer(**config)
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None
        for task in self._consumer_tasks:
            task.cancel()
        self._consumer_tasks.clear()

    async def publish(self, topic: str, key: str | None, value: Dict[str, Any]) -> PublishResult:
        if self._producer is None:
            await self.start()
        assert self._producer is not None  # for mypy
        import json

        future = await self._producer.send_and_wait(
            topic,
            json.dumps(value).encode("utf-8"),
            key=key.encode("utf-8") if key else None,
        )
        return PublishResult(topic=topic, partition=future.partition, offset=future.offset)

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
        *,
        group_id: str | None = None,
    ) -> None:
        try:
            from aiokafka import AIOKafkaConsumer  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("aiokafka is required for KafkaMessageBus consumers") from exc

        config: Dict[str, Any] = {
            "bootstrap_servers": self.bootstrap_servers,
            "group_id": group_id or "catalog-consumer",
            "enable_auto_commit": False,
            "auto_offset_reset": "latest",
        }
        if self.security_protocol:
            config["security_protocol"] = self.security_protocol
        if self.sasl_mechanism:
            config["sasl_mechanism"] = self.sasl_mechanism
        if self.sasl_username:
            config["sasl_plain_username"] = self.sasl_username
        if self.sasl_password:
            config["sasl_plain_password"] = self.sasl_password

        consumer = AIOKafkaConsumer(topic, **config)
        await consumer.start()

        async def _consume() -> None:
            try:
                import json

                async for record in consumer:
                    try:
                        payload = json.loads(record.value.decode("utf-8"))
                    except json.JSONDecodeError:
                        logger.exception("Failed to decode Kafka message")
                        continue
                    await handler(payload)
            finally:
                await consumer.stop()

        task = asyncio.create_task(_consume())
        self._consumer_tasks.append(task)


__all__ = [
    "MessageBus",
    "PublishResult",
    "InMemoryMessageBus",
    "KafkaMessageBus",
]
