# Part 1 - Redis Setup & Replication

This document captures the Redis OSS to Redis Enterprise replication setup for Part 1 of the assignment.

> Note: Docker was not used for this setup. Redis OSS was installed directly on Server A, and Redis Enterprise was installed directly on Server B.

## Environment Summary

| Component | Server | Details |
|---|---|---|
| Redis OSS Source | Server A | `<SERVER_A_HOSTNAME_OR_IP>` |
| Redis Enterprise Target | Server B | `<SERVER_B_HOSTNAME_OR_IP>` |
| Redis OSS Version | Server A | `7.2.0` |
| Redis OSS Port | Server A | `<CUSTOM_REDIS_OSS_PORT>` |
| Redis Enterprise Version | Server B | `<REDIS_ENTERPRISE_VERSION>` |
| Redis Enterprise Database | Server B | `<ENTERPRISE_DATABASE_NAME>` |
| Redis Enterprise DB Endpoint | Server B | `<ENTERPRISE_DB_ENDPOINT>:<ENTERPRISE_DB_PORT>` |

## 1. Redis OSS Installation - Server A

Redis OSS version `7.2.0` was installed on Server A without Docker.

### Redis OSS Version Snapshot

```bash
redis-server --version
```

Expected / captured output:

```text
<PASTE_REDIS_SERVER_VERSION_OUTPUT_HERE>
```

Screenshot:

`<PLACEHOLDER: screenshots/server-a-redis-version.png>`

## 2. Redis OSS Configuration

The default Redis port `6379` was changed to a custom port.

Persistence was enabled using AOF because it provides the strongest durability guarantees among Redis persistence options. The configuration uses `appendfsync always` for maximum durability.

### redis.conf Path

Redis OSS configuration file path:

```text
<PASTE_FULL_PATH_TO_REDIS_CONF_HERE>
```

Example:

```text
/etc/redis/redis.conf
```

### Key redis.conf Snippet

```conf
# Network
bind 0.0.0.0
protected-mode yes
port <CUSTOM_REDIS_OSS_PORT>

# Persistence - AOF enabled for best durability guarantees
appendonly yes
appendfilename "appendonly.aof"
appendfsync always

# Optional RDB snapshotting, if enabled in the implementation
save 900 1
save 300 10
save 60 10000

# Security
requirepass <REDIS_OSS_PASSWORD_IF_CONFIGURED>
```

Configuration snapshot:

`<PLACEHOLDER: screenshots/server-a-redis-conf.png>`

### Redis OSS Service Status Snapshot

Command:

```bash
sudo systemctl status redis
```

Snapshot:

`<PLACEHOLDER: screenshots/server-a-redis-service-status.png>`

### Redis OSS Connectivity Check

Command:

```bash
redis-cli -h <SERVER_A_HOSTNAME_OR_IP> -p <CUSTOM_REDIS_OSS_PORT> -a '<REDIS_OSS_PASSWORD_IF_CONFIGURED>' PING
```

Captured output:

```text
PONG
```

Snapshot:

`<PLACEHOLDER: screenshots/server-a-redis-ping.png>`

## 3. Data Load Using memtier-benchmark

At least `100,000` keys were loaded into Redis OSS using `memtier-benchmark`.

### memtier-benchmark Command

The following command can be run to validate the data load and benchmark results:

```bash
memtier_benchmark \
  --server <SERVER_A_HOSTNAME_OR_IP> \
  --port <CUSTOM_REDIS_OSS_PORT> \
  --authenticate '<REDIS_OSS_PASSWORD_IF_CONFIGURED>' \
  --protocol redis \
  --clients 50 \
  --threads 4 \
  --requests 2500 \
  --key-prefix part1: \
  --key-minimum 1 \
  --key-maximum 100000 \
  --data-size 128 \
  --ratio 1:0 \
  --hide-histogram
```

> The command above writes `50 clients * 4 threads * 2,500 requests = 500,000` SET operations over a key range of `100,000`, ensuring at least `100,000` keys are created.

If authentication was not configured, remove this argument:

```bash
--authenticate '<REDIS_OSS_PASSWORD_IF_CONFIGURED>'
```

### Throughput and Latency Results

Paste the captured benchmark summary below:

```text
<PASTE_MEMTIER_BENCHMARK_OUTPUT_HERE>
```

| Metric | Captured Value |
|---|---:|
| Total Ops/sec | `<OPS_PER_SEC>` |
| SET Ops/sec | `<SET_OPS_PER_SEC>` |
| Average Latency | `<AVG_LATENCY_MS>` |
| P50 Latency | `<P50_LATENCY_MS>` |
| P95 Latency | `<P95_LATENCY_MS>` |
| P99 Latency | `<P99_LATENCY_MS>` |

Benchmark snapshot:

`<PLACEHOLDER: screenshots/memtier-benchmark-results.png>`

### Redis OSS Key Count Validation

Command:

```bash
redis-cli -h <SERVER_A_HOSTNAME_OR_IP> -p <CUSTOM_REDIS_OSS_PORT> -a '<REDIS_OSS_PASSWORD_IF_CONFIGURED>' DBSIZE
```

Captured output:

```text
<PASTE_OSS_DBSIZE_OUTPUT_HERE>
```

Snapshot:

`<PLACEHOLDER: screenshots/server-a-oss-dbsize.png>`

## 4. Redis Enterprise Installation - Server B

Redis Enterprise was installed on Server B using the no-DNS setup.

### Redis Enterprise Version Snapshot

Command:

