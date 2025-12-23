from collections import deque


class RingBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def add(self, item):
        """Add item to the buffer (removes oldest if full)"""
        self.buffer.append(item)

    def get(self):
        """Get the current buffer as a list"""
        return list(self.buffer)

    def __str__(self):
        return str(self.buffer)

    def get_trailing_white_space(self) -> str:
        chars: list[str] = self.get()
        if len(chars) == 0:
            return ""
        upper = len(chars) - 1
        if not chars[upper].isspace():
            return ""
        lower = len(chars) - 1
        while lower > 0 and chars[lower].isspace():
            lower -= 1
        if lower > 0:
            lower += 1

        return ''.join(chars[lower:upper+1])

    def should_captlize_prev_word(self) -> bool:
        chars: list[str] = self.get()
        captilize_after = [".", "!", "?"]
        target_range = RingBuffer._get_prev_word_range(chars)
        if target_range is None:
            return False
        lower, _ = target_range
        if lower == 0:
            return False
        lower -= 1
        while lower > 0:
            if not chars[lower].isspace():
                break
            lower -= 1
        print(chars[lower:])
        return chars[lower] in captilize_after

    def get_prev_word(self) -> str:
        chars = self.get()
        target = RingBuffer._get_prev_word_range(chars)
        if target is None:
            return ""
        lower, upper = target
        return ''.join(chars[lower:upper+1])

    @staticmethod
    def _get_prev_word_range(chars: list[str]):
        if len(chars) == 0:
            return None
        upper = len(chars) - 1

        while chars[upper] == " ":
            upper -= 1
        if upper < 0 or chars[upper] == " ":
            return None
        lower = 0
        for i in range(upper, 0, -1):
            if chars[i] == ' ':
                lower = i+1
                break
        return (lower, upper)

    def clear(self):
        self.buffer.clear()

    def backspace(self):
        if not self.is_empty():
            self.buffer.pop()

    def ends_with(self, val: str):
        chars = self.get()

    def is_empty(self):
        return len(self.buffer) == 0

    def get_last(self):
        """Get the last inserted value"""
        if not self.is_empty():
            return self.buffer[-1]
        else:
            return None  # Return None if buffer is empty
