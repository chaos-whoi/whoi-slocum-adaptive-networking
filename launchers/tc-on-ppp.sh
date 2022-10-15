#!/bin/bash

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------

set -eu

# launching app
exec slow --device ${DEVICE} --bandwidth ${BANDWIDTH} --latency ${LATENCY}


# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE
