'''this module contains the logic to obtain
the status and song of a music player.'''

import os
import sys
import urllib
import glib
import Preferences

from gui.base.AvatarManager import AvatarManager
from gui.gtkui.Preferences import BaseTable

class Song(object):
    '''a class representing a song'''

    def __init__(self, artist="?", album="?", title="?", filename="?"):
        self.artist     = artist
        self.album      = album
        self.title      = title
        self.filename   = filename

    def __repr__(self):
        return "%s - %s - %s" % (self.artist, self.album, self.title)

    def format(self, strfmt):
        '''replace vars in strfmt for the values of the song'''
        return strfmt.replace('%ARTIST%', self.artist).replace('%ALBUM%',
                self.album).replace('%TITLE%', self.title).replace('%FILE%',
                        self.filename)

class BaseMusicHandlerConfig(BaseTable):
    '''the panel to display/modify the config related to
    the 'listening to' extension'''

    def __init__(self, config):
        '''constructor'''
        BaseTable.__init__(self, 4, 1)
        self.config = config

        self.append_entry_default(_('Format'), 'format', \
                                 'config.music_format', config.music_format)
        self.append_check(_('Set song cover as avatar'), 'config.change_avatar')

class BaseMusicHandler(object):
    '''Base class for all music handlers that 
        can't split artist/song/album (ie. Windows players)'''
    NAME = 'None'
    DESCRIPTION = 'Don\'t listen to any player'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'
    def __init__(self, main_window):
        self.last_title = None
        self.session = None
        self.avatar_manager = None

        self.session = main_window.session
        self.avatar_manager = AvatarManager(self.session)

        self.config = self.session.config
        # set default values if not set
        self.config.get_or_set('music_format', "%SONG%")
        self.config.get_or_set('change_avatar', False)

        self.config_dialog_class = BaseMusicHandlerConfig

        self.timeout = glib.timeout_add_seconds(15, self.check_song)

    def check_song(self):
        '''get the current song and set it if different than the last one'''
        if self.session:
            song = self.get_current_song()

            if song:
                if song != self.last_title:
                    self.session.set_media(song)
                    self.last_title = song

            elif self.last_title is not None:
                self.last_title = None
                self.session.set_media(_("not playing"))

        return True

    def get_current_song(self):
        ''' returns current song info
        This MUST be overriden'''
        return False

    def is_running(self):
        '''returns True if the player is running
        This MUST be overriden'''
        return False

    def is_playing(self):
        '''returns True if the player is playing a song
        This MUST be overriden'''
        return False

    def _on_config(self, status):
        '''callback for the config dialog'''
        if status:
            pass

    def preferences(self):
        ''' Shows the extension preferences dialog
        You don't need to override this'''
        config_dialog = self.config_dialog_class(self.config)

        preferences_dialog = Preferences.Preferences(
            self._on_config, self.NAME, config_dialog)

        preferences_dialog.show()

class MusicHandler(BaseMusicHandler):
    '''Base class for all music handlers 
        that can split artist from song from album, etc...'''
    NAME = 'None'
    DESCRIPTION = 'Don\'t listen to any player'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, main_window):
        BaseMusicHandler.__init__(self, main_window)
        # set default values if not set
        self.config.get_or_set('music_format', "%ARTIST% - %ALBUM% - %TITLE%")
        self.config.get_or_set('change_avatar', True)

    def check_song(self):
        '''get the current song and set it if different than the last one
        You don't need to override this'''
        if self.session:
            song = self.get_current_song()

            if song:
                # print self.config.format
                current_title = song.format(self.config.music_format)

                if current_title != self.last_title:
                    self.session.set_media(current_title)
                    self.last_title = current_title
                    self.set_cover_as_avatar(song)

            elif self.last_title is not None:
                self.last_title = None
                self.session.set_media(_("not playing"))

        return True

    def set_cover_as_avatar(self, song):
        ''' Sets song cover as avatar
        You don't need to override this'''
        if not self.config.change_avatar:
            return

        image_path = self.get_cover_path(song)
        if image_path != None and self.avatar_manager != None:
            self.avatar_manager.set_as_avatar(image_path)

    def get_cover_path(self, song):
        '''searches in the local covers cache
        if not found also searches in albumart covers website
        returns None if no image found'''
        ''' You don't need to override this'''

        artist = song.artist.encode('utf8')
        album = song.album.encode('utf8')

        if artist == "?":
            artist = ""

        if album == "?":
            album = ""

        if len(artist) == 0 and len(album) == 0:
            return None

        if (os.name != 'nt'):
            home_dir = os.path.expanduser('~')
        else:
            home_dir = os.path.expanduser("~").decode(
                sys.getfilesystemencoding())

        cover_art_path = os.path.join(home_dir, '.covers', '')

        if not os.path.exists(cover_art_path):
            os.makedirs(cover_art_path)

        # print "Searching for covers in " + cover_art_path

        image_path = cover_art_path + artist + '-' + album + '.jpg'

        # print "Checking if " + image_path + " exists"

        if os.path.exists(image_path):
            # print image_path + " found!"
            return image_path

        # print "Not found locally, let's try albumart.org"

        url = "http://www.albumart.org/index.php?srchkey=" + \
            urllib.quote_plus(artist) + "+" + urllib.quote_plus(album) + \
            "&itempage=1&newsearch=1&searchindex=Music"

        albumart = urllib.urlopen(url).read()
        image_url = ""

        for line in albumart.split("\n"):

            if "http://www.albumart.org/images/zoom-icon.jpg" in line:
                image_url = line.partition('src="')[2].partition('"')[0]

            if image_url:
                urllib.urlretrieve(image_url, image_path)
                break

        if os.path.exists(image_path):
            return image_path

        return None

