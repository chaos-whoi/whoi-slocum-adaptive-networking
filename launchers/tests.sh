#!/bin/bash

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------


mkdir -p /out/coverage


# launching app
nosetests \
    --rednose \
    --immediate \
    --cover-html \
    --cover-html-dir=/out/coverage \
    --cover-tests \
    --with-coverage \
    --cover-package=adanet \
    --nologcapture \
    --verbose \
    --where=/tests


# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE
