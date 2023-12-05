import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import sys
import threading
import time
from flask import Flask, jsonify, request

class Order:
    def __init__(self, order_id, rim_id, tyre_id, status="Scheduled"):
        self.order_id = order_id
        self.rim_id = rim_id
        self.tyre_id = tyre_id
        self.status = status
        self.scheduled_time = None

class MES:
    def __init__(self, update_interval=1000):
        self.orders = []
        self.update_interval = update_interval
        self.callback = None
        self.root = None

        self.rim_dataset = {
            "Felge1_Schwarz": 40,
            "Felge2_Silber": 30,
            "Felge3_Rot": 50,
        }
        self.tyre_dataset = {
            "Reife1_Schwarz_Sommer": 35,
            "Reife2_Blau_Winter": 25,
            "Reife3_AllWetter": 45,
        }


        self.keep_running=True;
        self.energy_consumption_init=10;
        self.energy_consumption=[10];
        self.max_energy = 100
        self.min_energy = 0
        self.fluctuation_range = 3

        self.heat_sensor1=[20];
        self.heat_sensor2=[25];

        self.fig, self.ax = plt.subplots(2, 2, figsize=(8, 6))
        plt.subplots_adjust(bottom=0.1, right=0.95, top=1) 
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=0, rowspan=1, sticky=tk.W + tk.E + tk.N + tk.S, pady=2)

        self.update_bar_charts()
        self.update_heat_charts()
        self.update_energy_chart()
        self.schedule_energy_update()
        self.schedule_heat_update()
        
        self.order_processing_robot = threading.Thread(target=self.process_order)
        self.order_processing_robot.start();
        
        self.heat_sensors=threading.Thread(target=self.generateHeat)
        self.heat_sensors.start();
        
        
    
        # Flask app
        self.app = Flask(__name__)

        # Add routes for web service
        self.app.add_url_rule('/get_rims', 'get_rims', self.get_rims_web_service)
        self.app.add_url_rule('/get_tyres', 'get_tyres', self.get_tyres_web_service)
        self.app.add_url_rule('/get_order_status/<int:order_id>', 'get_order_status', self.get_order_status_web_service)
        self.app.add_url_rule('/add_order', 'add_order', self.add_order_web_service, methods=['POST'])

        # Start Flask in a separate thread
        self.flask_thread = threading.Thread(target=self.app.run, kwargs={'port': 5000})
        self.flask_thread.start()
        
        
    def get_rims_web_service(self):
        return jsonify({"Felgen": self.get_rims()})

    def get_tyres_web_service(self):
            return jsonify({"Reifen": self.get_tyres()})

    def get_order_status_web_service(self, order_id):
        order = next((order for order in self.orders if order.order_id == order_id), None)
        if order:
            return jsonify({"Auftragsnummer": order.order_id, "status": order.status})
        else:
            return jsonify({"error": "Auftrag Nicht gefunden"}), 404

    def add_order_web_service(self):
        data = request.get_json()
        rim_id = data.get('rim_id')
        tyre_id = data.get('tyre_id')

        order = self.add_order(rim_id, tyre_id)
        print (order.order_id)
        if order:
            data = {
                "message": "Auftrag wurde erfoglreich erstellt.",
                "order_id": str(order.order_id)
            }

            # Convert the dictionary to a JSON string
            json_data = jsonify(data) 
            return json_data
        else:
            return jsonify({"error": "Auftrag konnte nicht erstellt werden. Aufgetragte Felge oer Reife existiert nicht im Lager."}), 400

        
        

    def set_root(self, root):
        self.root = root
        self.schedule_energy_update()
        self.schedule_heat_update()

    def add_order(self, rim_id, tyre_id):
        if rim_id not in self.rim_dataset or tyre_id not in self.tyre_dataset or self.tyre_dataset[tyre_id] <= 0 or self.rim_dataset[rim_id] <= 0:
            messagebox.showwarning("Out of Stock", f"{rim_id} or {tyre_id} are out of stock!")
            return None

        order_id = len(self.orders) + 1
        new_order = Order(order_id, rim_id, tyre_id)
        new_order.scheduled_time = datetime.now() 
        self.orders.append(new_order)
        
        self.update_datasets(rim_id, tyre_id)
        if self.callback:
            self.callback()
            self.update_bar_charts()
            self.update_energy_chart()
        return new_order
    

    def update_order_status(self, order_id, new_status):
        for order in self.orders:
            if order.order_id == order_id:
                order.status = new_status
                if self.callback:
                    self.callback()
                return True
        return False

    def display_orders(self):
        return [(order.order_id, order.rim_id, order.tyre_id, order.status, order.scheduled_time) for order in self.orders]

    def get_rims(self):
        return list(self.rim_dataset.keys())

    def get_tyres(self):
        return list(self.tyre_dataset.keys())

    def schedule_order_update(self):
        self.root.after(self.update_interval, self.update_loop)

    def generateHeat(self):
        while(self.keep_running):
            in_progress_order = next((order for order in self.orders if order.status == "In Progress"), None)
            
            if in_progress_order is None:
                #print("no progress in schedule")
                self.heat_sensor1.append( self.heat_sensor1[0]+random.uniform(-self.fluctuation_range, self.fluctuation_range));
                self.heat_sensor2.append(self.heat_sensor2[0]+random.uniform(-self.fluctuation_range, self.fluctuation_range))
            else: 
                self.heat_sensor1.append( self.heat_sensor1[0]+5+random.uniform(-self.fluctuation_range, self.fluctuation_range));
                self.heat_sensor2.append(self.heat_sensor2[0]+random.uniform(-self.fluctuation_range, self.fluctuation_range))
            
            time.sleep(1)     
            
            
            
    def process_order(self):
        while (self.keep_running):
    # Check if there is any order In Progress
            #print("process order is running")
            in_progress_order = next((order for order in self.orders if order.status == "In Progress"), None)
            #print("in progress order next"+str(in_progress_order))
            if in_progress_order is None:
                # If no order is In Progress, find the next scheduled order and change its status
                next_scheduled_order = next((order for order in self.orders if order.status == "Scheduled"), None)
                if next_scheduled_order is None:
                    time.sleep(10)
                else: 
                    #print("scheduling next task to in progress")
                    self.update_order_status(next_scheduled_order.order_id, "In Progress")
                    #print("staus changed, going to sleep")
                    time.sleep(10+ random.uniform(-2, 3))
                    self.update_order_status(next_scheduled_order.order_id, "Done")
                    time.sleep(2+ random.uniform(-2, 3))
                
                
            

    def update_loop(self):
        

        self.callback()
        self.update_energy_consumption()
        
        self.root.after(self.update_interval, self.update_loop)

    def update_energy_consumption(self):
        if any(order.status == "In Progress" for order in self.orders):
            new_energy = min(max(self.energy_consumption_init + random.uniform(-self.fluctuation_range, self.fluctuation_range), self.min_energy + 80), self.max_energy)
        else:
            new_energy = min(max(self.energy_consumption_init + random.uniform(-self.fluctuation_range, self.fluctuation_range), self.min_energy+ 10), self.max_energy)

        self.energy_consumption.append(new_energy)

    def update_datasets(self, rim_id, tyre_id):
        if rim_id.startswith("Felge") and rim_id in self.rim_dataset and self.rim_dataset[rim_id] > 0:
            self.rim_dataset[rim_id] -= 1
        if tyre_id.startswith("Reife") and tyre_id in self.tyre_dataset and self.tyre_dataset[tyre_id] > 0:
            self.tyre_dataset[tyre_id] -= 1

    def update_bar_charts(self):
        for ax in self.ax[:2]:
            ax[0].clear()

        rims_chart = self.ax[0,0].bar(self.rim_dataset.keys(), self.rim_dataset.values(), color='silver')
        self.ax[0,0].set_ylabel('Remaining Rims')
        self.ax[0,0].tick_params(axis='x', rotation=5)

        tyres_chart = self.ax[0,1].bar(self.tyre_dataset.keys(), self.tyre_dataset.values(), color='black')
        self.ax[0,1].set_ylabel('Remaining Tyres')
        self.ax[0,1].tick_params(axis='x', rotation=5)

        self.canvas.draw()

    def update_energy_chart(self):
        for ax in self.ax[2:]:
            ax[0].clear()

        self.ax[1,0].plot(range(len(self.energy_consumption)), self.energy_consumption, color='red')
        self.ax[1,0].set_ylabel('Energy Consumption')
        self.ax[1,0].set_xlabel('Time')

        self.canvas.draw()
    
    
    def update_heat_charts(self):
        for ax in self.ax[3:]:
            ax[0].clear()

        self.ax[1,1].plot(range(len(self.heat_sensor1)), self.heat_sensor1, color='purple')
        self.ax[1,1].set_ylabel('Temprature')
        self.ax[1,1].set_xlabel('Time')

        self.canvas.draw()



    def schedule_energy_update(self):
        if self.root:
            self.root.after(1000, self.update_energy_chart_continuously)
            
    

    def update_energy_chart_continuously(self):
        self.update_energy_chart()
        if self.root:
            self.root.after(1000, self.update_energy_chart_continuously)
            
    def schedule_heat_update(self):
        if self.root:
            self.root.after(1000, self.update_heat_chart_continuously)        
            
    def update_heat_chart_continuously(self):
        self.update_heat_charts()
        if self.root:
            self.root.after(1000, self.update_heat_chart_continuously)

