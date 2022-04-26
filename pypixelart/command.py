from typing import Protocol


class Command(Protocol):
    """
    Command class implemented by PyPixelArt actions, following the Command Design Pattern
    """

    def execute(self) -> None:
        ...

    def redo(self) -> None:
        ...

    def undo(self) -> None:
        ...
