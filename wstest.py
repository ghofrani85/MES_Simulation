import requests

# Base URL for the web service
base_url = "http://127.0.0.1:5000"

# Function to add a new order via web service
def add_order(rim_id, tyre_id):
    data = {"rim_id": rim_id, "tyre_id": tyre_id}
    response = requests.post(f"{base_url}/add_order", json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return {"error": f"Error: {response.status_code}"}

if __name__ == "__main__":
    # Add a new order
    rim_id = "Felge1_Schwarz"
    tyre_id = "Reife1_Schwarz_Sommer"
    add_order_response = add_order(rim_id, tyre_id)

    if "error" in add_order_response:
        print(f"Failed to add order: {add_order_response['error']}")
    else:
        print(f"{add_order_response['message']}, Auftragsnummer: {add_order_response['order_id']}")


