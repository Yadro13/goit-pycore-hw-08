from pathlib import Path
import json
import pickle
from colorama import Fore, Style, init
from collections import UserDict
from datetime import datetime as dtdt, timedelta
import re

init(autoreset=True)

# Helper function for colored messages
def dir_file_color(lvl: str, message: str) -> str:
    COLORS = {
        'CHANGE': Fore.BLUE,
        'ADD': Fore.GREEN,
        'DELETE': Fore.RED,
        'WARN': Fore.YELLOW
    }
    if lvl in COLORS:
        return f"{COLORS[lvl]}{message}{Style.RESET_ALL}"
    else:
        return f"{Fore.WHITE}{message}{Style.RESET_ALL}"

# JSON persistence functions
# PHONEBOOK_FILE = "contacts.json"

# Pickle filename setup
PHONEBOOK_FILE = "addressbook.pkl"

# Help text and function
HELP_TEXT = (
    f"{Fore.GREEN}Available commands:\n"
    f"{Fore.WHITE}hello {Fore.GREEN}- Greets you\n"
    f"{Fore.WHITE}add {Fore.YELLOW}[name] {Fore.CYAN}[phone] {Fore.GREEN}- Add a new contact or update phone for an existing contact\n"
    f"{Fore.WHITE}change {Fore.YELLOW}[name] {Fore.CYAN}[old phone] {Fore.CYAN}[new phone] {Fore.GREEN}- Change phone number for a contact\n"
    f"{Fore.WHITE}phone {Fore.YELLOW}[name] {Fore.GREEN}- Show phone numbers for a contact\n"
    f"{Fore.WHITE}all {Fore.GREEN}- Show all contacts\n"
    f"{Fore.WHITE}delete {Fore.YELLOW}[name] {Fore.GREEN}- Delete a contact\n"
    f"{Fore.WHITE}add-birthday {Fore.YELLOW}[name] {Fore.MAGENTA}[DD.MM.YYYY] {Fore.GREEN}- Add or update birthday for a contact\n"
    f"{Fore.WHITE}show-birthday {Fore.YELLOW}[name] {Fore.GREEN}- Show birthday for a contact\n"
    f"{Fore.WHITE}birthdays {Fore.GREEN}- Show upcoming birthdays in the next week and congrats help\n"
    f"{Fore.WHITE}help {Fore.GREEN}- Show this help message\n"
    f"{Fore.WHITE}close {Fore.GREEN}or {Fore.WHITE}exit {Fore.GREEN}- Exit the program{Style.RESET_ALL}"
)

def show_help():
    print(HELP_TEXT)

# Decorator for error handling
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as ve:
            return dir_file_color("WARN", f"Value Error: {ve}, please use 'help' command for more details")
        except KeyError as ke:
            return dir_file_color("WARN", f"Key Error: {ke}")
        except IndexError as ie:
            return dir_file_color("WARN", f"Index Error: {ie}")
    return inner

# Base Field class 
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self): 
        return str(self.value)

# Name class with validation
class Name(Field):
    def __init__(self, value):
        self.validate(value)
        super().__init__(value)

    def validate(self, value):
        if not value or not value.isalpha():
            raise ValueError("Name must contain only letters.")
        return value.capitalize()
    
# Phone class with validation
class Phone(Field):
    def __init__(self, value):
        self.validate(value)
        super().__init__(value)

    def validate(self, value):
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Phone number must be exactly 10 digits.")

# Birthday class with validation
class Birthday(Field):
    def __init__(self, value):
        try:
            if re.fullmatch(r"^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.\d{4}$", value):
                self.value = dtdt.strptime(value, "%d.%m.%Y")
            else:
                raise ValueError("Invalid date format. Use DD.MM.YYYY")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

# Record class for each contact
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def delete_phone(self, phone) -> bool:
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return True
        return False

    def edit_phone(self, old_phone, new_phone) -> bool:
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return True
        return False

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones) if self.phones else "No phones"
        birthday_str = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "No birthday"
        return f"Name: {self.name.value}, Phones: {phones_str}, Birthday: {birthday_str}"

# AddressBook class to manage contacts
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self) -> list:
        upcoming = []
        today = dtdt.today().date()
        
        for record in self.data.values():
            if record.birthday is None:
                continue

            bday = record.birthday.value.date()
            upcoming_bday = bday.replace(year=today.year)
            if upcoming_bday < today:
                upcoming_bday = bday.replace(year=today.year + 1)
            diff = (upcoming_bday - today).days

            if 0 <= diff < 7:
                if upcoming_bday.weekday() == 5:  # Saturday
                    upcoming_bday += timedelta(days=2)
                elif upcoming_bday.weekday() == 6:  # Sunday
                    upcoming_bday += timedelta(days=1)

                 # Check if there is at least one phone; if not, use a default message.
                phone = record.phones[0].value if record.phones else " No phone " 

                upcoming.append({
                    "name": record.name.value,
                    "congratulation_date": upcoming_bday.strftime("%d.%m.%Y"),
                    "phone": phone
                })
        return upcoming

