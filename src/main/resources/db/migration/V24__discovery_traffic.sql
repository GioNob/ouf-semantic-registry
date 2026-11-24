-- Measurements start at instrumented dispatch. Historical attempts contain no wire counts.
CREATE TABLE ouf_sem.discovery_fetch_traffic (
  request_id uuid NOT NULL REFERENCES ouf_sem.discovery_request ON DELETE CASCADE,
  resource_hash bytea NOT NULL CHECK (octet_length(resource_hash) = 32),
  sends bigint NOT NULL CHECK (sends > 0),
  useful boolean NOT NULL DEFAULT false,
  PRIMARY KEY (request_id, resource_hash)
);

CREATE TABLE ouf_sem.discovery_traffic_count (
  request_id uuid NOT NULL REFERENCES ouf_sem.discovery_request ON DELETE CASCADE,
  metric text NOT NULL,
  route text NOT NULL,
  origin text NOT NULL,
  amount bigint NOT NULL CHECK (amount > 0),
  PRIMARY KEY (request_id, metric, route, origin),
  CHECK ((metric IN ('searchSent','getExcluded') AND route = '' AND origin = '')
      OR (metric = 'http429' AND route IN ('search','fetch') AND origin IN ('APISIX','UPSTREAM','UNKNOWN')))
);

CREATE VIEW ouf_sem.discovery_job_traffic AS
  SELECT request_id, metric, route, origin, amount FROM ouf_sem.discovery_traffic_count
  UNION ALL
  SELECT request_id, 'getSent', '', '', sum(sends) FROM ouf_sem.discovery_fetch_traffic GROUP BY request_id
  UNION ALL
  SELECT request_id, 'getRepeated', '', '', sum(sends - 1) FROM ouf_sem.discovery_fetch_traffic GROUP BY request_id
  UNION ALL
  SELECT request_id, 'getUseful', '', '', count(*) FROM ouf_sem.discovery_fetch_traffic WHERE useful GROUP BY request_id;
