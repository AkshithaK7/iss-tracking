#!/bin/bash
# =============================================================
# setup_vm.sh
# Run this ONCE to provision the GCP VM for the ISS pipeline.
# It installs Java, Python, Kafka, and the Snowflake connector.
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../config.env"

export PATH=/opt/homebrew/share/google-cloud-sdk/bin:"$PATH"

SSH="gcloud compute ssh ${GCP_VM_NAME} --zone=${GCP_ZONE} --project=${GCP_PROJECT} --command"

echo "==> [1/6] Installing Java 11 and Python 3 on VM..."
$SSH "sudo apt update -y && sudo apt install -y openjdk-11-jdk python3 python3-pip"

echo "==> [2/6] Installing Python dependencies on VM..."
$SSH "pip3 install confluent-kafka requests"

echo "==> [3/6] Downloading Kafka ${KAFKA_VERSION}..."
$SSH "curl -O https://archive.apache.org/dist/kafka/3.7.0/kafka_${KAFKA_VERSION}.tgz && tar -xzf kafka_${KAFKA_VERSION}.tgz"

echo "==> [4/6] Downloading Snowflake Kafka Connector JAR..."
$SSH "mkdir -p ${PLUGINS_DIR} && curl -L -o ${PLUGINS_DIR}/snowflake-kafka-connector.jar https://repo1.maven.org/maven2/com/snowflake/snowflake-kafka-connector/2.1.2/snowflake-kafka-connector-2.1.2.jar"

echo "==> [5/6] Adding plugin.path to connect-standalone.properties..."
$SSH "grep -q 'plugin.path' ${KAFKA_HOME}/config/connect-standalone.properties || echo 'plugin.path=${PLUGINS_DIR}' >> ${KAFKA_HOME}/config/connect-standalone.properties"

echo "==> [6/6] Copying producer, connector config, and RSA key to VM..."
gcloud compute scp "$SCRIPT_DIR/../producer.py"          ${GCP_VM_NAME}:~/producer.py          --zone=${GCP_ZONE} --project=${GCP_PROJECT}
gcloud compute scp "$SCRIPT_DIR/../SF_connect.properties" ${GCP_VM_NAME}:~/SF_connect.properties --zone=${GCP_ZONE} --project=${GCP_PROJECT}
gcloud compute scp "$SCRIPT_DIR/../keys/rsa_key.pem"     ${GCP_VM_NAME}:~/rsa_key.pem          --zone=${GCP_ZONE} --project=${GCP_PROJECT}

echo ""
echo "VM setup complete. Run scripts/start_pipeline.sh to start the pipeline."
