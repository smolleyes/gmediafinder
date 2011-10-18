# -*- coding:utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import os.path
import threading
import time

import gobject
import gst

STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_READY = 3

STATE_READING = 0
STATE_FINISHED = 1
STATE_CANCELED = 2

_STATE_MAPPING = {gst.STATE_PLAYING : STATE_PLAYING,
                  gst.STATE_PAUSED : STATE_PAUSED,
                  gst.STATE_NULL : STATE_READY}

__version__ = '1.0'

class Cache(object):
    '''
    Reads out the whole file object to avoid for example stream timeouts.
    Use :class:`Player`'s :meth:`play_cache` method to play this object.
    
    Attention: This starts a new thread for reading.
    If you want to cancel this thread you have to call the :meth:`cancel` method.
    If you call :class:`Player`'s :meth:`stop` method the :meth:`cancel` method is automatically called.
    
    :param fileobj: file object to cache
    :param size: size to calculate state of caching (and playing)
    :param seekable: file object is seekable (not implemented yet)
    :param blocksize: size of blocks for reading and caching
    '''
    def __init__(self, fileobj, size, seekable=False, blocksize=2048):
        self._fileobj = fileobj
        self.size = size
        self.seekable = seekable # Not implemented yet
        self._blocksize = blocksize
        self._read_thread = threading.Thread(target=self._read)
        self._read_thread.start()
        self.state = STATE_READING
        self._memory = []
        self._current = 0
        self._active = True
        self.bytes_read = 0
        
    def _read(self):
        data = self._fileobj.read(self._blocksize)
        while data and self._active:
            self._memory.append(data)
            self.bytes_read += len(data)
            data = self._fileobj.read(self._blocksize)
        if self._active:
            self.state = STATE_FINISHED
        self._fileobj.close()
        
    def cancel(self):
        '''
        Cancels the reading thread.
        '''
        if self.state == STATE_READING:
            self._active = False
            self.state = STATE_CANCELED
        
    def read(self, size=None):
        '''
        Reads in the internal cache.
        This method should not be used directly.
        The :class:`Player` class uses this method to read data for playing.
        '''
        start_block, start_bytes = divmod(self._current, self._blocksize)
        if size:
            if size > self.size - self._current:
                size = self.size - self._current
            while self._current + size > self.bytes_read:
                time.sleep(0.01)
            self._current += size
            end_block, end_bytes = divmod(self._current, self._blocksize)
            result = self._memory[start_block:end_block]
        else:
            while self.size > self.bytes_read:
                time.sleep(0.01)
            self._current = self.size
            result = self._memory[start_block:]
        if size:
            if end_bytes > 0 :
                result.append(self._memory[end_block][:end_bytes])
        if start_bytes > 0 and result:
            result[0] = result[0][start_bytes:]
        return b''.join(result)    

