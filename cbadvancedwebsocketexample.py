# Ryan Mercier 2024
# simple example of connecting to coinbase advanced trade websocket and plotting bitcoin price

from coinbase.websocket import WSClient
import json
from queue import Queue
from dateutil import parser
import pandas as pd
import mplfinance as mpf
import matplotlib.animation as animation  # Correct import

# Coinbase API credentials
api_key = "<your api keu>"
api_secret = "<your secret key>"

max_data_points = 1000

# Queue for inter-thread communication to store Bitcoin prices and timestamps for graphing
plot_queue = Queue()

# Define global variables for data
data = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close'], index=pd.DatetimeIndex([]))  # Initialize an empty DataFrame

# Function to handle WebSocket messages
def handle_message(msg):
    msg = json.loads(msg)
    if 'events' in msg and msg['events'] and 'tickers' in msg['events'][0]:
        ticker = msg['events'][0]['tickers'][0]
        if 'price' in ticker and 'timestamp' in msg:
            plot_queue.put((msg['timestamp'], ticker['price']))  # Put data in the queue

# retrieve price data
def get_data():
    global data
    timestamps = []
    prices = []
    while not plot_queue.empty():
        timestamp, price = plot_queue.get()  # Get data from the queue
        timestamps.append(pd.to_datetime(parser.parse(timestamp).timestamp(), unit='s'))
        prices.append(float(price))

    if timestamps and prices:
        temp = pd.DataFrame(
        {
            'Open': prices,
            'Close': prices,
            'High': prices,
            'Low': prices
        }, index=timestamps)

        return temp
    
    else:
        return data

# Define the animation function
def animate(ival, ax):
    global data
    new_data = get_data()
    if new_data is not None:
        data = pd.concat([data, new_data])

        if len(data) > max_data_points:
            data = data.iloc[-max_data_points:]  # Keep only the last max_data_points rows

        ax.clear()
        mpf.plot(data, type='line', ax=ax)


def main():
    global data

    # Initialize WebSocket client with the handle_message callback function
    ws_client = WSClient(api_key=api_key, api_secret=api_secret, on_message=handle_message)

    # Open WebSocket connection and subscribe to ticker channel
    ws_client.open()
    ws_client.subscribe(product_ids=["BTC-USD"], channels=["ticker"])

    while data.empty:
        data = get_data()

    try:
        # Plot the data
        fig, axes = mpf.plot(data, type='line', title='Bitcoin (BTC) Prices', xlabel='Time', ylabel='Price (USD)', style='charles', returnfig=True)
        ax = axes[0]
        
        def update(frame):
            ax.clear()
            animate(frame, ax)

        ani = animation.FuncAnimation(fig, update, frames=None, interval=1000, cache_frame_data=False, blit=False)
        mpf.show()

    except KeyboardInterrupt:
        print("Script terminated by user.")
    finally:
        # Close WebSocket connection
        ws_client.close()

if __name__ == "__main__":
    main()