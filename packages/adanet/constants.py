import os
import uuid

DEBUG = bool(int(os.environ.get("DEBUG", 0)))

ZERO = 0
INFTY = 99999999999
PROCESS_KEY = str(uuid.uuid4())

# ports
ZMQ_SUB_SERVER_PORT = 12345
ZMQ_PUB_SERVER_PORT = 12346
ZMQ_HEARTBEAT_EVERY_SEC = 1.0

IFACE_BANDWIDTH_CHECK_EVERY_SECS = float(os.environ.get("IFACE_BANDWIDTH_CHECK_EVERY_SECS", 1.0))
IFACE_PING_CHECK_EVERY_SECS = float(os.environ.get("IFACE_PING_CHECK_EVERY_SECS", 1))

IFACE_MIN_BANDWIDTH_BYTES_SEC = 8
IFACE_BANDWIDTH_OPTIMISM = 1.0

NETWORK_LOG_EVERY_SECS = float(os.environ.get("NETWORK_LOG_EVERY_SECS", 2))
NETWORK_IFACES_DISCOVERY_EVERY_SECS = float(os.environ.get("NETWORK_IFACES_DISCOVERY_EVERY_SECS", 2))

CHANNELS_LOG_EVERY_SECS = float(os.environ.get("CHANNELS_LOG_EVERY_SECS", 2))

ZEROCONF_PREFIX = "_adanet._tcp.local."

ALLOW_DEVICE_TYPES = os.environ.get("ALLOW_DEVICE_TYPES", "all").split(",")

FORMULATE_PROBLEM_EVERY_SEC = 4.0

# solvers
DEFAULT_SOLVER = "SimpleSolver"

# reports
REPORT_PRECISION_SEC = 0.5

# weights and biases
WANDB_API_KEY = os.environ.get("WANDB_API_KEY", "9c9f492d9419ea478dbd7540806190989e1d9877")
WANDB_PROJECT = os.environ.get("WANDB_PROJECT", "whoi-adanet-test")
WANDB_NAME = os.environ.get("WANDB_NAME", None)
WANDB_OFFLINE = os.environ.get("WANDB_OFFLINE", "0").lower() in ["1", "true", "yes"]

# persist-queue
QUEUE_PATH = os.environ.get("QUEUE_PATH", "/tmp/queue")
os.makedirs(QUEUE_PATH, exist_ok=True)
