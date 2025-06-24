import json
import subprocess
import paho.mqtt.client as mqtt
import os

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "new_MPU_client"

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        uuid = payload["uuid"]
        ip = payload["ip"]
        port = payload["port"]
        policy = payload["runtime-policy"]

        policy_file = "policy.json"
        with open(policy_file, "w") as f:
            json.dump(policy, f)
        if not os.path.isfile(policy_file):
            raise Exception(f"Error saving policy file: {policy_file} not found")

        # Try to delete existing agent
        delete_result = subprocess.run(
            ["keylime_tenant", "-c", "delete", "--uuid", uuid],
            capture_output=True,
            text=True,
            check=False
        )
        if delete_result.returncode == 0:
            print(f"[MQTT] Agent {uuid} deleted (if it existed)")
        else:
            if "not found" in delete_result.stderr.lower():
                print(f"[MQTT] No existing agent found for {uuid}, continuing with add")
            else:
                print(f"[ERROR] Unexpected error while deleting agent {uuid}:\n{delete_result.stderr}")
                return

        # Try to add agent
        add_result = subprocess.run(
            [
                "keylime_tenant", "-c", "add",
                "--uuid", uuid,
                "-t", ip,
                "-tp", str(port),
                "--runtime-policy", policy_file
            ],
            capture_output=True,
            text=True,
            check=False
        )

        if add_result.returncode == 0:
            print(f"[MQTT] ✅ Attestation started for agent {uuid} ({ip}:{port})")
        else:
            if "conflict" in add_result.stderr.lower():
                print(f"[MQTT] Conflict: agent {uuid} already exists. Attempting update...")
                update_result = subprocess.run(
                    [
                        "keylime_tenant", "-c", "update",
                        "--uuid", uuid,
                        "-t", ip,
                        "-tp", str(port),
                        "--runtime-policy", policy_file
                    ],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if update_result.returncode == 0:
                    print(f"[MQTT] 🔄 Agent {uuid} updated successfully.")
                else:
                    print(f"[ERROR] Failed to update agent {uuid}:\n{update_result.stderr}")
            else:
                print(f"[ERROR] Failed to add agent {uuid}:\n{add_result.stderr}")

    except json.JSONDecodeError:
        print(f"[ERROR] Invalid JSON payload: {msg.payload}")
    except KeyError as e:
        print(f"[ERROR] Missing key in message: {e}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] keylime_tenant command error: {e}")
    except Exception as e:
        print(f"[ERROR] General error while handling MQTT message: {e}")

def start_mqtt_loop():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)
    client.on_message = on_message
    client.loop_forever()

if __name__ == "__main__":
    print(f"[MQTT] Listening on broker {MQTT_BROKER}:{MQTT_PORT} - Topic: {MQTT_TOPIC}")
    start_mqtt_loop()