class Player(gobject.GObject):
    '''
    Play media files, file objects and :class:`Cache` objects over GStreamer.
    Implemented as :class:`gobject.GObject`.
    
    GObject Signals:
    
    +------------+--------------------------------------------------------------------------------+
    | Signal     | Meaning                                                                        |
    +============+================================================================================+
    | started    | Source setup is completed and playing will start (not is playing!!!)           |
    +------------+--------------------------------------------------------------------------------+
    | finished   | Playing of the current file, file object or :class:`Cache` object finished     |
    +------------+--------------------------------------------------------------------------------+
    '''
    def __init__(self, gui):
        gobject.GObject.__init__(self)
        self._player = gst.element_factory_make('playbin2', 'player')
        self._player.connect('source-setup', self._source_setup)
        self._bus = self._player.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect('message', self._on_message)
        self._cache = None
        self._gui = gui
        
    def play_file(self, filename):
        '''
        Play a file by filename.
        
        :param filename: Filename of file to play. Could be absolute or relative.
        '''
        self._uri = 'file://%s' % (os.path.abspath(filename))
        self._setup()
    
    def play_fileobj(self, fileobj, size=None, seekable=False):
        '''
        Play by file object.
        
        :param fileobj: File object to play.
        :param size: Size for duration calculation.
        '''
        self._fileobj = fileobj
        self._size = size
        self._seekable = seekable # Not implemented yet
        self._uri = 'appsrc://'
        self._setup()
    
    def play_cache(self, cache):
        '''
        Play by :class:`Cache` object.
        
        :param cache: Cache object to play.
        '''
        self._cache = cache
        self.play_fileobj(cache, cache.size, cache.seekable)
    
    def play(self):
        '''
        Set state to playing.
        '''
        self._gui.play_btn_pb.set_from_pixbuf(self._gui.stop_icon)
        self._gui.pause_btn_pb.set_from_pixbuf(self._gui.pause_icon)
        self._player.set_state(gst.STATE_PLAYING)
    
    def pause(self):
        '''
        Set state to paused.
        '''
        self._player.set_state(gst.STATE_PAUSED)
        
    def stop(self):
        '''
        Cancel playing.
        You must call this if state is not :const:`STATE_READY` and you want to play a new file, file object or :class:`Cache` object.
        '''
        self._reset()
    
    @property
    def state(self):
        '''
        States:
        
        +------------------------+-------------------------------------+
        | Constant               | Meaning                             |
        +========================+=====================================+
        | :const:`STATE_PLAYING` | Player is playing                   |
        +------------------------+-------------------------------------+
        | :const:`STATE_PAUSED`  | Player is paused                    |
        +------------------------+-------------------------------------+
        | :const:`STATE_READY`   | Player is ready to play a file      |
        +------------------------+-------------------------------------+
        '''
        state = self._player.get_state()[1]
        if state in _STATE_MAPPING:
            return _STATE_MAPPING[state]
    
    @property
    def duration(self):
        '''
        Duration of the current file, file object or :class:`Cache` object.
        
        :rtype: tuple with minutes, seconds, nanoseconds and total nanoseconds
        '''
        total_nanoseconds = self._player.query_duration(gst.FORMAT_TIME)[0]
        seconds, nanoseconds = divmod(total_nanoseconds, 1000000000)
        minutes, seconds = divmod(seconds, 60)
        return minutes, seconds, nanoseconds, total_nanoseconds
    
    @property
    def position(self):
        '''
        Current position in the current file, file object or :class:`Cache` object.
        You have to set this with nanoseconds to seek in the file.
        Please do not seek while playing a file object or a :class:`Cache` object (will be implemented later).
        
        :rtype: tuple with minutes, seconds, nanoseconds and total nanoseconds
        '''
        total_nanoseconds = self._player.query_position(gst.FORMAT_TIME, None)[0]
        seconds, nanoseconds = divmod(total_nanoseconds, 1000000000)
        minutes, seconds = divmod(seconds, 60)
        return minutes, seconds, nanoseconds, total_nanoseconds
    
    @position.setter
    def position(self, nanoseconds):
        self._player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_ACCURATE, int(round(nanoseconds)))
    
    @property
    def volume(self):
        '''
        Volume of the Player. Set this to change volume.
        
        :rtype: float where 1 means full volume and 0 means mute.
        '''
        return self._player.get_property('volume')
    
    @volume.setter
    def volume(self, value):
        self._player.set_property('volume', value)
    
    def _source_setup(self, playbin, source):
        self._source = source
        if self._uri == 'appsrc://':
            self._source.connect('need-data', self._read_data)
            if self._size:
                self._source.set_property('size', self._size)
        gobject.idle_add(self.emit, 'started')
    
    def _seek_data(self, *args):
        print(args)
    
    def _read_data(self, appsrc, lenght):
        data = self._fileobj.read(lenght)
        if data:
            self._source.emit('push-buffer', gst.Buffer(data))
        else:
            self._source.emit('end-of-stream')
    
    def _setup(self):
        self._player.set_property('uri', self._uri)
        self.play()
    
    def _reset(self):
        if self._cache:
            self._cache.cancel()
            self._cache = None
        self._player.set_state(gst.STATE_NULL)
    
    def _on_message(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            self._reset()
            gobject.idle_add(self.emit, 'finished')
        elif message.type == gst.MESSAGE_ERROR:
            print('Error: %s' % (str(message.parse_error())))

def main():
    '''
    Gobject's main loop.
    You can also use other gobject main loops for example gtk's :meth:`gtk.main`.
    
    Not tested because I use :meth:`gtk.main`... Will test it later.
    '''
    global _mainloop
    _mainloop = gobject.MainLoop()
    _mainloop.run()

def main_quit():
    '''
    Stops the main loop.
    
    Not tested because I use :meth:`gtk.main`... Will test it later.
    '''
    global _mainloop
    _mainloop.quit()

gobject.threads_init()
gobject.type_register(Player)
gobject.signal_new('finished',
                   Player,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_BOOLEAN,
                   ())
gobject.signal_new('started',
                   Player,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_BOOLEAN,
                   ())
