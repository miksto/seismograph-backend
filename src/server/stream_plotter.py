from obspy import Catalog
from obspy.clients.fdsn import Client

IMAGE_DIRECTORY = 'files/images'
IMAGE_FILE_FORMAT = '.png'
IMAGE_SIZE_HOURLY = (2560, 500)
IMAGE_SIZE_DAY_PLOT = (2560, 1920)
OUTFILE_DPI = 150


class StreamPlotter:

    def __init__(self, directory):
        self.directory = directory

    @staticmethod
    def get_japan_earthquakes(client, starttime, endtime):
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
    def get_sweden_earthquakes(client, starttime, endtime):
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
    def get_global_earthquakes(client, starttime, endtime):
        try:
            return client.get_events(
                starttime=starttime,
                endtime=endtime,
                minmagnitude=6
            )
        except Exception as e:
            print(e)
            return Catalog()

    async def save_day_plot(self, stream):
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

    async def save_hour_plot(self, stream, hour):
        image_file_name = 'hour_' + str(hour) + IMAGE_FILE_FORMAT
        image_file_path = self.directory / image_file_name
        endtime = stream[0].stats.endtime
        stream.plot(
            size=IMAGE_SIZE_HOURLY,
            dpi=OUTFILE_DPI,
            outfile=image_file_path,
            starttime=(endtime - 60 * 60),
            endtime=endtime)

    async def save_last_10_minutes_plot(self, stream):
        # Always create latest.png from last minute
        image_file_name = 'last_10_minutes' + IMAGE_FILE_FORMAT
        image_file_path = self.directory / image_file_name
        endtime = stream[0].stats.endtime
        starttime = (endtime - (10 * 60))
        stream.plot(
            size=IMAGE_SIZE_HOURLY,
            dpi=OUTFILE_DPI,
            outfile=image_file_path,
            starttime=starttime,
            endtime=endtime)

    async def save_last_60_minutes_plot(self, stream):
        # Always create latest.png from last minute
        image_file_name = 'last_60_minutes' + IMAGE_FILE_FORMAT
        image_file_path = self.directory / image_file_name
        endtime = stream[0].stats.endtime
        starttime = (endtime - (60 * 60))
        stream.plot(
            size=IMAGE_SIZE_HOURLY,
            dpi=OUTFILE_DPI,
            outfile=image_file_path,
            starttime=starttime,
            endtime=endtime)
