# CLI - E-Commerce Application

#### Video Demo: <https://youtu.be/Ah95YkCIqCg>

#### Description:
Welcome to my final project for CS50P: Introduction to Programming with Python. This is a fully CLI-based E-commerce application that operates in two modes:
- **User Mode**: Run with `python filename.py`
- **Admin Mode**: Run with `python filename.py --admin`

### User Mode:
- Users can sign up by providing their name, email, and password. This information is stored in a CSV file, which is created during the first execution.
- After signing up, users can:
  - View products fetched from `stock.csv`, organized into tables by category.
  - Add items to the cart by specifying the product name (case-sensitive), category (not case-sensitive), and quantity.
  - Manage their cart by removing items, updating quantities, or clearing the cart entirely.
  - Proceed to checkout, which simulates order placement and clears the cart.
- All CRUD operations (Create, Read, Update, Delete) handle inventory management, ensuring no stock discrepancies.

### Admin Mode:
- Admins must first sign up, using an **admin key** to complete registration. The default key is: **Admin123_$**.
- After signing up, admins can:
  - Login and change the admin key (ensure to keep the new key secure).
  - Manage the inventory with full CRUD functionality.
  - View logs (to be scaled in the future).
- All admin credentials are securely stored in `admin.csv`, with passwords and keys hashed using bcrypt.

### Design Elements:
- The application features multiple pages and a router for seamless navigation between them.
- Classes were used to manage logic for user authentication, cart operations, and inventory management.
- CSV file handling is managed by a dedicated `CSVHandler` class for reading and writing.
- For better navigation in a CLI environment, a dictionary was implemented to map actions to corresponding functions, enabling back-and-forth movement within the application.
- The `pandas` library was used to manage cart and inventory data for efficient file I/O and data manipulation.
- The `tabulate` library displays data in tables, improving readability.
- To enhance the user experience, `os.system('clear')` was used to clear the terminal, and `time.sleep()` to simulate loading times. The `rich` library was used to style the terminal output.

### Files Included:
- `key.txt`: Admin key storage.
- `stock.csv`: Inventory data with 50 products in three categories.

### Features:
- **User/Admin Modes**: Operate in user or admin mode with the `--admin` flag.
- **File I/O**: Separate CSVs for credentials, inventory, and cart management.
- **Stock Management**: Cart operations automatically update inventory.
- **View Inventory**: Users can browse available products and their details.
- **Manage Cart**: Users can add, remove, and update items in their cart.
- **Checkout**: Users can place orders, which clears their cart afterward.
- **User Authentication**: Secure user accounts with password hashing.

### Installation:
To install the required dependencies, run:
```bash
pip install -r requirements.txt
```