# JSON save function
def save_address_book(book: AddressBook, filename=PHONEBOOK_FILE):
    data_to_save = {}
    for name, record in book.data.items():
        data_to_save[name] = {
            "phones": [p.value for p in record.phones],
            "birthday": record.birthday.value.strftime("%d.%m.%Y") if record.birthday else None
        }
    with open(filename, "w") as f:
        json.dump(data_to_save, f, indent=4)

# JSON load function
def load_address_book(filename=PHONEBOOK_FILE) -> AddressBook:
    book = AddressBook()
    path = Path(filename)
    if path.exists():
        with open(filename, "r") as f:
            data_loaded = json.load(f)
            for name, info in data_loaded.items():
                record = Record(name)
                for phone in info.get("phones", []):
                    record.add_phone(phone)
                birthday = info.get("birthday")
                if birthday:
                    record.add_birthday(birthday)
                book.add_record(record)
    return book

# Pickle save function
def save_data(book, filename=PHONEBOOK_FILE):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

# Pickle load function
def load_data(filename=PHONEBOOK_FILE):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

# Command handler functions
@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return dir_file_color("ADD", message)

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    if record.edit_phone(old_phone, new_phone):
        return dir_file_color("CHANGE", "Contact updated.")
    else:
        return dir_file_color("WARN", "Old phone number not found.")

@input_error    
def show_contact(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    phones = '; '.join(p.value for p in record.phones) if record.phones else "No phones"
    return f"{record.name.value}: {phones}"

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
    record.add_birthday(birthday)
    return dir_file_color("ADD", f"Birthday for {name} added/updated.")

@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    if record.birthday is None:
        return f"Birthday for {name} is not set."
    birthday_str = record.birthday.value.strftime("%d.%m.%Y")
    return f"{name}'s birthday is on {birthday_str}."

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()

    if not upcoming:
        return "No upcoming birthdays in the next week."
    result_lines = [f" To congrat {Fore.YELLOW}{entry['name']:<15}" \
                    f"{Fore.WHITE} -> call by: {Fore.CYAN}{entry['phone']}" \
                    f"{Fore.WHITE} -> on: {Fore.MAGENTA}{entry['congratulation_date']}"\
                    f"{Style.RESET_ALL}" for entry in upcoming]
    return "\n".join(result_lines)

@input_error
def delete_contact(args, book: AddressBook):
    name, *_ = args
    if book.find(name) is None:
        raise KeyError("Contact not found.")
    book.delete(name)
    return dir_file_color("DELETE", f"Contact {name} deleted.")

def print_contacts(book: AddressBook):
    if not book.data:
        print("No contacts in the address book.")
    else:
        # Print header
        header = f"{'Name':<15} {'Birthday':<15} {'Phones'}"
        print(header)
        print("-" * (len(header) + 4))
        
        for record in book.data.values():
            name = record.name.value
            birthday = record.birthday.value.strftime("%d.%m.%Y") if record.birthday else "No birthday"
            phones = '; '.join(phone.value for phone in record.phones) if record.phones else "No phones"
            print(f"{Fore.YELLOW}{name:<15}{Style.RESET_ALL} "
                  f"{Fore.MAGENTA}{birthday:<15}{Style.RESET_ALL} "
                  f"{Fore.CYAN}{phones}{Style.RESET_ALL}")
            
def parse_input(user_input):
    parts = user_input.split()
    command = parts[0].lower()
    return command, *parts[1:]

# Main program loop
def main():
    
    # JSON book load
    # book = load_address_book()

    # Pickle book load
    book = load_data()

    print(dir_file_color("ADD", "Welcome to the assistant bot!"))
    print(dir_file_color("CHANGE", "Type 'help' to see available commands."))
    
    print()
    print("Your phonebook, sir (or ma'am) ;)")
    print_contacts(book)
    
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit", "quit"]:
            
            # JSON book save
            # save_address_book(book)

            # Pickle book save
            save_data(book)
            
            print(dir_file_color("DELETE", "Phonebook is saved. Good bye!"))
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "help":
            show_help()

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_contact(args, book))

        elif command == "all":
            print_contacts(book)

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        elif command == "delete":
            print(delete_contact(args, book))

        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
