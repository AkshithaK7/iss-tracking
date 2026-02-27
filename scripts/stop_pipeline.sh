#!/bin/bash
# =============================================================
# stop_pipeline.sh
# Gracefully stops all pipeline components on the GCP VM:
#   1. ISS Python producer
#   2. Snowflake Kafka Connector
#   3. Kafka broker
#   4. Zookeeper
# =============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../config.env"

export PATH=/opt/homebrew/share/google-cloud-sdk/bin:"$PATH"

SSH="gcloud compute ssh ${GCP_VM_NAME} --zone=${GCP_ZONE} --project=${GCP_PROJECT} --command"

echo "==> [1/4] Stopping ISS producer..."
$SSH "pkill -f 'python3 -u producer.py' 2>/dev/null && echo 'Stopped' || echo 'Not running'"

echo "==> [2/4] Stopping Snowflake Kafka Connector..."
$SSH "pkill -f 'connect-standalone' 2>/dev/null && echo 'Stopped' || echo 'Not running'"
sleep 3

echo "==> [3/4] Stopping Kafka broker..."
$SSH "${KAFKA_HOME}/bin/kafka-server-stop.sh 2>/dev/null && echo 'Stopped' || echo 'Not running'"
sleep 3

echo "==> [4/4] Stopping Zookeeper..."
$SSH "${KAFKA_HOME}/bin/zookeeper-server-stop.sh 2>/dev/null && echo 'Stopped' || echo 'Not running'"

echo ""
echo "All pipeline components stopped."
