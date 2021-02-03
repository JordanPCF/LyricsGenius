from .base import Sender
from .public_methods import (
    SearchMethods,
    SongMethods
)


class API(Sender):
    """Genius API.

    The :obj:`API` class is in charge of making all the requests
    to the developers' API (api.genius.com)
    Use the methods of this class if you already have information
    such as song ID to make direct requests to the API. Otherwise
    the :class:`Genius` class provides a friendlier front-end
    to search and retrieve data from Genius.com.

    All methods of this class are available through the :class:`Genius` class.

    Args:
        access_token (:obj:`str`): API key provided by Genius.
        response_format (:obj:`str`, optional): API response format (dom, plain, html).
        timeout (:obj:`int`, optional): time before quitting on response (seconds).
        sleep_time (:obj:`str`, optional): time to wait between requests.
        retries (:obj:`int`, optional): Number of retries in case of timeouts and
            errors with a >= 500 response code. By default, requests are only made once.

    Attributes:
        response_format (:obj:`str`, optional): API response format (dom, plain, html).
        timeout (:obj:`int`, optional): time before quitting on response (seconds).
        sleep_time (:obj:`str`, optional): time to wait between requests.
        retries (:obj:`int`, optional): Number of retries in case of timeouts and
            errors with a >= 500 response code. By default, requests are only made once.

    Returns:
        :class:`API`: An object of the `API` class.

    """

    def __init__(self,
                 access_token,
                 response_format='plain',
                 timeout=5,
                 sleep_time=0.2,
                 retries=0,
                 ):
        super().__init__(
            access_token=access_token,
            response_format=response_format,
            timeout=timeout,
            sleep_time=sleep_time,
            retries=retries,
        )

    def search_songs(self, search_term, per_page=None, page=None):
        """Searches songs hosted on Genius.

        Args:
            search_term (:obj:`str`): A term to search on Genius.
            per_page (:obj:`int`, optional): Number of results to
                return per page. It can't be more than 5 for this method.
            page (:obj:`int`, optional): Number of the page.

        Returns:
            :obj:`dict`

        """
        endpoint = "search"
        params = {'q': search_term,
                  'per_page': per_page,
                  'page': page}
        return self._make_request(endpoint, params_=params)

    def song(self, song_id, text_format=None):
        """Gets data for a specific song.

        Args:
            song_id (:obj:`int`): Genius song ID
            text_format (:obj:`str`, optional): Text format of the results
                ('dom', 'html', 'markdown' or 'plain').

        Returns:
            :obj:`dict`

        Examples:
            .. code:: python

                genius = Genius(token)
                song = genius.song(2857381)
                print(song['full_title'])

        """
        endpoint = "songs/{id}".format(id=song_id)
        params = {'text_format': text_format or self.response_format}
        return self._make_request(endpoint, params_=params)

class PublicAPI(
        Sender,
        SearchMethods,
        SongMethods):
    """Genius public API.

    The :obj:`PublicAPI` class is in charge of making all the requests
    to the public API (genius.com/api)
    You can use this method without an access token since calls are made
    to the public API.

    All methods of this class are available through the :class:`Genius` class.

    Args:
        response_format (:obj:`str`, optional): API response format (dom, plain, html).
        timeout (:obj:`int`, optional): time before quitting on response (seconds).
        sleep_time (:obj:`str`, optional): time to wait between requests.
        retries (:obj:`int`, optional): Number of retries in case of timeouts and
            errors with a >= 500 response code. By default, requests are only made once.

    Attributes:
        response_format (:obj:`str`, optional): API response format (dom, plain, html).
        timeout (:obj:`int`, optional): time before quitting on response (seconds).
        sleep_time (:obj:`str`, optional): time to wait between requests.
        retries (:obj:`int`, optional): Number of retries in case of timeouts and
            errors with a >= 500 response code. By default, requests are only made once.

    Returns:
        :class:`PublicAPI`: An object of the `PublicAPI` class.

    """

    def __init__(
        self,
        response_format='plain',
        timeout=5,
        sleep_time=0.2,
        retries=0,
        **kwargs
    ):
        # Genius PublicAPI Constructor
        super().__init__(
            response_format=response_format,
            timeout=timeout,
            sleep_time=sleep_time,
            retries=retries,
            **kwargs
        )
