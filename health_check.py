#!/usr/bin/env python3
"""
Простой веб-сервер для проверки здоровья приложения
Используется для деплоя на платформах с HTTP проверками
"""

import os
import sys
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Добавление текущей директории в путь
sys.path.insert(0, str(Path(__file__).parent))

try:
    from database import Database
    from ai_model import AIModel
except ImportError as e:
    print(f"Ошибка импорта модулей: {e}")
    sys.exit(1)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов для проверки здоровья"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/health':
            self.send_health_response()
        else:
            self.send_error(404, "Not Found")
    
    def send_health_response(self):
        """Отправка ответа о состоянии здоровья"""
        try:
            # Проверка базы данных
            db = Database()
            
            # Проверка AI модели
            ai_model = AIModel()
            
            # Проверка переменных окружения
            bot_token = os.getenv("BOT_TOKEN")
            admin_id = os.getenv("ADMIN_ID")
            
            # Формирование ответа
            status = "healthy"
            checks = {
                "database": "ok",
                "ai_model": "ok",
                "environment": "ok" if bot_token and bot_token != "YOUR_BOT_TOKEN_HERE" else "warning"
            }
            
            response = {
                "status": status,
                "checks": checks,
                "message": "Бот Оданна работает нормально"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            import json
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            # Ошибка при проверке здоровья
            response = {
                "status": "unhealthy",
                "error": str(e),
                "message": "Ошибка проверки здоровья"
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            import json
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Отключение логирования запросов"""
        pass

def run_health_server(port=8080):
    """Запуск сервера проверки здоровья"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    
    print(f"Сервер проверки здоровья запущен на порту {port}")
    print(f"Проверка здоровья: http://localhost:{port}/health")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
        httpd.server_close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Сервер проверки здоровья для бота Оданна")
    parser.add_argument("--port", type=int, default=8080, help="Порт для сервера (по умолчанию: 8080)")
    
    args = parser.parse_args()
    run_health_server(args.port)