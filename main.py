from collections import UserDict
from datetime import datetime
from itertools import islice
import re
import json

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, number):
        if not self.validate_number(number):
            raise ValueError(f"Неправильний номер телефону: {number}")
        super().__init__(number)

    @staticmethod
    def validate_number(number):
        if isinstance(number, Phone):
            number = number.value 
        return re.fullmatch(r'\+?\d{10,15}', number) is not None
    
    def to_dict(self):
        return {"value": self.value}

    @classmethod
    def from_dict(cls, data):
        return cls(data['value'])

class Birthday:
    def __init__(self, birthday):
        self._birthday = None
        self.birthday = birthday

    @property
    def birthday(self):
        return self._birthday

    @birthday.setter
    def birthday(self, value):
        if not value:
            self._birthday = None
        else:
            try:
                birthday = datetime.strptime(value, '%Y-%m-%d').date()
                self._birthday = birthday
            except ValueError:
                raise ValueError("Неправильний формат дати, використовуйте YYYY-MM-DD")

    def __str__(self):
        return str(self._birthday) if self._birthday else ''
    
    def to_dict(self):
        return self._birthday.strftime('%Y-%m-%d') if self._birthday else None

    @classmethod
    def from_dict(cls, birthday_str):
        return cls(birthday_str) if birthday_str else None

class Record:
    def __init__(self, name, phones=[], birthday=None):
        self.name = Name(name)
        self.phones = [Phone(phone) for phone in phones]
        self.birthday = Birthday(birthday) if birthday else None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, number):
        for phone in self.phones:
            if phone.value == number:
                self.phones.remove(phone)
                return f"Номер телефону {number} видалено з контакту {self.name}"
        raise ValueError(f"Номер телефону {number} не знайдено у запису {self.name}")

    def edit_phone(self, old_number, new_number):
        found_phone = self.find_phone(old_number)
        if found_phone:
            found_phone.value = new_number
            return f"Змінено номер телефону для {self.name} з {old_number} на {new_number}"
        else:
            raise ValueError(f"Номер телефону {old_number} не знайдено у запису {self.name}")
    
    def find_phone(self, number):
        for phone in self.phones:
            if phone.value == number:
                return phone
        raise ValueError(f"Номер телефону {number} не знайдено у запису {self.name}")

    def days_to_birthday(self):
        if not self.birthday:
            return "Дата народження не встановлена"
        now = datetime.now()
        next_birthday = datetime(now.year, self.birthday.birthday.month, self.birthday.birthday.day)
        if next_birthday < now:
            next_birthday = datetime(now.year+1, self.birthday.birthday.month, self.birthday.birthday.day)
        return (next_birthday - now).days
    
    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones_str = "; ".join(str(phone) for phone in self.phones)
        return f"Ім'я контакту: {self.name}, телефони: {phones_str}, Днів до ДН: {self.days_to_birthday()}"
    def to_dict(self):
        return {
            "name": str(self.name),
            "phones": [phone.to_dict() for phone in self.phones],
            "birthday": self.birthday.to_dict() if self.birthday else None
        }
    @classmethod
    def from_dict(cls, data):
        name = data['name']
        phones = [Phone(phone_data['value']) for phone_data in data['phones']]
        birthday = Birthday.from_dict(data['birthday']) if data['birthday'] else None
        return cls(name, phones, birthday)

class AddressBook(UserDict):
    def iterator(self, n=2):
        it = iter(self.data.values())
        while True:
            records_slice = list(islice(it, n))
            if not records_slice:
                break
            yield records_slice

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
            return f"Контакт {name} видалено"
        raise ValueError(f"Контакт {name} не знайдено")   
    
    def save_to_file(self, filename):
        with open(filename, 'w') as file:
            json_data = {name: record.to_dict() for name, record in self.data.items()}
            json.dump(json_data, file, default=str, indent=4)
            
    def load_from_file(self, filename):
        with open(filename, 'r') as file:
            json_data = json.load(file)
            self.data.clear()  # очистити поточні дані перед завантаженням нових
            for name, record_data in json_data.items():
                record = Record.from_dict(record_data)
                self.add_record(record)
    
def input_error(handler):
    def wrapped(*args):
        try:
            return handler(*args)
        except KeyError as e:
            return f"Error: {e} not found."
        except ValueError as e:
            return f"Error: {e}"
        except IndexError as e:
            return f"Error: {e}"
    return wrapped

def hello(*args):
    return "How can I help you?"

def add_contact(name, phone):
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
    record.add_phone(phone)
    return f"Додано номер телефону {phone} до контакту {name}"

def add_birthday(name, birthday):
    record = book.find(name)
    if not record:
        raise ValueError("Контакт не знайдено")

    record.add_birthday(birthday)
    return f"Додано день народження {birthday} до контакту {name}"

def change_phone(name, old_number, new_number):
    record = book.find(name)
    if not record:
        raise KeyError(name)
    return record.edit_phone(old_number, new_number)

def show_phone(name):
    record = book.find(name)
    if not record:
        raise KeyError(name)
    phones_str = "; ".join(str(phone) for phone in record.phones)
    return f"{name}: {phones_str}"

def show_all(*args):
    result = ''
    for name, record in book.items():
        result += f"{name}: {record}\n"
    return result.strip()

def delete_contact(name):
    return book.delete(name)

handlers = {
    "hello": hello,
    "add": add_contact,
    "change": change_phone,
    "phone": show_phone,
    "show all": show_all,
    "delete": delete_contact,
    "add birthday": add_birthday,
}

def main():
    while True:
        user_input = input("Введіть команду: ").strip().lower()
        command_parts = user_input.split()

        if len(command_parts) > 1 and ' '.join(command_parts[:2]) in handlers:
            command_name = ' '.join(command_parts[:2])
            data = command_parts[2:]
        else:
            command_name = command_parts[0]
            data = command_parts[1:]

        if command_name in ["good bye", "close", "exit"]:
            print("До побачення!")
            break

        handler = handlers.get(command_name)

        if not handler:
            print(f"Невідома команда! Доступні команди: {', '.join(handlers.keys())}.")
            continue

        try:
            result = handler(*data)
            print(result)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    book = AddressBook()
    try:
        book.load_from_file('address_book.json')
    except (FileNotFoundError, json.JSONDecodeError):
        print("Файл address_book.json не знайдено або пошкоджений. Буде створено нову адресну книгу.") 

    try:
        main()
    finally:
        book.save_to_file('address_book.json')