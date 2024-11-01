import os
import re
import csv
import sys
import time
import bcrypt
import getpass
import validators
import pandas as pd
from os import name
from tabulate import tabulate
from rich.console import Console

# If admin logged in then true
admin_logged_in = False

# If user logged
user_logged_in = False

# Save the logged in user email, in case needed
logged_in_user_email = None


# Role class that handles user roles
class Role:
    def __init__(self):
        # Default role is "user"
        self.role = "user"

        # Check if running in admin mode
        if len(sys.argv) > 1 and sys.argv[1] == "--admin":
            self.role = "admin"

    def is_admin(self):
        return self.role == "admin"


# Creates user.csv and admin.csv during program initation if they don't exist
class CSVInitializer:
    headers = ['first name', 'last name', 'age', 'email', 'password']

    @staticmethod
    def initialize_csv_files():
        #Create both user and admin CSV files with headers if they don't exist.
        user_file_name = 'users.csv'
        admin_file_name = 'admin.csv'
        user_cart_name = 'user_cart.csv'

        # Initialize user CSV file
        if not os.path.exists(user_file_name):
            with open(user_file_name, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=CSVInitializer.headers)
                writer.writeheader()

        # Initialize admin CSV file
        if not os.path.exists(admin_file_name):
            with open(admin_file_name, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=CSVInitializer.headers)
                writer.writeheader()



