import json
import os
import hashlib
from functools import wraps
from flask import session, redirect, request

class AccountManager:
    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.users = self.load_users()
    
    def load_users(self):
        """Загружает пользователей из файла"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def save_users(self):
        """Сохраняет пользователей в файл"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=4)
    
    def hash_password(self, password):
        """Хэширует пароль с использованием salt"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + key.hex()
    
    def verify_password(self, stored_password, provided_password):
        """Проверяет пароль против хэша"""
        salt = bytes.fromhex(stored_password[:64])
        stored_key = stored_password[64:]
        key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return key.hex() == stored_key
    
    def register(self, username, password):
        """Регистрирует нового пользователя"""
        if username in self.users:
            return False, "Username already exists"
        
        self.users[username] = {
            'password': self.hash_password(password),
            'tasks': []
        }
        self.save_users()
        return True, "Registration successful"
    
    def login(self, username, password):
        """Аутентифицирует пользователя"""
        if username not in self.users:
            return False, "User not found"
        
        if not self.verify_password(self.users[username]['password'], password):
            return False, "Invalid password"
        
        return True, "Login successful"
    
    def get_user_tasks(self, username):
        """Возвращает задачи пользователя"""
        if username in self.users:
            return self.users[username].get('tasks', [])
        return []
    
    def add_user_task(self, username, task_data):
        """Добавляет задачу пользователю"""
        if username in self.users:
            if 'tasks' not in self.users[username]:
                self.users[username]['tasks'] = []
            self.users[username]['tasks'].append(task_data)
            self.save_users()
            return True
        return False
    
    def update_user_task(self, username, task_id, task_data):
        """Обновляет задачу пользователя"""
        if username in self.users and 'tasks' in self.users[username]:
            for i, task in enumerate(self.users[username]['tasks']):
                if task.get('id') == task_id:
                    self.users[username]['tasks'][i] = task_data
                    self.save_users()
                    return True
        return False
    
    def delete_user_task(self, username, task_id):
        """Удаляет задачу пользователя"""
        if username in self.users and 'tasks' in self.users[username]:
            self.users[username]['tasks'] = [
                task for task in self.users[username]['tasks'] 
                if task.get('id') != task_id
            ]
            self.save_users()
            return True
        return False

# Декоратор для проверки аутентификации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function