class AddOrderWindow:
    def __init__(self, parent, mes_system):
        self.parent = parent
        self.mes_system = mes_system
        self.window = tk.Toplevel(parent)
        self.window.title("Neuer Auftrag erstellen")

        self.rims = mes_system.get_rims()
        self.tyres = mes_system.get_tyres()

        self.rim_var = tk.StringVar()
        self.tyre_var = tk.StringVar()

        self.rim_label = ttk.Label(self.window, text="Felge:")
        self.rim_label.grid(row=0, column=0, padx=10, pady=10)
        self.rim_combo = ttk.Combobox(self.window, textvariable=self.rim_var, values=self.rims, state="readonly")
        self.rim_combo.grid(row=0, column=1, padx=10, pady=10)

        self.tyre_label = ttk.Label(self.window, text="Reife:")
        self.tyre_label.grid(row=1, column=0, padx=10, pady=10)
        self.tyre_combo = ttk.Combobox(self.window, textvariable=self.tyre_var, values=self.tyres, state="readonly")
        self.tyre_combo.grid(row=1, column=1, padx=10, pady=10)

        self.add_button = ttk.Button(self.window, text="Neuer Auftrag erstellen", command=self.add_order)
        self.add_button.grid(row=2, column=0, columnspan=2, pady=10)

    def add_order(self):
        rim_id = self.rim_var.get()
        tyre_id = self.tyre_var.get()
        order = self.mes_system.add_order(rim_id, tyre_id)
        if order:
            messagebox.showinfo("Auftrag erstellt", f"Order {order.order_id} added successfully.")

class MESApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MES System")

        self.mes_system = MES()
        self.mes_system.set_root(root)

        self.frame = ttk.Frame(self.root, padding="1")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.label = ttk.Label(self.frame, text="MES System", font=("Helvetica", 16))
        self.label.grid(row=0, column=0, columnspan=2, pady=1)

        self.add_order_button = ttk.Button(self.frame, text="Neuer Auftrag erstellen", command=self.open_add_order_window)
        self.add_order_button.grid(row=1, column=0, pady=1)

        self.orders_tree = ttk.Treeview(self.frame, columns=("Order ID", "Rim ID", "Tyre ID", "Status", "Scheduled Time"), show="headings")
        self.orders_tree.heading("Order ID", text="Order ID")
        self.orders_tree.heading("Rim ID", text="Rim ID")
        self.orders_tree.heading("Tyre ID", text="Tyre ID")
        self.orders_tree.heading("Status", text="Status")
        self.orders_tree.heading("Scheduled Time", text="Scheduled Time")
        self.orders_tree.grid(row=2, column=0, pady=1)

        self.mes_system.callback = self.refresh_orders_table
        self.mes_system.schedule_order_update()
        
        # Register the callback function to be called on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        # Stop threads and close the window
        self.mes_system.keep_running=False
        
        self.mes_system.order_processing_robot.join();
        self.mes_system.heat_sensors.join();
        
        self.root.destroy()
        sys.exit()

    def open_add_order_window(self):
        AddOrderWindow(self.root, self.mes_system)

    def refresh_orders_table(self):
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)

        for order_info in self.mes_system.display_orders():
            order_id, rim_id, tyre_id, status, scheduled_time = order_info
            if status == "Scheduled":
                color = "red"
            elif status == "In Progress":
                color = "blue"
            elif status == "Done":
                color = "green"
            else:
                color = "black"

            self.orders_tree.insert("", "end", values=(order_id, rim_id, tyre_id, status, scheduled_time), tags=(status,))
            self.orders_tree.tag_configure(status, background=color)

if __name__ == "__main__":
    
    root = tk.Tk()
    app = MESApp(root)
    root.mainloop()
  
    
