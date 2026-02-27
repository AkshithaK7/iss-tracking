#!/bin/bash
# =============================================================
# start_pipeline.sh
# Starts all pipeline components on the GCP VM:
#   1. Zookeeper
#   2. Kafka broker
#   3. Creates Kafka topic (idempotent)
#   4. Snowflake Kafka Connector
#   5. ISS Python producer
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../config.env"

export PATH=/opt/homebrew/share/google-cloud-sdk/bin:"$PATH"

SSH="gcloud compute ssh ${GCP_VM_NAME} --zone=${GCP_ZONE} --project=${GCP_PROJECT} --command"

echo "==> [1/5] Starting Zookeeper..."
$SSH "bash -c 'nohup ${KAFKA_HOME}/bin/zookeeper-server-start.sh ${KAFKA_HOME}/config/zookeeper.properties > /tmp/zookeeper.log 2>&1 </dev/null &'"
sleep 5
echo "    Zookeeper started. Log: /tmp/zookeeper.log"

echo "==> [2/5] Starting Kafka broker..."
$SSH "bash -c 'nohup ${KAFKA_HOME}/bin/kafka-server-start.sh ${KAFKA_HOME}/config/server.properties > /tmp/kafka.log 2>&1 </dev/null &'"
sleep 8
echo "    Kafka broker started. Log: /tmp/kafka.log"

echo "==> [3/5] Creating Kafka topic '${KAFKA_TOPIC}' (if not exists)..."
$SSH "${KAFKA_HOME}/bin/kafka-topics.sh --create --if-not-exists --topic ${KAFKA_TOPIC} --bootstrap-server ${KAFKA_BROKER} --partitions 1 --replication-factor 1" || true
echo "    Topic '${KAFKA_TOPIC}' ready."

echo "==> [4/5] Starting Snowflake Kafka Connector..."
$SSH "bash -c 'nohup ${KAFKA_HOME}/bin/connect-standalone.sh ${KAFKA_HOME}/config/connect-standalone.properties ~/SF_connect.properties > /tmp/connector.log 2>&1 </dev/null &'"
sleep 5
echo "    Connector started. Log: /tmp/connector.log"

echo "==> [5/5] Starting ISS producer..."
$SSH "bash -c 'nohup python3 -u ~/producer.py > /tmp/producer.log 2>&1 </dev/null &'"
sleep 3
echo "    Producer started. Log: /tmp/producer.log"

echo ""
echo "Pipeline is running. To check status:"
echo "  gcloud compute ssh ${GCP_VM_NAME} --zone=${GCP_ZONE} --project=${GCP_PROJECT} --command='pgrep -a java; pgrep -a python3'"
echo ""
echo "To tail producer logs:"
echo "  gcloud compute ssh ${GCP_VM_NAME} --zone=${GCP_ZONE} --project=${GCP_PROJECT} --command='tail -f /tmp/producer.log'"
