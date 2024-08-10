"""Provides functionality to store websites metrics in a Postgres database

This file can be imported as a module and contains the following classes:
    * DbManager - Provides functionality required for store websites metrics
        in the database
"""

from contextlib import contextmanager
import logging

import psycopg2

from .bounded_threaded_connection_pool import BoundedThreadedConnectionPool


class DbManager:
    """Provides functionality to interact with a Postgres database

    Methods
    -------
    initialize_db()
        Creates the corresponding tables in the database if required
    store_metrics(url, regexp, error_code, response_time, matched_text)
        Stores a websites metrics in the database
    """

    WEBSITES_SELECT_QUERY = "SELECT * FROM websites WHERE url=%s"

    WEBSITES_INSERT_QUERY = (
        "INSERT INTO websites(url, regexp) VALUES(%s, %s) RETURNING id"
    )

    METRICS_INSERT_QUERY = (
        "INSERT INTO metrics(website_id, error_code, response_time, matched_text) "
        "VALUES(%s, %s, %s, %s)"
    )

    def __init__(
        self,
        sql_schema_path: str,
        conn_pool: BoundedThreadedConnectionPool,
        logger_name: str = __name__,
    ):
        """
        Parameters
        ----------
        sql_schema_path : str
            Path of the file containing the sql statements to be executed to
            create the corresponding tables in the database.
        conn_pool : BoundedThreadedConnectionPool
            Provides connections to the database.
        logger_name : str
            Logger's name.
        """

        self._sql_schema_path = sql_schema_path
        self._conn_pool = conn_pool
        self._logger = logging.getLogger(logger_name)
        self._logger.debug(
            "%s.__init__(sql_schema_path=%s logger_name=%s)",
            self.__class__.__name__,
            sql_schema_path,
            logger_name,
        )

    @contextmanager
    def _get_connection(self, use_transaction=False):
        """KKKKKKKKKKKKKKGets a db connection and provides a transaction context for it.

        Acquires a database connection from a connections pool, and
        guarantees that it will be released back when the corresponding
        transaction has finished.

        Parameters
        ----------
        use_transaction : bool
            If true, a transaction context will be used
        """

        self._logger.debug(
            "%s._get_connection(use_transaction=%s)",
            self.__class__.__name__,
            use_transaction,
        )
        conn = None
        try:
            conn = self._conn_pool.getconn()
            yield conn
            if use_transaction:
                self._logger.debug("Trying to commit the transaction...")
                conn.commit()
                self._logger.debug(
                    "The transaction was successfully commit to the database"
                )
        except Exception as ex:
            self._logger.exception("Error trying to access the database server:")
            if conn is not None and use_transaction:
                self._logger.debug("Trying to rollback the transaction...")
                conn.rollback()
                self._logger.debug("The transaction was successfully rollback")

            raise ex
        finally:
            if conn is not None:
                conn.reset()
                self._conn_pool.putconn(conn=conn)
                self._logger.debug(
                    "The connection was successfully sent back to the pool"
                )

    def _get_website_id(self, url: str) -> int:
        """Gets from the database, the id of website with the url specified

        Parameters
        ----------
        url : str
            Url of the website whose id is to be determined.

        Returns
        -------
        int
            If a website is found in the database with the specified url, its
            id will be returned. Else will return -1.
        """

        self._logger.debug("%s._get_website_id(url=%s)", self.__class__.__name__, url)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(self.WEBSITES_SELECT_QUERY, (url,))
                result = cursor.fetchone()
                return result[0] if result else -1

    def _store_website(self, url: str, regexp: str):
        """Stores in the database a website's related data

        Parameters
        ----------
        url : str
            Url of the website.
        regexp : str
            Regexp associated to the url.

        Returns
        -------
        int
            The id of the website stored in the database

        Raise
        -----
        psycopg2.IntegrityError
            If a website with the specified url already exists in the
            database.
        """

        self._logger.debug(
            "%s._store_website(url=%s, regexp=%s)", self.__class__.__name__, url, regexp
        )
        with self._get_connection(use_transaction=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(self.WEBSITES_INSERT_QUERY, (url, regexp))
                return cursor.fetchone()[0]

    def _get_id_or_store_website(self, url: str, regexp: str):
        """Gets a website's id or stores a website in the database.

        First it will try to get from the database the id of a website with
        the specified url. If it does not exist, it will store in the
        database a website with the corresponding data.

        Parameters
        ----------
        url : str
            Url of the website.
        regexp : str
            Regexp associated to the url.

        Returns
        -------
        int
            Id of the website
        """

        self._logger.debug(
            "%s._get_id_or_store_website(url=%s, regexp=%s)",
            self.__class__.__name__,
            url,
            regexp,
        )
        website_id = self._get_website_id(url)
        if website_id != -1:
            self._logger.debug(
                "A website with url '%s' already exist in the db. " "website_id=%s",
                url,
                website_id,
            )
            return website_id

        self._logger.debug("A website with url '%s' doesn't exist in the db.", url)

        # A record for the specified url, doesn't exist yet in the table
        # "websites". Let's try to create it:
        try:
            website_id = self._store_website(url, regexp)
            self._logger.debug(
                "A website with url '%s' was successfully stored in the db. "
                "website_id: %s",
                url,
                website_id,
            )
            return website_id
        except psycopg2.IntegrityError:
            self._logger.exception(
                "Error trying to store a website with the url '%s' in the db: ", url
            )
            # Maybe a different execution thread inserted it, will try to
            # grab it again:
            self._logger.debug(
                "Looks like somebody has already stored the url in the "
                "database. Trying to acquire from the database the id "
                "associated to the website's url instead..."
            )
            website_id = self._get_website_id(url)
            self._logger.debug("website_id: %s", website_id)
            return website_id

    def initialize_db(self):
        """Creates the corresponding tables in the database if required."""

        self._logger.debug("%s.initialize_db()", self.__class__.__name__)
        try:
            with open(self._sql_schema_path, "r") as file:
                sql = file.read()

            with self._get_connection(use_transaction=True) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
        except Exception as ex:
            self._logger.exception("Error trying to initialize the database:")
            raise ex

    def store_metrics(self, url, regexp, error_code, response_time, matched_text):
        """Stores a websites check metrics in the database.

        Parameters
        ----------
        url : str
            Url of the website.
        regexp : str
            Regexp applied to the web page acquired as response, when asked
            to the web server for the url.
        error_code : int
            Status code.
        response_time : float
            Time it toke to receive a response to the HTTP GET request, from
            the web server.
        matched_text : str
            Text matched by the regexp, in the page response.
        """

        self._logger.debug(
            "%s.store_metrics(url=%s, regexp=%s, error_code=%s, "
            "response_time=%s, matched_text=%s)",
            self.__class__.__name__,
            url,
            regexp,
            error_code,
            response_time,
            matched_text,
        )
        website_id = self._get_id_or_store_website(url, regexp)
        with self._get_connection(use_transaction=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    self.METRICS_INSERT_QUERY,
                    (website_id, error_code, response_time, matched_text),
                )

        self._logger.debug(
            "Metrics were successfully sored in the db for the website with url '%s'",
            url,
        )
