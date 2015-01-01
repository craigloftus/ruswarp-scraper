URL = 'http://192.168.35.200/www/custom/turbinesummary.html'
WAIT_FOR = 'healthIndicator'

POLL = 30

VPN_NAME = 'ruswarp'
VPN_BACKOFF = 30

try:
    from local_settings import *
except ImportError:
    pass