```bash
rladmin status
```

Captured output:

```text
<PASTE_RLADMIN_STATUS_OUTPUT_HERE>
```

Snapshot:

`<PLACEHOLDER: screenshots/server-b-redis-enterprise-status.png>`

### Redis Enterprise Cluster / Node Snapshot

Snapshot:

`<PLACEHOLDER: screenshots/server-b-enterprise-cluster-nodes.png>`

## 5. Redis Enterprise Database Configuration

A Redis Enterprise database was created on Server B to receive replication from the Redis OSS source.

### Database Details

| Field | Value |
|---|---|
| Database Name | `<ENTERPRISE_DATABASE_NAME>` |
| Endpoint | `<ENTERPRISE_DB_ENDPOINT>` |
| Port | `<ENTERPRISE_DB_PORT>` |
| Memory Limit | `<DATABASE_MEMORY_LIMIT>` |
| Persistence | `<PERSISTENCE_SETTING>` |
| Eviction Policy | `<EVICTION_POLICY>` |
| Replication Source | `<SERVER_A_HOSTNAME_OR_IP>:<CUSTOM_REDIS_OSS_PORT>` |

### Redis Enterprise Database Configuration Snapshot

Snapshot:

`<PLACEHOLDER: screenshots/server-b-enterprise-db-config.png>`

Optional command output:

```bash
rladmin status databases
```

Captured output:

```text
<PASTE_RLADMIN_DATABASE_STATUS_OUTPUT_HERE>
```

## 6. OSS to Redis Enterprise Replication

Replication was configured with Redis OSS as the source and Redis Enterprise as the target.

Replication direction:

```text
Redis OSS on Server A  --->  Redis Enterprise Database on Server B
```

### Replication Configuration

Source:

```text
<SERVER_A_HOSTNAME_OR_IP>:<CUSTOM_REDIS_OSS_PORT>
```

Target:

```text
<ENTERPRISE_DB_ENDPOINT>:<ENTERPRISE_DB_PORT>
```

Authentication:

```text
<SOURCE_AUTH_CONFIG_IF_ANY>
```

### Redis Enterprise Replication Status Snapshot

Snapshot:

`<PLACEHOLDER: screenshots/server-b-replica-of-status.png>`

Optional command / UI evidence:

```text
<PASTE_REDIS_ENTERPRISE_REPLICATION_STATUS_HERE>
```

Expected status:

```text
Replica Of status: Active / Syncing completed
Source: <SERVER_A_HOSTNAME_OR_IP>:<CUSTOM_REDIS_OSS_PORT>
Target: <ENTERPRISE_DATABASE_NAME>
```

## 7. Key Count Validation After Replication

The number of keys in Redis OSS should match the number of keys in the Redis Enterprise database.

### Redis OSS Key Count

Command:

```bash
redis-cli -h <SERVER_A_HOSTNAME_OR_IP> -p <CUSTOM_REDIS_OSS_PORT> -a '<REDIS_OSS_PASSWORD_IF_CONFIGURED>' DBSIZE
```

Captured output:

```text
<PASTE_OSS_DBSIZE_OUTPUT_HERE>
```

### Redis Enterprise Key Count

Command:

```bash
redis-cli -h <ENTERPRISE_DB_ENDPOINT> -p <ENTERPRISE_DB_PORT> -a '<ENTERPRISE_DB_PASSWORD_IF_CONFIGURED>' DBSIZE
```

Captured output:

```text
<PASTE_ENTERPRISE_DBSIZE_OUTPUT_HERE>
```

### Validation Result

| Database | Key Count |
|---|---:|
| Redis OSS Source | `<OSS_KEY_COUNT>` |
| Redis Enterprise Target | `<ENTERPRISE_KEY_COUNT>` |

Result:

```text
<PASS_OR_FAIL: Key counts match / Key counts do not match>
```

Snapshot:

`<PLACEHOLDER: screenshots/key-count-validation.png>`

## 8. Optional Notes: Issues Faced and Resolution

### Issue 1: `<ISSUE_TITLE>`

Problem:

```text
<DESCRIBE_WHAT_FAILED_HERE>
```

Root cause:

```text
<DESCRIBE_ROOT_CAUSE_HERE>
```

Resolution:

```text
<DESCRIBE_HOW_IT_WAS_RESOLVED_HERE>
```

Snapshot:

`<PLACEHOLDER: screenshots/issues/issue-1-resolution.png>`

### Issue 2: `<ISSUE_TITLE>`

Problem:

```text
<DESCRIBE_WHAT_FAILED_HERE>
```

Resolution:

```text
<DESCRIBE_HOW_IT_WAS_RESOLVED_HERE>
```

Snapshot:

`<PLACEHOLDER: screenshots/issues/issue-2-resolution.png>`

## Submission Checklist

- [ ] Redis OSS `7.2.0` installed on Server A without Docker.
- [ ] Redis OSS default port `6379` changed.
- [ ] Persistence enabled with AOF for best durability guarantees.
- [ ] `redis.conf` path included.
- [ ] `redis.conf` key configuration snippet included.
- [ ] `memtier-benchmark` command included in runnable text format.
- [ ] Throughput and latency numbers captured.
- [ ] Redis Enterprise installed on Server B using no-DNS setup.
- [ ] Redis Enterprise database configuration snapshot included.
- [ ] Redis Enterprise replication status snapshot included.
- [ ] Redis OSS key count matches Redis Enterprise database key count.
- [ ] Optional failure / resolution notes added, if applicable.
