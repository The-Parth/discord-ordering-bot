import json
import requests
import os


def path_finder(path):
    if os.name == "nt":
        return path.replace("/", "\\")
    else:
        return path.replace("\\", "/")


filepath = os.path.dirname(os.path.abspath(
    __file__)) + "/src/data/menus/newmenu.json"

filepath = path_finder(filepath)

if not os.path.exists(filepath):
    with open(filepath, "w") as f:
        json.dump([], f, indent=4)


def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


def valid_image(image_url: str) -> bool:
    """Checks if the URL is a valid image."""
    image_formats = (
        "image/png", "image/jpeg", "image/jpg", "image/gif", "image/bmp", "image/webp"
    )
    try:
        req = requests.head(image_url)
        if req.headers["content-type"] in image_formats:
            return True
    except:
        pass
    return False


def menu_loader() -> list:
    """Loads the menu from the JSON file."""
    with open(filepath, "r") as f:
        menu = json.load(f)
    return menu


def menu_saver(menu: list):
    """Saves the menu to the JSON file."""
    with open(filepath, "w") as f:
        json.dump(menu, f, indent=4)


def item_in_menu(item: str):
    """Checks if the item is in the menu."""
    menu = menu_loader()
    for options in menu:
        if options["ITEM"].lower() == item.lower():
            return options
    if item.isdigit():
        if int(item) <= len(menu):
            return menu[int(item)-1]

    return False


def add_item():
    menu = menu_loader()
    clear_screen()
    print("ADD WIZARD")
    item = input(
        "Enter the item name you want to add (your case will be saved, type 'cancel' to exit): ")
    if item.lower() == "cancel":
        print("Cancelled!")
        return
    if item_in_menu(item):
        print("Item already exists!")
    else:
        while True:
            description = input(
                "Enter the item description (your case will be saved): ")
            if description == "":
                print("Description cannot be empty!")
                continue
            break
        while True:
            price = input("Enter the item price (Numbers only!): ")
            if price == "":
                print("Price cannot be empty!")
                continue
            try:
                float(price)
            except ValueError:
                print("Price must be a number!")
                continue
            price = str(round(float(price), 2))
            if float(price) < 0:
                print("Price cannot be negative!")
                continue
            break
        while True:
            prep = input(
                "Enter the item preparation time (your case will be saved): ")
            if prep == "" or not prep.isdecimal():
                print("Preparation time must be a number! (integer only)")
                continue
            if int(prep) <= 0:
                print("Preparation time cannot be zero or negative!")
                continue
            prep = " "+prep+" minutes"
            break
        image = input(
            "[Optional] Enter the item image URL (your case will be saved): ")
        while True:
            confirm = input("Are you sure you want to add this item? (Y/N): ")
            if confirm.lower() == "y":
                break
            elif confirm.lower() == "n":
                print("Cancelled!")
                return
            else:
                print("Invalid input!")
                continue
        if valid_image(image):
            menu.append({"ITEM": item, "COST": str(price).strip(),
                        "DESC": description, "TIME": prep, "IMAG": image})
        else:
            image = None
            menu.append({"ITEM": item, "COST": str(price).strip(),
                        "DESC": description, "TIME": prep})
        clear_screen()
        print(f"Item added!"
              f"\nItem: {item}"
              f"\nDescription: {description}"
              f"\nPrice: {price}"
              f"\nPreparation time: {prep}"
              f"\nImage: {image if not None else 'No valid image'}")
        menu_saver(menu)
    while True:
        choice = input("Do you want to add another item? (Y/N): ")
        if choice.lower() == "y":
            add_item()
        break
    clear_screen()


