"""Reactive Event Bus and Rule Engine for LightingEngine."""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from wled_engine.core import LightingEngine


@dataclass
class Event:
    """An asynchronous or synchronous event published to the lighting engine."""
    name: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class EventRule:
    """Declarative trigger rule mapping an event to a lighting engine action."""
    event_name: str
    action: str  # 'fade_layer', 'set_layer_opacity', 'transition_cue', 'master_brightness', 'set_layer_enabled'
    params: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Decoupled event broker managing listeners, reactive rules, and engine triggers."""

    def __init__(self, engine: LightingEngine | None = None) -> None:
        self.engine = engine
        self._handlers: dict[str, list[Callable[[Event, LightingEngine], None]]] = {}
        self._rules: list[EventRule] = []

    def bind_engine(self, engine: LightingEngine) -> None:
        """Bind or rebind target lighting engine."""
        self.engine = engine

    def subscribe(
        self,
        event_name: str,
        handler: Callable[[Event, LightingEngine], None],
    ) -> None:
        """Register a custom callback for an event name (or '*' for wildcard)."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        if handler not in self._handlers[event_name]:
            self._handlers[event_name].append(handler)

    def unsubscribe(
        self,
        event_name: str,
        handler: Callable[[Event, LightingEngine], None],
    ) -> bool:
        """Remove a registered callback."""
        if event_name in self._handlers and handler in self._handlers[event_name]:
            self._handlers[event_name].remove(handler)
            return True
        return False

    def add_rule(self, rule: EventRule) -> None:
        """Add a declarative reactive rule."""
        self._rules.append(rule)

    def remove_rules_for_event(self, event_name: str) -> int:
        """Remove all declarative rules matching an event name."""
        initial_len = len(self._rules)
        self._rules = [r for r in self._rules if r.event_name != event_name]
        return initial_len - len(self._rules)

    def publish(self, event_or_name: Event | str, **extra_data: Any) -> list[str]:
        """Publish an event, dispatching to rules and subscribers."""
        if isinstance(event_or_name, str):
            event = Event(name=event_or_name, data=extra_data)
        else:
            if extra_data:
                event_or_name.data.update(extra_data)
            event = event_or_name

        executed_actions: list[str] = []

        # 1. Execute declarative rules against bound engine
        if self.engine is not None:
            for rule in self._rules:
                if rule.event_name == event.name or rule.event_name == "*":
                    self._execute_rule(rule, event)
                    executed_actions.append(rule.action)

        # 2. Invoke specific handlers
        if event.name in self._handlers and self.engine is not None:
            for handler in self._handlers[event.name]:
                handler(event, self.engine)

        # 3. Invoke wildcard handlers
        if "*" in self._handlers and self.engine is not None:
            for handler in self._handlers["*"]:
                handler(event, self.engine)

        return executed_actions

    def _execute_rule(self, rule: EventRule, event: Event) -> None:
        """Execute a predefined declarative engine action."""
        if self.engine is None:
            return

        action = rule.action
        params = dict(rule.params)
        # Merge event data into params if provided
        params.update(event.data)

        if action == "fade_layer":
            layer_idx = int(params.get("layer", 0))
            target_opacity = float(params.get("target_opacity", 1.0))
            duration = float(params.get("duration_sec", 1.0))
            self.engine.fade_layer(layer_idx, target_opacity=target_opacity, duration_sec=duration)

        elif action == "set_layer_opacity":
            layer_idx = int(params.get("layer", 0))
            opacity = float(params.get("opacity", 1.0))
            self.engine.layer(layer_idx).opacity = opacity

        elif action == "set_layer_enabled":
            layer_idx = int(params.get("layer", 0))
            enabled = bool(params.get("enabled", True))
            self.engine.layer(layer_idx).enabled = enabled

        elif action == "transition_cue":
            cue_name = str(params.get("cue", params.get("name", "")))
            duration = float(params.get("duration_sec", 1.0))
            self.engine.transition_to_cue(cue_name, duration_sec=duration)

        elif action == "master_brightness":
            brightness = float(params.get("brightness", 1.0))
            self.engine.master_brightness = brightness
