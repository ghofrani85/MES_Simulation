import requests
import sys

# Base URL for the web service
base_url = "http://127.0.0.1:5000"

# Function to get order status via web service
def get_order_status(order_id):
    response = requests.get(f"{base_url}/get_order_status/{order_id}")

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return {"error": f"Error: {response.status_code}"}

if __name__ == "__main__":
    # Check if an order ID is provided in the command line arguments
    if len(sys.argv) != 2:
        print("Usage: python status_check.py <order_id>")
        sys.exit(1)

    # Read the order ID from the command line
    order_id_to_check = int(sys.argv[1])

    # Get the status of the order
    order_status_response = get_order_status(order_id_to_check)

    if "error" in order_status_response:
        print(f"Failed to get order status: {order_status_response['error']}")
    else:
        print(f"Status of Order {order_id_to_check}: {order_status_response['status']}")