def remove_item():
    menu = menu_loader()
    clear_screen()
    print("REMOVAL WIZARD")
    item = input(
        "Enter the item name you want to remove(type 'cancel' to exit): ")
    if item.lower() == "cancel":
        print("Cancelled!")
        return
    item_obj = item_in_menu(item)
    if not item_obj:
        print("Item not found!")
    else:
        while True:
            confirm = input(
                "Are you sure you want to delete this item? (Y/N): ")
            if confirm.lower() == "y":
                break
            elif confirm.lower() == "n":
                print("Cancelled!")
                return
            else:
                print("Invalid input!")
                continue
        menu.remove(item_obj)
        menu_saver(menu)
        print("Item removed!")
        print(f"Item: {item_obj['ITEM']}"
                f"\nPrice: {item_obj['COST']}"
        )
    while True:
        choice = input("Do you want to delete another item? (Y/N): ")
        if choice.lower() == "y":
            remove_item()
        break
    clear_screen()


def backup():
    """Makes a backup of the menu."""
    import datetime
    menu = menu_loader()
    path = os.path.dirname(os.path.abspath(__file__)) + "/backups/menus/"
    backup_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_")+"menu.json"
    path += backup_name
    path = path_finder(path)
    print("Creating backup...")
    with open(path,"w") as f:
        json.dump(menu, f, indent=4)
    print("Backup created! Name: "+backup_name)
    input("Press enter to continue...")
    clear_screen()


def show_items():
    clear_screen()
    menu = menu_loader()
    print("MENU")
    l = len(menu)
    for i in range(l):
        print(f"{i+1}. {menu[i]['ITEM']} - Rs.{menu[i]['COST']}")
    print(f"Total items: {l}")
    print("Press enter to continue...")
    input()
    clear_screen()


def edit_item():
    menu = menu_loader()
    clear_screen()
    print("EDIT WIZARD")
    item = input(
        "Enter the item name or index you want to edit(type 'cancel' to exit): ")
    if item.lower() == "cancel":
        print("Cancelled!")
        return
    item_obj = item_in_menu(item)
    if not item_obj:
        print("Item not found!")
    else:
        new_item = {}
        while True:
            new_item["ITEM"] = input(
                "Enter the new item name (your case will be saved): ")
            if new_item["ITEM"].strip() == "":
                print("Empty name. Using old name.")
                new_item["ITEM"] = item_obj["ITEM"]
                break
            if item_in_menu(new_item["ITEM"]):
                print("Item already exists!")
                continue
            break
        while True:
            new_item["COST"] = input(
                "Enter the new item price (Numbers only!): ")
            if new_item["COST"].strip() == "":
                print("Empty price. Using old price.")
                new_item["COST"] = item_obj["COST"]
                break
            try:
                float(new_item["COST"])
            except ValueError:
                print("Price must be a number!")
                continue
            new_item["COST"] = str(round(float(new_item["COST"]), 2))
            if float(new_item["COST"]) < 0:
                print("Price cannot be negative!")
                continue
            new_item["COST"] = str(new_item["COST"]).strip()
            break
        while True:
            new_item["DESC"] = input(
                "Enter the new item description (your case will be saved): ")
            if new_item["DESC"].strip() == "":
                print("Empty description. Using old description.")
                new_item["DESC"] = item_obj["DESC"]
                break
            break
        while True:
            new_item["TIME"] = input(
                "Enter the new item preparation time (your case will be saved): ")
            if new_item["TIME"].strip() == "":
                print("Empty preparation time. Using old preparation time.")
                new_item["TIME"] = item_obj["TIME"]
                break
            if not new_item["TIME"].isdecimal():
                print("Preparation time must be a number! (integer only)")
                continue
            if int(new_item["TIME"]) <= 0:
                print("Preparation time cannot be zero or negative!")
                continue
            new_item["TIME"] = " "+new_item["TIME"]+" minutes"
            break
        while True:
            new_item["IMAG"] = input(
                "[Optional] Enter the new item image URL (type 'delete' to delete the image): ")
            if new_item["IMAG"].strip() == "":
                print("Empty image URL. Using old image URL. (if any)")
                if "IMAG" in item_obj:
                    new_item["IMAG"] = item_obj["IMAG"]
                else:
                    del new_item["IMAG"]
                break
            if valid_image(new_item["IMAG"]):
                break
            elif new_item["IMAG"].lower() == "DELETE".lower():
                print("Image deleted!")
                del new_item["IMAG"]
                break
            else:
                print("Invalid image URL, ignoring...")
                del new_item["IMAG"]
                if "IMAG" in item_obj:
                    new_item["IMAG"] = item_obj["IMAG"]
                break
        menu[menu.index(item_obj)] = new_item
        while True:
            confirm = input("Are you sure you want to edit this item? (Y/N): ")
            if confirm.lower() == "y":
                break
            elif confirm.lower() == "n":
                print("Cancelled!")
                return
            else:
                print("Invalid input!")
                continue
        menu_saver(menu)
        print("Item edited! Name: "+item_obj["ITEM"])
    while True:
        choice = input("Do you want to edit another item? (Y/N): ")
        if choice.lower() == "y":
            edit_item()
        break
    clear_screen()


