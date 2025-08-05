from flask import Flask
from threading import Thread
import time

app = Flask('')

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Оданн Telegram Bot</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    background: linear-gradient(135deg, #ffeaa7, #fab1a0);
                    margin: 0;
                    padding: 50px;
                }
                .container {
                    background: white;
                    border-radius: 15px;
                    padding: 40px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    max-width: 600px;
                    margin: 0 auto;
                }
                h1 { color: #e17055; }
                .status { 
                    color: #00b894; 
                    font-weight: bold; 
                    font-size: 18px;
                }
                .emoji { font-size: 24px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="emoji">🌸</div>
                <h1>Telegram Бот Оданн</h1>
                <p>Бот успешно запущен и работает!</p>
                <div class="status">🟢 ONLINE</div>
                <br>
                <p>Найдите бота в Telegram и начните общение!</p>
                <p><em>Powered by AI • Based on "Kakuriyo no Yadomeshi"</em></p>
            </div>
        </body>
    </html>
    """

def run():
    """Запуск Flask сервера"""
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Поддержание работы через веб-сервер"""
    t = Thread(target=run)
    t.daemon = True
    t.start()

def ping_server():
    """Функция для периодического пинга сервера"""
    import requests
    import os
    
    while True:
        try:
            # Получаем URL Replit проекта
            repl_url = os.getenv('REPL_URL', 'http://localhost:8080')
            requests.get(repl_url, timeout=10)
            print("🌸 Ping sent to keep bot alive")
        except Exception as e:
            print(f"❌ Ping error: {e}")
        
        # Пинг каждые 5 минут
        time.sleep(300)