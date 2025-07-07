CREATE TABLE viaipe_norte_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    clients_reporting INT,
    avg_bandwidth_mbps FLOAT,
    avg_latency_ms FLOAT,
    avg_packet_loss_percent FLOAT,
    quality_score FLOAT
);