def change_position():
    menu = menu_loader()
    clear_screen()
    print("POSITION CHANGE WIZARD")
    show_items()
    item = input(
        "Enter the item name or index you want to change position (type 'cancel' to exit): ")
    if item.lower() == "cancel":
        print("Cancelled!")
        return
    item_obj = item_in_menu(item)
    if not item_obj:
        print("Item not found!")
        return
    else:
        new_pos = ""
        while True:
            new_pos = input("Enter the new position (integer only): ")
            if new_pos.strip() == "":
                print("Empty position. Using old position.")
                return
            if not new_pos.isdecimal():
                print("Position must be a number (integer only)!")
                continue
            if int(new_pos) <= 0:
                print("Position cannot be zero or negative!")
                continue
            if int(new_pos) > len(menu):
                print("Position cannot be greater than total items.")
                continue
            break
        menu.remove(item_obj)
        menu.insert(int(new_pos)-1, item_obj)
        while True:
            confirm = input("Are you sure you want to edit this item? (Y/N): ")
            if confirm.lower() == "y":
                break
            elif confirm.lower() == "n":
                print("Cancelled!")
                return
            else:
                print("Invalid input!")
                continue
        menu_saver(menu)
        print("Position changed! Name: " +
              item_obj["ITEM"], "New position: "+new_pos)
        print("Show new menu? (y/n)", end=" ")
        if input().lower() == "y":
            show_items()
    while True:
        choice = input("Do you want to edit another item? (Y/N): ")
        if choice.lower() == "y":
            change_position()
        break
    clear_screen()


def switch_good():
    """Case like menu system"""
    print("Menu Editor for Discord-Ordering-Bot by The-Parth")
    print("If you want to reset the menu, type 'reset_menu'")
    input("Press enter to continue...")
    while True:
        print("1. Add item")
        print("2. Delete item")
        print("3. Edit item")
        print("4. Change position")
        print("5. Show menu")
        print("6. Exit")
        choice = input("Enter your choice: ")
        if choice == "1" or choice == "add":
            add_item()
        elif choice == "2" or choice == "delete":
            remove_item()
        elif choice == "3" or choice == "edit":
            edit_item()
        elif choice == "4" or choice == "change":
            change_position()
        elif choice == "5" or choice == "show":
            show_items()
        elif choice == "6" or choice == "exit":
            print("Exiting menu editor...")
            print("Goodbye!")
            break
        elif choice == "reset_menu":
            check = input("Are you sure you want to reset the menu? (Y/N): ")
            if check.lower() == "n":
                print("Cancelled!")
                continue
            check = input("Are you really sure? Type 'reset' to reset: ")
            if check.lower() != "reset":
                print("Cancelled!")
                continue
            print("Resetting menu...")
            backup()
            menu_saver([])
            print("Menu reset!")
            
        else:
            print("Invalid input!")


if __name__ == "__main__":
    clear_screen()
    switch_good()
    input("Press enter to exit...")
