import os
import uuid

DEBUG = bool(os.environ.get("DEBUG", 0))

ZERO = 0
INFTY = 99999999999
PROCESS_KEY = str(uuid.uuid4())

# ports
SERVER_PORT = 12345

IFACE_BANDWIDTH_CHECK_EVERY_SECS = float(os.environ.get("IFACE_BANDWIDTH_CHECK_EVERY_SECS", 1.0))
IFACE_LATENCY_CHECK_EVERY_SECS = float(os.environ.get("IFACE_LATENCY_CHECK_EVERY_SECS", 1.0))
IFACE_PING_CHECK_EVERY_SECS = float(os.environ.get("IFACE_PING_CHECK_EVERY_SECS", 1.0))

IFACE_MIN_BANDWIDTH_BYTES_SEC = 8
IFACE_BANDWIDTH_OPTIMISM = 0.5

ZEROCONF_PREFIX = "_adanet._tcp.local."

ALLOW_DEVICE_TYPES = os.environ.get("ALLOW_DEVICE_TYPES", "all").split(",")

FORMULATE_PROBLEM_EVERY_SEC = 5

# solvers
DEFAULT_SOLVER = "SimpleSolver"

# reports
REPORT_PRECISION_SEC = 0.5

# weights and biases
WANDB_API_KEY = "9c9f492d9419ea478dbd7540806190989e1d9877"
WANDB_PROJECT = "test"
WANDB_OFFLINE = os.environ.get("WANDB_OFFLINE", "0").lower() in ["1", "true", "yes"]

# persist-queue
QUEUE_PATH = os.environ.get("QUEUE_PATH", "/tmp/queue")
os.makedirs(QUEUE_PATH)
