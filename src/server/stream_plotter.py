from pathlib import Path

from obspy import Catalog, Stream, UTCDateTime
from obspy.clients.fdsn import Client

IMAGE_DIRECTORY = 'files/images'
IMAGE_FILE_FORMAT = '.png'
IMAGE_SIZE_HOURLY = (1280, 250)
IMAGE_SIZE_DAY_PLOT = (2560, 1920)
OUTFILE_DPI = 150


class StreamPlotter:
    directory: Path

    def __init__(self, directory: Path):
        self.directory = directory

    @staticmethod
    def get_japan_earthquakes(client: Client, starttime: UTCDateTime, endtime: UTCDateTime) -> Catalog:
        try:
            return client.get_events(
                starttime=starttime,
                endtime=endtime,
                latitude=35.6895,
                longitude=139.6917,
                maxradius=15,
                maxmagnitude=6
            )
        except Exception as e:
            print(e)
            return Catalog()

    @staticmethod
    def get_sweden_earthquakes(client: Client, starttime: UTCDateTime, endtime: UTCDateTime) -> Catalog:
        try:
            return client.get_events(
                starttime=starttime,
                endtime=endtime,
                latitude=59.334591,
                longitude=18.063240,
                maxradius=15,
                maxmagnitude=6
            )
        except Exception as e:
            print(e)
            return Catalog()

    @staticmethod
    def get_global_earthquakes(client: Client, starttime: UTCDateTime, endtime: UTCDateTime) -> Catalog:
        try:
            return client.get_events(
                starttime=starttime,
                endtime=endtime,
                minmagnitude=6
            )
        except Exception as e:
            print(e)
            return Catalog()

    @staticmethod
    def get_plot_color(stream: Stream) -> str:
        day_of_year = stream[0].stats.starttime.julday
        if day_of_year % 2 == 0:
            return "black"
        else:
            return "blue"

    async def save_day_plot(self, stream: Stream) -> None:
        starttime = stream[0].stats.starttime
        endtime = stream[0].stats.endtime
        print("Plotting day plot for stream with starttime:", starttime)
        image_file_name = 'day_' + str(starttime.datetime.day) + IMAGE_FILE_FORMAT
        image_file_path = self.directory / image_file_name

        try:
            client = Client("IRIS")
            cat = StreamPlotter.get_sweden_earthquakes(client, starttime, endtime)
            cat += StreamPlotter.get_global_earthquakes(client, starttime, endtime)

            stream.plot(
                title=starttime.datetime,
                size=IMAGE_SIZE_DAY_PLOT,
                dpi=OUTFILE_DPI,
                type="dayplot",
                outfile=image_file_path,
                events=cat,
                vertical_scaling_range=500,
            )
        except Exception as e:
            print("Failed to plot day plot.", e)

    async def save_hour_plot(self, stream: Stream, hour: int) -> None:
        image_file_name = 'hour_' + str(hour) + IMAGE_FILE_FORMAT
        image_file_path = self.directory / image_file_name
        endtime = stream[0].stats.endtime

        stream.plot(
            color=StreamPlotter.get_plot_color(stream),
            size=IMAGE_SIZE_HOURLY,
            dpi=OUTFILE_DPI,
            outfile=image_file_path,
            starttime=(endtime - 60 * 60),
            endtime=endtime)

    async def save_last_10_minutes_plot(self, stream: Stream) -> None:
        # Always create latest.png from last minute
        image_file_name = 'last_10_minutes' + IMAGE_FILE_FORMAT
        image_file_path = self.directory / image_file_name
        endtime = stream[0].stats.endtime
        starttime = (endtime - (10 * 60))
        stream.plot(
            color=StreamPlotter.get_plot_color(stream),
            size=IMAGE_SIZE_HOURLY,
            dpi=OUTFILE_DPI,
            outfile=image_file_path,
            starttime=starttime,
            endtime=endtime)

    async def save_last_60_minutes_plot(self, stream: Stream) -> None:
        # Always create latest.png from last minute
        image_file_name = 'last_60_minutes' + IMAGE_FILE_FORMAT
        image_file_path = self.directory / image_file_name
        endtime = stream[0].stats.endtime
        starttime = (endtime - (60 * 60))
        stream.plot(
            color=StreamPlotter.get_plot_color(stream),
            size=IMAGE_SIZE_HOURLY,
            dpi=OUTFILE_DPI,
            outfile=image_file_path,
            starttime=starttime,
            endtime=endtime)
