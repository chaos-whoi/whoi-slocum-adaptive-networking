# The standard 2-part DsHeader block
# This allows both a standard ROS header and DS-specific header blocks
# See HEADERS.md in ds_core_msgs for details
std_msgs/Header header
#ds_core_msgs/DsHeader ds_header

float64 lat
float64 lon

float64 northing
float64 easting
float64 depth
float64 altitude

float64 delta_north
float64 delta_east

float64 roll
float64 pitch
float64 heading

# w/ ahrs = 1 (high precision), w/o ahrs = 0 (low precision)
bool    fidelity