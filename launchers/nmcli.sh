#!/usr/bin/env python3

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------


# launching app
import nmcli
import json

print(json.dumps(nmcli.device.show_all(), sort_keys=True, indent=4))


# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE
