CREATE TABLE monitors (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    interval_seconds INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT check_interval
        CHECK (interval_seconds > 0)
);

CREATE TABLE check_results (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    monitor_id BIGINT NOT NULL,
    status VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_monitor
        FOREIGN KEY (monitor_id)
        REFERENCES monitors(id)
        ON DELETE CASCADE,

    CONSTRAINT check_status
        CHECK (status IN ('UP', 'DOWN')),

    CONSTRAINT check_response_time
        CHECK (response_time_ms IS NULL OR response_time_ms >= 0)
);

CREATE INDEX idx_check_results_monitor_checked
ON check_results (monitor_id, checked_at DESC);