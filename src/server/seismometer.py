from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from obspy import Stream

from stream_manager import StreamManager
from stream_plotter import StreamPlotter

MSEED_FILES_DIRECTORY = 'mseed/'
IMAGE_FILES_DIRECTORY = 'images/'


class Seismometer(object):
    seismometer_id: str
    directory: Path
    last_saved_hour: int
    last_saved_minute: int
    stream_manager: StreamManager
    stream_plotter: StreamPlotter

    stats: Dict[str, Any] = None

    def __init__(self, seismometer_id: str, directory: Path):
        self.seismometer_id = seismometer_id
        self.directory = directory

        self.last_saved_hour = datetime.today().hour
        self.last_saved_minute = datetime.today().minute

        self.stream_manager = StreamManager(self.directory / MSEED_FILES_DIRECTORY)
        self.stream_plotter = StreamPlotter(self.directory / IMAGE_FILES_DIRECTORY)

    def create_folders(self) -> None:
        mseed_path = self.directory / MSEED_FILES_DIRECTORY
        image_path = self.directory / IMAGE_FILES_DIRECTORY

        if not mseed_path.exists():
            mseed_path.mkdir(parents=True)

        if not image_path.exists():
            image_path.mkdir(parents=True)

    async def handle_data(self, values: List[int], stats: Dict[str, Any]) -> None:
        self.stats = stats
        await self.stream_manager.append_values(values)
        await self.save_plots_and_mseed()

    async def get_last_seconds_of_data(self, seconds) -> List[int]:
        stream = await self.stream_manager.get_wrapped_stream()
        endtime = stream[0].stats.endtime
        starttime = endtime - seconds
        slice: Stream = stream.slice(starttime, endtime)
        return slice[0].data.tolist() if slice.count() > 0 else []

    async def save_plots_and_mseed(self) -> None:
        current_minute = datetime.today().minute
        current_hour = datetime.today().hour
        if self.last_saved_minute != current_minute:
            await self.stream_plotter.save_last_10_minutes_plot(await self.stream_manager.get_wrapped_stream())
            await self.stream_plotter.save_last_60_minutes_plot(await self.stream_manager.get_wrapped_stream())
            await self.stream_manager.save_to_file()
            self.last_saved_minute = current_minute

        if self.last_saved_hour != current_hour:
            await self.stream_plotter.save_hour_plot(await self.stream_manager.get_wrapped_stream(),
                                                     self.last_saved_hour)
            self.last_saved_hour = current_hour

        if not self.stream_manager.is_valid_for_current_date():
            await self.stream_plotter.save_day_plot(await self.stream_manager.get_wrapped_stream())

            self.stream_manager.begin_new_stream()
            await self.stream_manager.save_to_file()
