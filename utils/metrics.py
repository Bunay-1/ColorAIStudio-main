from prometheus_client import Counter, Histogram, Gauge

request_counter = Counter(
    "icap_api_requests_total",
    "Total number of API requests received",
    ["endpoint", "method", "status"]
)

delta_e_duration_seconds = Histogram(
    "icap_delta_e_duration_seconds",
    "Time spent calculating Delta E",
    ['endpoint']
)

rag_query_duration_seconds = Histogram(
    "icap_rag_query_duration_seconds",
    "Time spent executing a RAG query",
    ['operation']
)

rag_documents_indexed_total = Counter(
    "icap_rag_documents_indexed_total",
    "Total number of documents sent for RAG indexing"
)

rag_indexing_duration_seconds = Histogram(
    "icap_rag_indexing_duration_seconds",
    "Time spent indexing documents into RAG",
    ['endpoint']
)

iot_event_counter = Counter(
    "icap_iot_events_total",
    "Total number of IoT events processed",
    ['device_type']
)

database_query_duration_seconds = Histogram(
    "icap_database_query_duration_seconds",
    "Time spent executing database queries",
    ['operation']
)

gauge_rag_enabled = Gauge(
    "icap_rag_enabled",
    "Whether the RAG subsystem is enabled",
)

# Circuit Breaker Metrics
circuit_breaker_state = Gauge(
    "icap_circuit_breaker_state",
    "Current state of circuit breakers (0=CLOSED, 1=HALF_OPEN, 2=OPEN)",
    ['service']
)

circuit_breaker_failures = Gauge(
    "icap_circuit_breaker_failures_total",
    "Total number of failures recorded by circuit breaker",
    ['service']
)

circuit_breaker_last_failure_time = Gauge(
    "icap_circuit_breaker_last_failure_timestamp",
    "Unix timestamp of the last failure for each circuit breaker",
    ['service']
)
