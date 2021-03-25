"""Defines constants

DEFAULT_STATUS_CODE
    Default status code to use when a status code can't be determined
DNS_LOOKUP_ERROR_CODE
    Status code to use when a DNS lookup for a domain name fails
NETWORK_CNX_TIMEOUT_ERROR_CODE
    Status code to use when a TCP connection time out take place
DEFAULT_RESPONSE_TIME
    Default response time to be used when it couldn't be determined
"""

# Default status code to use when a status code can't be determined:
DEFAULT_STATUS_CODE = -1

# Status code to use when a DNS lookup for a domain name fails:
DNS_LOOKUP_ERROR_CODE = 404

# Status code to use when a TCP connection time out take place:
NETWORK_CNX_TIMEOUT_ERROR_CODE = 599

# Default response time to be used when it couldn't be determined:
DEFAULT_RESPONSE_TIME = -1
