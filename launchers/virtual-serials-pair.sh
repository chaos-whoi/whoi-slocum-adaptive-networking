#!/bin/bash

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------


# launching app
exec socat -d -d PTY,raw,echo=0,link=${PORT_A} PTY,raw,echo=0,link=${PORT_B}


# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE
