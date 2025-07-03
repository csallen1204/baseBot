--Create a table for web metrics
CREATE TABLE web_metrics (
 time TIMESTAMP WITH TIME ZONE NOT NULL,
 endpoint VARCHAR(255) NOT NULL,
 response_time_ms INT NOT NULL,
 status_code INT NOT NULL
);

--Convert to a hypertable
SELECT create_hypertable('web_metrics', 'time');

--Insert sample data
INSERT INTO web_metrics (time, endpoint, response_time_ms, status_code) VALUES
('2024-03-15 09:00:00+00', '/api/data', 150, 200),
('2024-03-15 09:01:00+00', '/api/data', 145, 200),
('2024-03-15 09:02:00+00', '/api/user', 160, 404);

--Query to analyze average response times by endpoint
SELECT endpoint, AVG(response_time_ms) AS avg_response_time
FROM web_metrics
GROUP BY endpoint;