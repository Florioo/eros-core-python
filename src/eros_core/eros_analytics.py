import time
from dataclasses import dataclass, field


ALPHA = 0.9


@dataclass
class ErosStreamAnalytics:
    prev_bytes = 0
    total_bytes = 0
    last_flush_time = time.time()
    last_delta = 0
    deltas: list[float] = field(default_factory=list)

    def register_data(self, size_bytes):
        self.total_bytes += size_bytes

    def get_rate(self):
        """Get the rate of the channel in bytes per second

        Returns:
            float: Rate in bits per second
        """
        if time.time() - self.last_flush_time < 0.5:
            return self.last_delta

        delta = (self.total_bytes - self.prev_bytes) / (
            time.time() - self.last_flush_time
        )

        self.deltas.append(delta)
        if len(self.deltas) > 10:
            self.deltas.pop(0)

        self.prev_bytes = self.total_bytes
        self.last_flush_time = time.time()

        # self.last_delta = ALPHA*delta + (1-ALPHA)*self.last_delta
        self.last_delta = sum(self.deltas) / len(self.deltas)

        return self.last_delta

    def get_total(self):
        """Get the total number of bytes received

        Returns:
            _type_: _description_
        """
        return self.total_bytes
