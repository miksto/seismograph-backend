from typing import List


class DataBox(object):
    max_size: int
    received_data: List[int]
    data_to_upload: List[int]

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.received_data = []
        self.data_to_upload = []

    def add(self, data_point: int) -> None:
        self.received_data.append(data_point)

    def is_full(self) -> bool:
        return len(self.received_data) >= self.max_size

    def prepare_for_data_upload(self):
        self.data_to_upload = self.received_data
        self.received_data = []
