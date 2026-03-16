import pytest

def test_subscribe_and_emit():
    from engram_ai.events.bus import EventBus
    bus = EventBus()
    received = []
    bus.on("test.event", lambda payload: received.append(payload))
    bus.emit("test.event", {"data": "hello"})
    assert received == [{"data": "hello"}]

def test_multiple_subscribers():
    from engram_ai.events.bus import EventBus
    bus = EventBus()
    results = []
    bus.on("evt", lambda p: results.append("a"))
    bus.on("evt", lambda p: results.append("b"))
    bus.emit("evt", {})
    assert results == ["a", "b"]

def test_unsubscribe():
    from engram_ai.events.bus import EventBus
    bus = EventBus()
    received = []
    callback = lambda p: received.append(p)
    bus.on("evt", callback)
    bus.off("evt", callback)
    bus.emit("evt", {"data": 1})
    assert received == []

def test_emit_no_subscribers():
    from engram_ai.events.bus import EventBus
    bus = EventBus()
    bus.emit("no.listeners", {})

def test_fail_open_on_subscriber_error():
    from engram_ai.events.bus import EventBus
    bus = EventBus()
    results = []
    def bad_callback(p):
        raise ValueError("oops")
    def good_callback(p):
        results.append("ok")
    bus.on("evt", bad_callback)
    bus.on("evt", good_callback)
    bus.emit("evt", {})
    assert results == ["ok"]

def test_different_events_are_isolated():
    from engram_ai.events.bus import EventBus
    bus = EventBus()
    results = []
    bus.on("event_a", lambda p: results.append("a"))
    bus.on("event_b", lambda p: results.append("b"))
    bus.emit("event_a", {})
    assert results == ["a"]
