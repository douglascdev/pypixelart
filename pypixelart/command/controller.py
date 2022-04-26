from dataclasses import dataclass, field

from pypixelart.command.command import Command


@dataclass
class CommandController:
    undo_stack: list[Command] = field(default_factory=list)
    redo_stack: list[Command] = field(default_factory=list)

    def execute(self, command: Command) -> None:
        command.execute()
        self.redo_stack.clear()
        self.undo_stack.append(command)

    def undo(self) -> None:
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)

    def redo(self) -> None:
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.redo()
            self.undo_stack.append(command)
