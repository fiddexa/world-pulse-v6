# =========================================================
# AROUND THE MAIN v6 — CONFIGURATION
# =========================================================

APP_NAME = "AROUND THE MAIN"
VERSION = "6.0"

# ---------------------------------------------------------
# PIPELINE
# ---------------------------------------------------------

PIPELINE_VERSION = "6"

# ---------------------------------------------------------
# CLUSTERING
# ---------------------------------------------------------

# Conservative default.
# Same event should merge only when identity evidence
# is sufficiently strong.
CLUSTER_THRESHOLD = 0.70

# Never allow clustering below this value.
MIN_CLUSTER_THRESHOLD = 0.65

# ---------------------------------------------------------
# VERIFICATION
# ---------------------------------------------------------

MIN_SOURCES_FOR_CONFIRMED = 3
MIN_SOURCES_FOR_MULTI_SOURCE = 5

# ---------------------------------------------------------
# RANKING
# ---------------------------------------------------------

SIGNIFICANCE_CRITICAL = 90.0
SIGNIFICANCE_VERY_HIGH = 80.0
SIGNIFICANCE_HIGH = 65.0
SIGNIFICANCE_MEDIUM = 50.0

# ---------------------------------------------------------
# LIMITS
# ---------------------------------------------------------

MAX_TOP_EVENTS = 10
MAX_ARTICLES_PER_EVENT = 20