# Handles authorization CSV I/O
class CSVHandler:

    # Dynamically select the right CSV
    @staticmethod
    def get_file_name():
        #Return the appropriate CSV file name based on the mode.
        return 'admin.csv' if Role().is_admin() else 'users.csv'


    # CSV get user
    @staticmethod
    def check_user_exists(file_name, email):
        # Check if a user with the specified email exists in the CSV file.
        with open(file_name, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["email"] == email:
                        return True
        return False


    # CSV users writer
    @staticmethod
    def write_to_csv(file_name, content):
        # Write content to the specified CSV file.
        with open(file_name, mode='a', newline="") as file:
            writer = csv.writer(file)
            writer.writerow(content)


    # CSV password checker
    @staticmethod
    def validate_user_password(email, password, file_name):
        # Validate user's password by checking the CSV file.
        with open(file_name, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["email"] == email:
                    hashed_password = row["password"]
                    # Check the entered password against the stored hashed password
                    if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                        return True
        return False


    # CSV Admin key reader
    @staticmethod
    def read_admin_key(file_name):
        with open(file_name, mode='r') as file:
                return file.read().strip()


    # CSV Admin key writer
    @staticmethod
    def write_admin_key(file_name, content):
        with open(file_name, mode='w') as file:
                file.write(content)
        return True


    # CSV Stock getter
    def read_stock_csv():
        # Read the CSV file
        file = pd.read_csv('stock.csv')

        file.columns = file.columns.str.upper()

        desired_order = ['ID', 'NAME', 'CATEGORY', 'STOCK', 'PRICE']

        for category in file['CATEGORY'].unique():
            category_data = file[file['CATEGORY'] == category]

            if not category_data.empty:

                category_data = category_data[desired_order]

                category_data['PRICE'] = category_data['PRICE'].apply(lambda x: f"{x:.2f}")

                print(f"Items in {category}:")
                print(tabulate(category_data, headers='keys', tablefmt='heavy_grid', showindex=False))
                print("\n")
            else:
                print(f"No items found in {category}.")


    # Check if item exists in inventory
    def item_exists(name, category):
    # Read the stock CSV file
        df = pd.read_csv('stock.csv')

        # Check if an item with the same name and category exists
        exists = df[(df['name'] == name) & (df['category'] == category)].any().any()

        return exists


    # Check if item exists in cart
    def item_exists_cart(name, category):
        df_cart = pd.read_csv('user_cart.csv')

        exists = df_cart[(df_cart['name'] == name) & (df_cart['category'] == category)].any().any()

        return exists



    # Match the stock of the item with name and category and validate quantity
    def check_quantity_stock(name, category, quantity):
        df = pd.read_csv('stock.csv')

        item_row = df[(df['name'] == name) & (df['category'] == category)]

        if not item_row.empty:
            available_stock = int(item_row['stock'].values[0])
            if quantity <= available_stock:
                return True
            else:
                return False
        else:
            return False


    # Write Stocks into Inventory
    def write_stock_csv(action, content):
        df = pd.read_csv('stock.csv')

        if action == 'add':
            # Check if the DataFrame is empty, and if so, set the max_id for the category to 0
            if not df.empty:

                # Filter the DataFrame for the specific category to find the max ID in that category
                category_df = df[df['category'] == content['category']]
                if not category_df.empty:
                    max_id = category_df['id'].max()
                else:
                    max_id = 0
            else:
                max_id = 0

            # Assign a new ID to the content based on the max ID in that category
            content['id'] = max_id + 1

            content_df = pd.DataFrame([content])

            df = pd.concat([df, content_df], ignore_index=True)

            df = df.sort_values(by=['category', 'id']).reset_index(drop=True)

            df.to_csv('stock.csv', index=False)

            return True

        elif action == 'delete':

            # Filter out rows where both 'name' and 'category' match the content
            df = df[~((df['name'] == content['name']) & (df['category'] == content['category']))]

            df.reset_index(drop=True, inplace=True)

            df['id'] = df.groupby('category').cumcount() + 1

            df.to_csv('stock.csv', index=False)
            return True

        elif action == 'update':

            # Example: Update stock and price based on name and category
            mask = (df['name'] == content['name']) & (df['category'] == content['category'])

            if not mask.any():
                return "Item not found for update."

            if 'price' in content and content['price'] != 0.0:
                df.loc[mask, 'price'] = content['price']
            if 'stock' in content and content['stock'] != 0.0:
                df.loc[mask, 'stock'] = content['stock']

            df.to_csv('stock.csv', index=False)
            return True


    # Read the cart and Tabulate
    def read_user_cart():
            # Read the CSV file
            try:
                cart = pd.read_csv('user_cart.csv')
            except FileNotFoundError:
                print("Cart empty. Please add items to cart\nRedirecting to User Page.")
                time.sleep(1.5)
                user_page()
                return

            # Convert column names to uppercase
            cart.columns = cart.columns.str.upper()

            desired_order = ['NAME', 'CATEGORY', 'UNIT PRICE', 'QUANTITY', 'TOTAL PRICE']

            if not cart.empty:

                # Reorder and select only the desired columns
                cart = cart[desired_order]

                cart_total = cart['TOTAL PRICE'].sum()
                total_quantity = cart['QUANTITY'].sum()

                cart['UNIT PRICE'] = cart['UNIT PRICE'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "0.00")
                cart['TOTAL PRICE'] = cart['TOTAL PRICE'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "0.00")


                print(f"Total Cart Value: {cart_total:.2f}\nTotal Items: {total_quantity}")
                print(tabulate(cart, headers='keys', tablefmt='heavy_grid', showindex=False))
                print("\n")
                return True
            else:
                print("CART IS EMPTY. LET'S GO SHOPPING.")
                return False


    # Handles cart writting functionalities
    def write_to_cart(action, content):
        if action == 'add':
            df_stock = pd.read_csv('stock.csv')

            item_row_stock = df_stock[(df_stock['name'] == content['name']) & (df_stock['category'] == content['category'])]

            if not item_row_stock.empty:
                unit_price = float(item_row_stock['price'].values[0])

                total_price = int(content['quantity']) * unit_price

                new_row = {
                    'name': content['name'],
                    'category': content['category'],
                    'unit price': unit_price,
                    'quantity': int(content['quantity']),
                    'total price': total_price
                }

                df_items = pd.DataFrame([new_row])

                # Read the user_cart CSV or create it if it doesn't exist
                try:
                    df_cart = pd.read_csv('user_cart.csv')
                except FileNotFoundError:
                    df_cart = pd.DataFrame(columns=['name', 'category', 'unit price', 'quantity', 'total price'])

                # Add to cart functionalities
                exists = not df_cart[(df_cart['name'] == content['name']) & (df_cart['category'] == content['category'])].empty
                if exists:
                    # Update the quantity and total price for existing items in the cart
                    cart_mask = (df_cart['name'] == content['name']) & (df_cart['category'] == content['category'])
                    df_cart.loc[cart_mask, 'quantity'] += int(content['quantity'])
                    df_cart.loc[cart_mask, 'total price'] = df_cart.loc[cart_mask, 'quantity'] * unit_price
                else:
                    df_cart = pd.concat([df_cart, df_items], ignore_index=True)

                # Update the stock
                stock_mask = (df_stock['name'] == content['name']) & (df_stock['category'] == content['category'])
                df_stock.loc[stock_mask, 'stock'] -= int(content['quantity'])

            # Write to the stock and cart CSV files
            df_stock.to_csv('stock.csv', index=False)
            df_cart.to_csv('user_cart.csv', index=False)

            return True

        # Delete items from cart functionalities
        elif action == 'delete':
            df_user_cart = pd.read_csv('user_cart.csv')
            df_inventory = pd.read_csv('stock.csv')

            cart_mask = (df_user_cart['name'] == content['name']) & (df_user_cart['category'] == content['category'])
            cart_quantity = df_user_cart.loc[cart_mask, 'quantity'].sum()

            if cart_quantity > 0:

                inventory_mask = (df_inventory['name'] == content['name']) & (df_inventory['category'] == content['category'])
                df_inventory.loc[inventory_mask, 'stock'] += cart_quantity

                df_user_cart = df_user_cart[~cart_mask]

                df_user_cart.to_csv('user_cart.csv', index=False)
                df_inventory.to_csv('stock.csv', index=False)

                return True
            else:
                return False


        # Update cart functionalities
        elif action == 'update':
            df_user_cart_update = pd.read_csv('user_cart.csv')
            df_inventory_update = pd.read_csv('stock.csv')

            cart_mask_update = (df_user_cart_update['name'] == content['name']) & (df_user_cart_update['category'] == content['category'])
            cart_update_quantity = df_user_cart_update.loc[cart_mask_update, 'quantity'].sum()

            if cart_update_quantity > 0:

                inventory_update_mask = (df_inventory_update['name'] == content['name']) & (df_inventory_update['category'] == content['category'])

                price = df_inventory_update.loc[inventory_update_mask, 'price'].values[0]

                new_quantity = content['quantity']

                df_inventory_update.loc[inventory_update_mask, 'stock'] += (cart_update_quantity - new_quantity)

                df_user_cart_update.loc[cart_mask_update, 'quantity'] = new_quantity
                df_user_cart_update.loc[cart_mask_update, 'total price'] = price * new_quantity

                df_user_cart_update.to_csv('user_cart.csv', index=False)
                df_inventory_update.to_csv('stock.csv', index=False)

                return True
            else:
                return False



    # Completely clear the CSV except the headers
    def user_clear_cart():
        df_cart = pd.read_csv('user_cart.csv')
        df_inventory = pd.read_csv('stock.csv')

        for index, row in df_cart.iterrows():
            cart_name = row['name']
            cart_category = row['category']
            cart_quantity = row['quantity']

            inventory_mask = (df_inventory['name'] == cart_name) & (df_inventory['category'] == cart_category)

            df_inventory.loc[inventory_mask, 'stock'] += cart_quantity

        df_inventory.to_csv('stock.csv', index = False)

        headers = df_cart.columns
        pd.DataFrame(columns=headers).to_csv('user_cart.csv', index=False)


    # Just clear the cart CSV
    def checkout_clear_cart():
        df_cart = pd.read_csv('user_cart.csv')

        headers = df_cart.columns
        pd.DataFrame(columns=headers).to_csv('user_cart.csv', index=False)




# Handles Admin Key realted methods
class Admin_key:
    def __init__(self):
        self.file_name = 'key.txt'
        self._admin_key = self.read_key_txt()


    @property
    def admin_key(self):
        return self._admin_key

    @admin_key.setter
    def admin_key(self, new_key):
        self.set_admin_key(new_key)

    def read_key_txt(self):
        try:
            return CSVHandler().read_admin_key(self.file_name)
        except FileNotFoundError:
            sys.exit("Key file not found. Contact Customer Support.")

    def validate_new_key_pattern(self, new_key):
        # Check if the new key follows the required pattern
        if match_admin_key_pattern(new_key):
            return True
        print("Invalid admin key format. Please try again.")
        return False

    def set_admin_key(self, new_key):
        # Hash and store the new admin key in the CSV
        hashed_new_admin_key = password_hasher(new_key)
        if CSVHandler().write_admin_key(self.file_name, hashed_new_admin_key):
            self._admin_key = hashed_new_admin_key
            return True
        return False


    def validate_admin_key(self, key):
        # Validate the provided key against the stored admin key
        if bcrypt.checkpw(key.encode('utf-8'), self.admin_key.encode('utf-8')):
            return True
        print("Incorrect admin key. Please try again.")
        return False

    @staticmethod
    def compare_new_key(input1, input2):
        if input1 != input2:
            print("Keys do not match. Please try again.")
            return False
        return True






# Class for signup with associated methods
class Signup:
    def __init__(self,first_name,last_name,age,email,password,password2,admin_key=None):
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self.email = email
        self.password = password
        self.password2 = password2
        self.admin_key = admin_key
        self.hashed_password = None

    def validate_firstname(self):

        if not self.first_name.isalpha():
            print("Invalid first name. Must only contain letters.")
            return False
        return True

    def validate_lastname(self):
            if not self.last_name.isalpha():
                print("Invalid last name. Must only contain letters.")
                return False
            return True


    def validate_age(self):
        if not self.age.isdigit() or int(self.age) <= 18:
            print("Invalid age. Must be a number above 18.")
            return False
        return True

    def validate_email(self):
        if not validators.email(self.email):
            print("Invalid email format.")
            return False
        elif email_exists(self.email):
            print("Email already exists.")
            return False
        return True

    def validate_password(self):
         #Validate and return a hashed password.
        password_pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{7,12}$"
        if not re.match(password_pattern, self.password):
            print("Invalid password format.")
            return None

        if self.password != self.password2:
            print("Passwords do not match.")
            return None


        self.hashed_password = password_hasher(self.password)
        return True

    # Stores the user's credentials in a CSV file.
    def store_credentials(self):


        # Ensure hashed_password is generated
        if self.hashed_password is None:
            print("No hashed password available.")
            return

        # Create a list of user details
        user_details = [self.first_name, self.last_name, self.age, self.email, self.hashed_password]

        # Pass it to CSVHandler to write to the appropriate CSV file
        CSVHandler.write_to_csv(CSVHandler.get_file_name(), user_details)




# Class for login with associated methods
class Login:
    def __init__(self, email,password):
        self.email = email
        self.password = password

    def validate_email(self):
        if not validators.email(self.email):
            print("Invalid email format.")
            return False
        elif not email_exists(self.email):
            print("Email does not exist. Please sign up or enter a valid email.")
            return False
        return True

    def authorize_password(self):
        # Match input password with hash in csv and authorise login
        return CSVHandler.validate_user_password(self.email, self.password, CSVHandler.get_file_name())





# Inventory management class
class Inventory:
    def __init__(self, name, category, quantity, price, id=None):
        self.name = name
        self.category = category
        self.quantity = quantity
        self.price = price
        self.id = id

    def add_to_inventory(self):
        # Adds a new item to the inventory after validation
        new_item = {
            'category': self.category,
            'stock': self.quantity,
            'price': self.price,
            'name': self.name
        }
        return CSVHandler.write_stock_csv('add', new_item)

    def del_from_inventory(self):
        # Deletes an item from the inventory if it exists.
        deleted_items = {
            'name': self.name,
            'category': self.category
        }
        return CSVHandler.write_stock_csv('delete', deleted_items)

    def update_inventory(self):
        # Updates the itme price or stock if it exists
        updated_items = {
            'category': self.category,
            'stock': self.quantity,
            'price': self.price,
            'name': self.name

        }
        return CSVHandler.write_stock_csv('update', updated_items)



# Cart class handles all cart functionalities
class Cart:
    def __init__(self, name, category, quantity):
        self.name = name
        self.category = category
        self.quantity = quantity

    def add_to_cart(self):
        add_cart = {
            'name':self.name,
            'category':self.category,
            'quantity':self.quantity,
        }
        return CSVHandler.write_to_cart('add', add_cart) is not None

    def update_cart(self):
        updated_cart = {
            'name':self.name,
            'category':self.category,
            'quantity':self.quantity,
        }
        return CSVHandler.write_to_cart('update', updated_cart) is not None

    def delete_cart(self):
        deleted_cart = {
            'name':self.name,
            'category':self.category,
        }
        return CSVHandler.write_to_cart('delete', deleted_cart) is not None

    def clear_cart():
        return CSVHandler.user_clear_cart()

    def checkout_clear_cart():
        return CSVHandler.checkout_clear_cart()






#-------------------------------------------------------------------------------------------------------------------------------#
#------FUNCTIONS THAT HANDLE AS PAGES-------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------------------------------------------#



# Router to map page to input
def route(page_name, id):
    routes = {
        'homepage': {
            '1': signup_page,
            'signup': signup_page,
            '2': login_page,
            'login': login_page,
            '3': exit_application
        },
        'admin_page': {
            '1': inventory_page,
            'inventory': inventory_page,
            '2': change_key_page,
            'change_key': change_key_page,
            '3': log_page,
            'log': log_page,
            '4': homepage,
            'log out': homepage,
        },
        'inventory_page': {
            'back': admin_page,
        },
        'user_page': {
            '1': view_product,
            'view product': view_product,
            '2': view_cart,
            'view cart': view_cart,
            '3': checkout,
            'checkout': checkout,
            '4': homepage,
            'Log Out': homepage,

        }
    }

    if page_name in routes and id in routes[page_name]:
        routes[page_name][id]()
    else:
        print("Invalid Response")


# Independent page based function
def router_homepage(id):
    route('homepage', id)

def router_adminpage(id):
    route('admin_page', id)

def router_inventory(id):
    route('inventory_page', id)

def router_userpage(id):
    route('user_page', id)

def exit_application():
    print("Exiting Application...\nGoodbye")
    time.sleep(1)
    clear()
    sys.exit()




# Homepage of the application i.e entry point
def homepage():
    Console().print("Welcome to the E-commerce™ store!", style='bold magenta', justify='center')
    actions_homepage = {
            '1': 'Sign Up',
            '2': 'Log In',
            '3': 'Exit',
        }

    print("Admin Mode") if Role().is_admin() else print("User Mode")

    print("Available options:")
    for id, action in actions_homepage.items():
        print(f"{id}. {action}")

    while True:
            choice = input("Enter the operation number you like to perform: ")
            if choice not in actions_homepage.keys():
                print("Invalid response")
            else:
                router_homepage(choice)
                break




# Sign up page calls the signup class
def signup_page():
    while True:

        while True:
            first_name = input("Enter your first name or 'back' to go back: ").strip()
            if first_name == 'back':
                    clear()
                    homepage()
            else:
                signup = Signup(first_name, "", "", "", "", "")
                if signup.validate_firstname():
                    break
                print("Please re-enter your first name.")

        # Validate last name
        while True:
            last_name = input("Enter your last name: ").strip()
            signup.last_name = last_name
            if signup.validate_lastname():
                break
            print("Please re-enter your last name.")

        # Validate age
        while True:
            age = input("Enter your age: ").strip()
            signup.age = age
            if signup.validate_age():
                break
            print("Please re-enter your age.")

        # Validate email
        while True:
            email = input("Enter your email ID: ").strip().lower()
            signup.email = email

            if signup.validate_email():
                break
            while True:

                choice = input('Type "login" to go to the login page or "retry" to enter email again: ').strip().lower()

                if choice == 'login':
                    router_homepage(choice)
                    return
                elif choice == 'retry':
                    break
                else:
                    print("Invalid response. Please type 'login' or 'retry'.")
                    continue


        # Validate password
        while True:
            password = getpass.getpass("Enter a password (7-12 characters with numbers and special characters): ")
            password2 = getpass.getpass("Re-enter your password: ")
            signup.password = password
            signup.password2 = password2
            if signup.validate_password():
                break

        # Admin key validation
        admin_key = None
        if Role().is_admin():
            while True:
                admin_key = getpass.getpass("Enter the admin key: ")
                if Admin_key().validate_admin_key(admin_key):
                    break
                print("Please re-enter the admin key.")


        signup.store_credentials()
        if Role().is_admin():
            clear()
            print("")
            print("Signup successful! \nRedirecting to admin page....")
            time.sleep(1)
            clear()
            admin_page()
        else:
            clear()
            print("")
            print("Signup successful! \nRedirecting to user page....")
            time.sleep(1)
            clear()
            user_page()
        break



# Login page calls the login class
def login_page():
    global logged_in_user_email
    global admin_logged_in, user_logged_in

    while True:
        email = input("Enter your email ID or 'back' to go back: ").strip().lower()
        if email == 'back':
            clear()
            homepage()
        else:
            login = Login(email, '')

            if login.validate_email():
                # Move to password validation if email is valid
                max_attempts = 3

                for attempt in range(max_attempts):

                    password = getpass.getpass("Enter your password: ").strip()
                    login.password = password

                    if login.authorize_password():
                        logged_in_user_email = login.email

                        # Check user role
                        if Role().is_admin():
                            admin_logged_in = True
                            clear()
                            print("")
                            print("Admin logged in.")
                            admin_page()
                        else:
                            user_logged_in = True
                            clear()
                            print("")
                            print("User logged in.")
                            user_page()

                        return

                    else:
                        print("Incorrect password. Please try again.")

                print("Too many failed attempts. Please try again later.")
                homepage()
                return

            else:
                while True:

                    choice = input('Type "signup" to go to the signup page or "retry" to enter email again: ').strip().lower()

                    if choice == 'signup':
                        router_homepage(choice)
                        return
                    elif choice == 'retry':
                        break
                    else:
                        print("Invalid response. Please type 'signup' or 'retry'.")
                        continue




# The page with admin functionalities
def admin_page():
    actions_admin = {
        '1': 'Update Inventory',
        '2': 'Change Admin Key',
        '3': 'View Log',
        '4': 'Log Out',
    }
    print("\nAdmin Dashboard - Available options:")
    for id, action in actions_admin.items():
            print(f"{id}. {action}")

    while True:
            choice = input("Enter the operation number you like to perform: ")
            if choice not in actions_admin.keys():
                print("Invalid response")
            else:
                clear()
                router_adminpage(choice)
                break


def change_key_page():
    global logged_in_user_email

    login = Login(logged_in_user_email, '')
    admin_key = Admin_key()

    while True:
        max_attempts = 3

        # Validate current admin key
        for attempt in range(max_attempts):
            current_admin_key = getpass.getpass("Enter your current admin key or 'Press Enter' to go back: ")
            if not current_admin_key:
                clear()
                admin_page()
            else:
                if admin_key.validate_admin_key(current_admin_key):
                    break
        else:
            print("Too many failed attempts. Please try again later.")
            time.sleep(1)
            homepage()
            return

        # Validate user password
        for attempt in range(max_attempts):
            password = getpass.getpass("Enter your password: ")
            login.password = password
            if login.authorize_password():
                break
            print("Incorrect password. Please try again.")
        else:
            print("Too many failed attempts. Please try again later.")
            time.sleep(1)
            clear()
            homepage()
            return

        # Get and validate new admin key (first and second entries)
        while True:
            new_admin_key = getpass.getpass("Enter the new admin key\n1.Must contain 6-8 characters\n2.Uppercase & Lowercase\n3.Numbers & Special characters\n: ")

            if admin_key.validate_new_key_pattern(new_admin_key):
                new_admin_key2 = getpass.getpass("Re-enter the new admin key: ")

                if admin_key.compare_new_key(new_admin_key, new_admin_key2):
                    if admin_key.set_admin_key(new_admin_key):
                        print("")
                        clear()
                        print("Admin key changed successfully\nRedirecting to admin page.")
                        time.sleep(1)
                        clear()
                        admin_page()
                        break



def inventory_page():
    inventory = Inventory("", "", 0, 0.0)
    clear()
    display_products()
    print(" ")
    while True:
        action = input("What action would you like to perform?\nAdd\nDelete\nUpdate\nBack:\n ").strip().lower()
        prompt = ['add', 'delete', 'update', 'back']

        if action in prompt:
            if action == 'add':
                while True:
                    try:
                        total_adds = int(input("How many unique items would you like to add? "))
                        break
                    except ValueError:
                        print("Please enter a valid number.")

                for _ in range(total_adds):
                    while True:
                        add_name = input("Enter item name: ")
                        if add_name:
                            add_category = input("Enter category: ")
                            if add_category:
                                if CSVHandler.item_exists(add_name, add_category):
                                    print("Item already exists, please enter a new item.")
                                    continue
                                inventory.name = add_name
                                inventory.category = add_category
                                break
                            else:
                                print("Category cannot be empty")
                        else:
                            print("Name cannot be empty")



                    while True:
                        try:
                            add_quantity = int(input("Enter stock: ").strip())
                            if validate_stock(add_quantity):
                                inventory.quantity = add_quantity
                                break
                        except ValueError:
                            print("Invalid stock entered. Please enter a positive integer.")

                    while True:
                        add_price = input("Enter price: ")
                        formatted_price = validate_price(add_price)

                        if formatted_price:
                            inventory.price = formatted_price
                            break
                        else:
                            print("Invalid price entered. Please enter a valid price.")

                    success = inventory.add_to_inventory()
                    if success:
                        print("Item added successfully.")
                    else:
                        print("Error: Item already exists in the inventory.")

                    time.sleep(1)
                    clear()
                    display_products()
                    time.sleep(1)

                input("Press Enter to go back to the admin page...")
                clear()
                router_inventory('back')

            elif action == 'delete':
                while True:
                    del_name = input("Enter item name (enter 'back' to go back): ").strip()
                    if del_name.lower() == 'back':  # Check if the user wants to go back
                        clear()
                        router_inventory('back')
                        break

                    # Get item category
                    del_category = input("Enter item category (enter 'back' to go back): ").strip()
                    if del_category.lower() == 'back':  # Check if the user wants to go back
                        clear()
                        router_inventory('back')
                        break

                    # Check if the item exists before proceeding to delete
                    if not CSVHandler.item_exists(del_name, del_category):
                        print("Item does not exist for deletion, please enter valida name and category")
                        continue

                    inventory.name = del_name
                    inventory.category = del_category

                    success = inventory.del_from_inventory()
                    if success:
                        print("Item deleted successfully.")
                    else:
                        print("Error: Unable to delete the item.")

                    time.sleep(1)
                    clear()
                    display_products()

                    # Go back to the admin page after deleting items
                    input("Press Enter to go back to the admin page...")
                    clear()
                    router_inventory('back')

            elif action == 'update':

                while True:
                    # Get item name and category, and check if they exist
                    update_name = input("Enter the item name: ").strip()
                    update_category = input("Enter the item category: ").strip()

                    if CSVHandler.item_exists(update_name, update_category):
                        # Set the inventory attributes
                        inventory.name = update_name
                        inventory.category = update_category

                        while True:
                            new_price = input(f"Enter the new price or leave blank to keep the existing price: ").strip()
                            if new_price:
                                formatted_new_price = validate_price(new_price)
                                if formatted_new_price:
                                    inventory.price = formatted_new_price
                                    break
                                else:
                                    print("Invalid price entered. Please enter a valid price.")
                            else:
                                print("Price unchanged.")
                                break


                        while True:
                            new_stock = input(f"Enter the new stock or leave blank to keep the existing stock: ").strip()
                            if new_stock:
                                try:
                                    new_stock = int(new_stock)
                                    if validate_stock(new_stock):
                                        inventory.quantity = new_stock
                                        break
                                    else:
                                        print("Invalid stock entered. Please enter a positive integer.")
                                except ValueError:
                                    print("Invalid input. Please enter a valid integer.")
                            else:
                                print("Stock unchanged.")
                                break


                        success = inventory.update_inventory()
                        if success:
                            print("Item updated successfully.")
                        else:
                            print("Error: Unable to update the item.")

                        time.sleep(1)
                        clear()
                        display_products()

                        # Go back to the admin page after updating items
                        input("Press Enter to go back to the admin page...")
                        clear()
                        router_inventory('back')

                    else:
                        print("Item does not exist in inventory.")

            elif action == 'back':
                clear()
                router_inventory('back')
        else:
           print("Invalid response. Please enter one of: Add, Delete, Update, Back.")


def log_page():
    print("Coming Soon....\nRedirecting to Admin Page")
    time.sleep(1.7)
    clear()
    admin_page()



# The page with user functionalities
def user_page():
    actions_user = {
        '1': 'View Products',
        '2': 'View Cart',
        '3': 'Checkout',
        '4': 'Log Out',
    }
    print("\nUser Dashboard - Available options:")
    for id, action in actions_user.items():
            print(f"{id}. {action}")

    while True:
            choice = input("Enter the operation number you like to perform: ").strip().lower()
            if choice not in actions_user.keys():
                print("Invalid response")
            else:
                clear()
                router_userpage(choice)
                break



# Product table and add to cart functionality
def view_product():
    cart = Cart('', '', 0)
    while True:
        #clear()
        display_products()
        print("CART")

        name = input("Enter the name of the item you want to add to the cart\nor 'back' to go back: ").strip()

        if name == 'back':
            clear()
            user_page()
            break

        category = input("Enter the category of that item: ").lower().strip()

        if CSVHandler.item_exists(name, category):
            cart.name = name
            cart.category = category

            while True:
                quantity_input = input("Enter the quantity you want to purchase: ").strip()

                # Check if the input is a valid integer
                if quantity_input.isdigit():
                    quantity = int(quantity_input)

                    if CSVHandler.check_quantity_stock(name, category, quantity):
                        cart.quantity = quantity
                        success = cart.add_to_cart()

                        if success:
                            #clear()
                            print("Items added to cart successfully\nRefreshing Inventory...")
                            time.sleep(1.5)
                        break
                    else:
                        print("Quantity exceeded stock. Please add a quantity <= stock")
                        time.sleep(1.3)
                else:
                    print("Please enter a valid quantity (positive integer).")
                    time.sleep(1.3)
        else:
            print("Item/Category does not exist.")
            time.sleep(1.7)




def view_cart():
    cart = Cart('', '', 0)
    clear()
    print("Your Cart")

    if not display_cart():
        input("Press any key to go back to the user page")
        clear()
        user_page()
        return

    actions_user = {
        '1': 'Remove Item',
        '2': 'Update Quantity',
        '3': 'Clear Cart',
        '4': 'Back',
    }

    print("\nUser Cart - Available options:")
    for id, action in actions_user.items():
        print(f"{id}. {action}")

    while True:
        choice = input("Enter the operation number you would like to perform: ").strip().lower()
        if choice not in actions_user.keys():
            print("Invalid response")
        else:
            if choice in ('1', 'remove item'):
                while True:
                    name = input("Enter name of the item: ")
                    category = input("Enter the category: ")
                    if CSVHandler.item_exists_cart(name, category):
                        cart.name = name
                        cart.category = category
                        success = cart.delete_cart()
                        if success:
                            print("Item successfully deleted from cart")
                            time.sleep(1)
                            clear()
                            view_cart()
                        else:
                            print("Error deleting item")
                            time.sleep(1)
                            clear()
                            view_cart()

                    else:
                        print("Item doesn't exist in cart")


            elif choice in ('2', 'update quantity'):
                while True:
                    name = input("Enter name of the item: ")
                    category = input("Enter the category: ")

                    if CSVHandler.item_exists_cart(name, category):
                        cart.name = name
                        cart.category = category

                        while True:
                            new_quantity = input("Enter the new quantity: ")

                            # Check if the input is a valid integer
                            if new_quantity.isdigit():
                                quantity = int(new_quantity)

                                if CSVHandler.check_quantity_stock(name, category, quantity):
                                    cart.quantity = quantity
                                    success = cart.update_cart()
                                    if success:
                                        print("Cart updated successfully\nRefreshing cart...")
                                        time.sleep(1.5)
                                        view_cart()
                                    break
                                else:
                                    print("Error: Quantity exceeds available stock. Please try again.")
                            else:
                                print("Invalid input. Please enter a valid integer for quantity.")

                    else:
                        print("Error: Item or Category does not exist. Please try again.")


            # Clear cart
            elif choice in ('3', 'clear cart'):
                clear_cart()
                break

            # Back to user page
            elif choice in ('4', 'back'):
                clear()
                user_page()
                break







# Handle Cart clearing and restocking the inventory
def clear_cart():
    while True:
        confirmation = input("This action will delete all items in the cart. Enter y/n to confirm: ").strip().lower()
        if confirmation == 'n':
            clear()
            print("Redirecting to User page....")
            time.sleep(1)
            user_page()
            break
        elif confirmation == 'y':
            clear()
            print("Clearing cart....")
            Cart.clear_cart()
            clear()
            time.sleep(1)
            display_cart()
            input("Press any key to go back to the user page")
            clear()
            user_page()
            break
        else:
            print("Invalid response. Please enter 'y' or 'n'.")


# Handles checkout logic clearing the cart csv
def checkout():
    cart_empty = not display_cart()

    if not cart_empty:
        print("Payment Gateway coming soon....")
        time.sleep(1)
        print("Order Successfully placed through CoD")
        time.sleep(1)
        print("Thank you for shopping")
        Cart.checkout_clear_cart()
        time.sleep(1.5)
        clear()
        print("Redirecting to user page.....")
        time.sleep(1)
        clear()
        user_page()
    else:
        print("Please add items to place an order")
        time.sleep(0.6)
        print("Redirecting to user page.....")
        time.sleep(0.8)
        clear()
        user_page()






# ------------------------------------------------------------------------------------------------------------------------------------------------ #
# -----INDEPENDENT FUNCTIONS---------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------------------ #

# Check if email already exists during signup
def email_exists(validated_email):
    return CSVHandler.check_user_exists(CSVHandler.get_file_name(), validated_email)

def validate_email(email):
    if not validators.email(email):
        return False
    return True

# Handle the hashing of password during signup
def password_hasher(password):
    # Hash the password if it is validated
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def match_admin_key_pattern(key):
    # Match admin key to regext
    admin_key_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+{}[\]:;<>,.?~`-])[A-Za-z\d!@#$%^&*()_+{}[\]:;<>,.?~`-]{6,12}$"
    return re.match(admin_key_pattern, key) is not None

# Validate quantity
def validate_stock(stock):
    if not isinstance(stock, int) or stock < 0:
        return False
    return True


# Validate Price
def validate_price(price):
    try:
        price_float = float(price)

        if price_float < 0:
            return False

        formatted_price = f"{price_float:.2f}"
        return formatted_price
    except ValueError:
        return False


# Displays inventory from the csv in a table
def display_products():
    CSVHandler.read_stock_csv()

# Displays cart from the csv in a table
def display_cart():
    if not CSVHandler.read_user_cart():
        return False
    return True

# define our clear function
def clear():
    # for windows
    if name == 'nt':
        os.system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        os.system('clear')




# -------------------------------------------------------------------------------------------------------------------------------------- #
# -----ENTRY POINT---------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------------------------- #

def main():
    try:
        CSVInitializer.initialize_csv_files()
        clear()
        homepage()

    except EOFError:
        print("")
        print("")
        exit_application()


if __name__ == "__main__":
    main()
