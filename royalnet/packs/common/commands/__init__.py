# Imports go here!
from .ping import PingCommand

# Enter the commands of your Pack here!
commands = [
    PingCommand,
]

# Don't change this, it should automatically generate __all__
__all__ = [command.__class__.__qualname__ for command in commands]