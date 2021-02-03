# GeniusAPI
# John W. Miller
# See LICENSE for details

"""API documentation: https://docs.genius.com/"""

import json
import os
import re
import shutil
import time

from bs4 import BeautifulSoup

from .api import API, PublicAPI
from .types import Song
from .utils import clean_str, safe_unicode


class Genius(API, PublicAPI):
    """User-level interface with the Genius.com API and public API.

    Args:
        access_token (:obj:`str`, optional): API key provided by Genius.
        response_format (:obj:`str`, optional): API response format (dom, plain, html).
        timeout (:obj:`int`, optional): time before quitting on response (seconds).
        sleep_time (:obj:`str`, optional): time to wait between requests.
        verbose (:obj:`bool`, optional): Turn printed messages on or off.
        remove_section_headers (:obj:`bool`, optional): If `True`, removes [Chorus],
            [Bridge], etc. headers from lyrics.
        skip_non_songs (:obj:`bool`, optional): If `True`, attempts to
            skip non-songs (e.g. track listings).
        excluded_terms (:obj:`list`, optional): extra terms for flagging results
            as non-lyrics.
        replace_default_terms (:obj:`list`, optional): if True, replaces default
            excluded terms with user's. Default excluded terms are listed below.
        retries (:obj:`int`, optional): Number of retries in case of timeouts and
            errors with a >= 500 response code. By default, requests are only made once.

    Attributes:
        verbose (:obj:`bool`, optional): Turn printed messages on or off.
        remove_section_headers (:obj:`bool`, optional): If `True`, removes [Chorus],
            [Bridge], etc. headers from lyrics.
        skip_non_songs (:obj:`bool`, optional): If `True`, attempts to
            skip non-songs (e.g. track listings).
        excluded_terms (:obj:`list`, optional): extra terms for flagging results
            as non-lyrics.
        replace_default_terms (:obj:`list`, optional): if True, replaces default
            excluded terms with user's.
        retries (:obj:`int`, optional): Number of retries in case of timeouts and
            errors with a >= 500 response code. By default, requests are only made once.

    Returns:
        :class:`Genius`

    Note:
        Default excluded terms are the following regular expressions:
        :obj:`track\\s?list`, :obj:`album art(work)?`, :obj:`liner notes`,
        :obj:`booklet`, :obj:`credits`, :obj:`interview`, :obj:`skit`,
        :obj:`instrumental`, and :obj:`setlist`.

    """

    default_terms = ['track\\s?list', 'album art(work)?', 'liner notes',
                     'booklet', 'credits', 'interview', 'skit',
                     'instrumental', 'setlist']

    def __init__(self, access_token=None,
                 response_format='plain', timeout=5, sleep_time=0.2,
                 verbose=True, remove_section_headers=False,
                 skip_non_songs=True, excluded_terms=None,
                 replace_default_terms=False,
                 retries=0,
                 ):
        # Genius Client Constructor
        super().__init__(
            access_token=access_token,
            response_format=response_format,
            timeout=timeout,
            sleep_time=sleep_time,
            retries=retries
        )

        self.verbose = verbose
        self.remove_section_headers = remove_section_headers
        self.skip_non_songs = skip_non_songs

        excluded_terms = excluded_terms if excluded_terms is not None else []
        if replace_default_terms:
            self.excluded_terms = excluded_terms
        else:
            self.excluded_terms = self.default_terms.copy()
            self.excluded_terms.extend(excluded_terms)

    def lyrics(self, urlthing, remove_section_headers=False):
        """Uses BeautifulSoup to scrape song info off of a Genius song URL
        Args:
            urlthing (:obj:`str` | :obj:`int`):
                Song ID or song URL.
            remove_section_headers (:obj:`bool`, optional):
                If `True`, removes [Chorus], [Bridge], etc. headers from lyrics.
        Returns:
            :obj:`str` \\|‌ :obj:`None`:
                :obj:`str` If it can find the lyrics, otherwise `None`
        Note:
            If you pass a song ID, the method will have to make an extra request
            to obtain the song's URL and scrape the lyrics off of it. So it's best
            to pass the method the song's URL if it's available.
            If you want to get a song's lyrics by searching for it,
            use :meth:`Genius.search_song` instead.
        Note:
            This method removes the song headers based on the value of the
            :attr:`Genius.remove_section_headers` attribute.
        """
        if isinstance(urlthing, int):
            path = self.song(urlthing)['song']['path'][1:]
        else:
            path = urlthing.replace("https://genius.com/", "")

        # Scrape the song lyrics from the HTML
        html = BeautifulSoup(
            self._make_request(path, web=True).replace('<br/>', '\n'),
            "html.parser"
        )

        # Determine the class of the div
        div = html.find("div", class_=re.compile("^lyrics$|Lyrics__Root"))
        if div is None:
            if self.verbose:
                print("Couldn't find the lyrics section. "
                      "Please report this if the song has lyrics.\n"
                      "Song URL: https://genius.com/{}".format(path))
            return None

        lyrics = div.get_text()

        # Remove [Verse], [Bridge], etc.
        if self.remove_section_headers or remove_section_headers:
            lyrics = re.sub(r'(\[.*?\])*', '', lyrics)
            lyrics = re.sub('\n{2}', '\n', lyrics)  # Gaps between verses
        return lyrics.strip("\n")

    def _result_is_lyrics(self, song):
        """Returns False if result from Genius is not actually song lyrics.

        Sets the :attr:`lyricsgenius.Genius.excluded_terms` and
        :attr:`lyricsgenius.Genius.replace_default_terms` as instance variables
        within the Genius class.

        Args:
            song_title (:obj:`str`, optional): Title of the song.

        Returns:
            :obj:`bool`: `True` if none of the terms are found in the song title.

        Note:
            Default excluded terms are the following: 'track\\s?list',
            'album art(work)?', 'liner notes', 'booklet', 'credits',
            'interview', 'skit', 'instrumental', and 'setlist'.

        """
        if song['lyrics_state'] != 'complete':
            return False

        expression = r"".join(["({})|".format(term) for term in self.excluded_terms])
        expression = expression.strip('|')
        regex = re.compile(expression, re.IGNORECASE)
        return not regex.search(clean_str(song['title']))

    def _get_item_from_search_response(self, response, search_term, type_, result_type):
        """Gets the desired item from the search results.

        This method tries to match the `hits` of the :obj:`response` to
        the :obj:`response_term`, and if it finds no match, returns the first
        appropriate hit if there are any.

        Args:
            response (:obj:`dict`): A response from
                :meth:‍‍‍‍`Genius.search_all` to go through.
            search_term (:obj:`str`): The search term to match with the hit.
            type_ (:obj:`str`): Type of the hit we're looking for (e.g. song, artist).
            result_type (:obj:`str`): The part of the hit we want to match
                (e.g. song title, artist's name).

        Returns:
            :obj:‍‍`str` \\|‌ :obj:`None`:
            - `None` if there is no hit in the :obj:`response`.
            - The matched result if matching succeeds.
            - The first hit if the matching fails.

        """

        # Convert list to dictionary
        top_hits = response['sections'][0]['hits']

        # Check rest of results if top hit wasn't the search type
        sections = sorted(response['sections'],
                          key=lambda sect: sect['type'] == type_)

        hits = [hit for hit in top_hits if hit['type'] == type_]
        hits.extend([hit for section in sections
                     for hit in section['hits']
                     if hit['type'] == type_])

        for hit in hits:
            item = hit['result']
            if clean_str(item[result_type]) == clean_str(search_term):
                return item

        # If the desired type is song lyrics and none of the results matched,
        # return the first result that has lyrics
        if type_ == 'song' and self.skip_non_songs:
            for hit in hits:
                song = hit['result']
                if self._result_is_lyrics(song):
                    return song

        return hits[0]['result'] if hits else None

    def _result_is_match(self, result, title, artist=None):
        """Returns `True` if search result matches searched song."""
        result_title = clean_str(result['title'])
        title_is_match = result_title == clean_str(title)
        if not artist:
            return title_is_match
        result_artist = clean_str(result['primary_artist']['name'])
        return title_is_match and result_artist == clean_str(artist)


    def search_song(self, title=None, artist="", song_id=None,
                    get_full_info=True):
        """Searches for a specific song and gets its lyrics.

        You must pass either a :obj:`title` or a :obj:`song_id`.

        Args:
            title (:obj:`str`): Song title to search for.
            artist (:obj:`str`, optional): Name of the artist.
            get_full_info (:obj:`bool`, optional): Get full info for each song (slower).
            song_id (:obj:`int`, optional): Song ID.

        Returns:
            :class:`Song <types.Song>` \\| :obj:`None`: On success,
            the song object is returned, otherwise `None`.

        Tip:
            Set :attr:`Genius.verbose` to `True` to read why the search fails.

        Examples:
            .. code:: python

                genius = Genius(token)
                artist = genius.search_artist('Andy Shauf', max_songs=0)
                song = genius.search_song('Toy You', artist.name)
                # same as: song = genius.search_song('To You', 'Andy Shauf')
                print(song.lyrics)

        """
        msg = "You must pass either a `title` or a `song_id`."
        if title is None and song_id is None:
            assert any([title, song_id]), msg

        if self.verbose and title:
            if artist:
                print('Searching for "{s}" by {a}...'.format(s=title, a=artist))
            else:
                print('Searching for "{s}"...'.format(s=title))

        if song_id:
            result = self.song(song_id)['song']
        else:
            search_term = "{s} {a}".format(s=title, a=artist).strip()
            search_response = self.search_all(search_term)
            result = self._get_item_from_search_response(search_response,
                                                         title,
                                                         type_="song",
                                                         result_type="title")

        # Exit search if there were no results returned from API
        # Otherwise, move forward with processing the search results
        if result is None:
            if self.verbose and title:
                print("No results found for: '{s}'".format(s=search_term))
            return None

        # Reject non-songs (Liner notes, track lists, etc.)
        # or songs with uncomplete lyrics (e.g. unreleased songs, instrumentals)
        if self.skip_non_songs and not self._result_is_lyrics(result):
            valid = False
        else:
            valid = True

        if not valid:
            if self.verbose:
                print('Specified song does not contain lyrics. Rejecting.')
            return None

        song_id = result['id']

        # Download full song info (an API call) unless told not to by user
        song_info = result
        if song_id is None and get_full_info is True:
            new_info = self.song(song_id)['song']
            song_info.update(new_info)
        if song_info['lyrics_state'] == 'complete':
            lyrics = self.lyrics(song_info['url'])
        else:
            lyrics = ""

        # Skip results when URL is a 404 or lyrics are missing
        if self.skip_non_songs and not lyrics:
            if self.verbose:
                print('Specified song does not have a valid lyrics. '
                      'Rejecting.')
            return None

        # Return a Song object with lyrics if we've made it this far
        song = Song(self, song_info, lyrics)
        if self.verbose:
            print('Done.')
        return song
