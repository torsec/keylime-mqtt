import json
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "MPU_client_status"

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        uuid = payload["uuid"]
        trusted = payload["trusted"]

        status = "✅ TRUSTED" if trusted else "❌ UNTRUSTED"
        print(f"[MQTT] Agent {uuid}: {status}")

    except json.JSONDecodeError:
        print(f"[ERROR] Invalid JSON payload: {msg.payload}")
    except KeyError as e:
        print(f"[ERROR] Missing key in message: {e}")
    except Exception as e:
        print(f"[ERROR] General error while handling MQTT message: {e}")

def start_mqtt_loop():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)
    client.on_message = on_message
    client.loop_forever()

if __name__ == "__main__":
    print(f"[MQTT] 🔎 Listening for attestation results on {MQTT_BROKER}:{MQTT_PORT} - Topic: {MQTT_TOPIC}")
    start_mqtt_loop()
