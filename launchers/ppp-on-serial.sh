#!/bin/bash

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------


# launching app
exec pppd -detach ${PORT} ${BAUD_RATE} ${LOCAL_IP}:${REMOTE_IP} proxyarp local noauth debug nodetach dump nocrtscts passive persist


# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE
