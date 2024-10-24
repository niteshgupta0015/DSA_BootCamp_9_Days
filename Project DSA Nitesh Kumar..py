import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime
import json
from typing import Optional, Dict, List, Tuple

class MessageQueue:
    def __init__(self, max_size: int):
        self.queue: List[Dict] = []
        self.max_size = max_size
        self.processed_messages: List[Dict] = []
    
    def is_empty(self) -> bool:
        return len(self.queue) == 0
    
    def is_full(self) -> bool:
        return len(self.queue) == self.max_size
    
    def enqueue(self, message: Dict) -> bool:
        if self.is_full():
            return False
        message['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.queue.append(message)
        return True
    
    def dequeue(self) -> Optional[Dict]:
        if self.is_empty():
            return None
        message = self.queue.pop(0)
        self.processed_messages.append(message)
        return message
    
    def size(self) -> int:
        return len(self.queue)
    
    def get_history(self) -> List[Dict]:
        return self.processed_messages

class DatabaseManager:
    def __init__(self):
        self.stored_data = {
            "restaurants": {
                "Domino's": {
                    "menu": ["Pizza", "Pasta", "Garlic Bread"],
                    "status": "Open",
                    "rating": 4.2
                },
                "McDonald's": {
                    "menu": ["Burgers", "Fries", "McFlurry"],
                    "status": "Open",
                    "rating": 4.0
                },
                "Starbucks": {
                    "menu": ["Coffee", "Sandwiches", "Pastries"],
                    "status": "Open",
                    "rating": 4.5
                }
            },
            "orders": {},
            "delivery_partners": {
                "DP001": {"name": "John", "status": "Available"},
                "DP002": {"name": "Sarah", "status": "Busy"}
            }
        }
        self.order_counter = 1000
        # Initialize with some sample orders
        self._create_sample_orders()

    def _create_sample_orders(self):
        # Create a few sample orders with different statuses
        sample_orders = [
            ("Domino's", ["Pizza", "Garlic Bread"], "Received"),
            ("McDonald's", ["Burgers", "Fries"], "Prepared"),
            ("Starbucks", ["Coffee", "Sandwiches"], "Delivered")
        ]
        
        for restaurant, items, status in sample_orders:
            order_id = f"ORDER#{self.order_counter}"
            self.stored_data["orders"][order_id] = {
                "status": status,
                "restaurant": restaurant,
                "items": items,
                "delivery_status": "Pending" if status != "Delivered" else "Delivered",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.order_counter += 1

    def create_order(self, restaurant: str, items: List[str]) -> str:
        order_id = f"ORDER#{self.order_counter}"
        self.order_counter += 1
        
        self.stored_data["orders"][order_id] = {
            "status": "Received",
            "restaurant": restaurant,
            "items": items,
            "delivery_status": "Pending",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return order_id

    def update_order_status(self, order_id: str, status: str) -> bool:
        if order_id in self.stored_data["orders"]:
            self.stored_data["orders"][order_id]["status"] = status
            return True
        return False

    def update_delivery_status(self, order_id: str, status: str) -> bool:
        if order_id in self.stored_data["orders"]:
            self.stored_data["orders"][order_id]["delivery_status"] = status
            return True
        return False

    def get_order_details(self, order_id: str) -> Optional[Dict]:
        # Normalize the order ID format
        if not order_id.upper().startswith("ORDER#"):
            order_id = f"ORDER#{order_id}"
        return self.stored_data["orders"].get(order_id)

class MessagingQueueGUI:
    def __init__(self, root, queue: MessageQueue, db: DatabaseManager):
        self.root = root
        self.root.title("Zomato Real-Time Messaging System")
        self.root.geometry("800x600")
        self.queue = queue
        self.db = db

        # Create main frames
        self.create_frames()
        self.create_role_selector()
        self.create_message_input()
        self.create_action_buttons()
        self.create_chat_display()
        self.create_status_bar()

        # Add keyboard shortcuts
        self.root.bind('<Return>', lambda e: self.send_message())
        self.root.bind('<Control-p>', lambda e: self.process_message())

        # Display initial help message
        self.display_message("System", "Welcome! Type 'NEW' to create a new order, or enter an order number (1000-1002) to check status.")

    def create_frames(self):
        # Main container with padding
        self.main_container = tk.Frame(self.root, padx=10, pady=5)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Individual frames
        self.top_frame = tk.Frame(self.main_container)
        self.top_frame.pack(fill=tk.X, pady=5)
        
        self.middle_frame = tk.Frame(self.main_container)
        self.middle_frame.pack(fill=tk.X, pady=5)
        
        self.bottom_frame = tk.Frame(self.main_container)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.status_frame = tk.Frame(self.main_container)
        self.status_frame.pack(fill=tk.X, pady=5)

    def create_role_selector(self):
        role_frame = tk.LabelFrame(self.top_frame, text="User Role", padx=5, pady=5)
        role_frame.pack(fill=tk.X)

        self.role_var = tk.StringVar(value="Customer")
        roles = ["Customer", "Restaurant", "Delivery Partner"]
        
        for role in roles:
            tk.Radiobutton(role_frame, text=role, variable=self.role_var, 
                          value=role, command=self.update_interface).pack(side=tk.LEFT, padx=10)

    def create_message_input(self):
        input_frame = tk.Frame(self.middle_frame)
        input_frame.pack(fill=tk.X, pady=5)

        self.message_label = tk.Label(input_frame, text="Message:")
        self.message_label.pack(side=tk.LEFT, padx=5)

        self.message_entry = tk.Entry(input_frame, width=50)
        self.message_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    def create_action_buttons(self):
        button_frame = tk.Frame(self.middle_frame)
        button_frame.pack(fill=tk.X, pady=5)

        tk.Button(button_frame, text="Send (Enter)", 
                 command=self.send_message,
                 relief=tk.RAISED, padx=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Process Message (Ctrl+P)", 
                 command=self.process_message,
                 relief=tk.RAISED, padx=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Clear Chat", 
                 command=self.clear_history,
                 relief=tk.RAISED, padx=10).pack(side=tk.LEFT, padx=5)

    def create_chat_display(self):
        self.chat_display = scrolledtext.ScrolledText(
            self.bottom_frame, wrap=tk.WORD, height=20,
            font=("Courier", 10))
        self.chat_display.pack(fill=tk.BOTH, expand=True)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(self.status_frame, textvariable=self.status_var,
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X)
        self.update_status()

    def update_status(self):
        queue_size = self.queue.size()
        max_size = self.queue.max_size
        self.status_var.set(f"Messages in Queue: {queue_size}/{max_size} | " +
                           f"Current Role: {self.role_var.get()} | " +
                           f"Processed Messages: {len(self.queue.processed_messages)}")

    def update_interface(self):
        role = self.role_var.get()
        if role == "Customer":
            self.message_label.config(text="Enter Order ID or 'NEW' for new order:")
        elif role == "Restaurant":
            self.message_label.config(text="Enter Order ID to update:")
        else:
            self.message_label.config(text="Enter Order ID to update delivery status:")

    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            messagebox.showwarning("Error", "Please enter a message")
            return

        role = self.role_var.get()
        message_data = {
            "role": role,
            "content": message
        }

        if self.queue.enqueue(message_data):
            self.display_message(f"{role}", message)
            self.message_entry.delete(0, tk.END)
            self.update_status()
            # Auto-process the message
            self.process_message()
        else:
            messagebox.showwarning("Queue Full", "Please process some messages first")

    def process_message(self):
        message = self.queue.dequeue()
        if message:
            response = self.generate_response(message["role"], message["content"])
            self.display_message("System", response)
            self.update_status()
        else:
            messagebox.showinfo("Queue Empty", "No messages to process")

    def generate_response(self, role: str, message: str) -> str:
        try:
            if role == "Customer":
                if message.upper() == "NEW":
                    order_id = self.db.create_order("Domino's", ["Pizza"])
                    return f"New order created: {order_id}"
                else:
                    order_details = self.db.get_order_details(message)
                    if order_details:
                        return (f"Order {message} Details:\n"
                               f"Restaurant: {order_details['restaurant']}\n"
                               f"Status: {order_details['status']}\n"
                               f"Delivery: {order_details['delivery_status']}\n"
                               f"Items: {', '.join(order_details['items'])}")
                    return "Order not found"

            elif role == "Restaurant":
                if self.db.update_order_status(message, "Prepared"):
                    return f"Order {message} marked as Prepared"
                return "Invalid order ID"

            elif role == "Delivery Partner":
                if self.db.update_delivery_status(message, "Delivered"):
                    return f"Order {message} marked as Delivered"
                return "Invalid order ID"

            return "Invalid request"

        except Exception as e:
            return f"Error processing request: {str(e)}"

    def display_message(self, sender: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.chat_display.see(tk.END)

    def clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear the chat history?"):
            self.chat_display.delete(1.0, tk.END)
            self.display_message("System", "Welcome! Type 'NEW' to create a new order, or enter an order number (1000-1002) to check status.")

def main():
    root = tk.Tk()
    root.title("Zomato Messaging System")
    
    # Set app theme
    root.tk_setPalette(background='#f0f0f0',
                      foreground='black',
                      activeBackground='#e0e0e0',
                      activeForeground='black')

    # Initialize components
    message_queue = MessageQueue(max_size=10)
    db_manager = DatabaseManager()
    
    # Create and run the application
    app = MessagingQueueGUI(root, message_queue, db_manager)
    
    # Center the window
    window_width = 800
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()