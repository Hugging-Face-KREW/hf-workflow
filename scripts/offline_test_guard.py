"""Optional pytest plugin: block real sockets during free experiment validation.

Usage: PYTHONPATH=scripts python -m pytest -p offline_test_guard
Remove API credential environment variables as well so optional clients do not
change deterministic test behavior. Mock transports remain usable.
"""
import socket


def pytest_sessionstart(session):
    def blocked(*args, **kwargs):
        raise OSError("Offline validation: real network connections are disabled")

    socket.socket.connect = blocked
    socket.socket.connect_ex = blocked
    socket.create_connection = blocked
