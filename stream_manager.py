
import os
import datetime
from pathlib import Path
import numpy
from obspy import UTCDateTime, read, Trace, Stream

MSEED_DIRECTORY = 'files/mseed'

class StreamManager:
  wrapped_stream = None

  @staticmethod
  def create_dirs():
    if not os.path.exists(MSEED_DIRECTORY):
      os.makedirs(MSEED_DIRECTORY)
  
  @staticmethod
  def _stream_file_name(date):
    return MSEED_DIRECTORY + '/day_' + str(date.day) + '.mseed'

  @staticmethod
  def _is_stream_valid_for_current_date(stream):
    current_date = datetime.datetime.today().date()
    stream_start_date = stream[0].stats.starttime.datetime.date()
    return stream_start_date == current_date

  @staticmethod
  def _create_new_stream():
    data = numpy.array([], dtype='int16')
    stats = {'network': 'BW', 'station': 'MIK', 'location': '',
            'channel': 'Z', 'npts': len(data), 'sampling_rate': 10,
            'mseed': {'dataquality': 'D'}}
    start_time = datetime.datetime.now()

    stats['starttime'] = UTCDateTime(start_time)
    stream = Stream([Trace(data=data, header=stats)])
    return stream

  async def get_wrapped_stream(self):
    if self.wrapped_stream is None:
      await self._init_wrapped_stream()
    return self.wrapped_stream

  async def append_values(self, values):
    stream = await self.get_wrapped_stream()
    data = numpy.array(values, dtype='int16')
    stream[0].data = numpy.append(stream[0].data, data)
    
    # Update sample rate
    time_delta = (datetime.datetime.now() - stream[0].stats.starttime.datetime).total_seconds()
    sampling_rate = stream[0].stats.npts / time_delta
    stream[0].stats.sampling_rate = sampling_rate

  async def _init_wrapped_stream(self):
    current_date = datetime.datetime.today().date()
    file_name = StreamManager._stream_file_name(current_date)

    if self.wrapped_stream is None:
      if Path(file_name).is_file():
        stream = read(file_name, dtype='int16')
        
        # Stream date must match current date. It could be last month's stream
        if StreamManager._is_stream_valid_for_current_date(stream):
          self.wrapped_stream = stream
      
    # If current_stream still is None, create a new one
    if self.wrapped_stream is None:
      self.wrapped_stream = StreamManager._create_new_stream()

  def is_valid_for_current_date(self):
    return StreamManager._is_stream_valid_for_current_date(self.wrapped_stream)

  async def save_to_file(self):
    stream_start_date = self.wrapped_stream[0].stats.starttime.datetime.date()
    file_name = StreamManager._stream_file_name(stream_start_date)
    self.wrapped_stream.write(file_name)

  def begin_new_stream(self):
    self.wrapped_stream = StreamManager._create_new_stream()