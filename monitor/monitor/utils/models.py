"""Defines the model that should match a link's metadata

This file can be imported as a module and contains the following classes:
    * UrlModel - Defines the expected metadata associated to an URL in the
        input file.
"""

from typing import Optional

from pydantic import AnyHttpUrl, BaseModel


class UrlModel(BaseModel):
    """Defines the expected metadata associated to an URL in the input file.

    It also implicitly enforce validation
    The expected dict format is the following:
    {
      "url": "https://google.com",
      "regexp": "UPDATED"
    }
    """

    url: AnyHttpUrl
    regexp: Optional[str] = None

    class Config:
        """Prohibit the mutation of the model attributes"""

        allow_mutation = False
