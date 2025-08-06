import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from typing import List, Dict, Optional, Any
from config import MODEL_NAME, MAX_LENGTH, TEMPERATURE, TOP_P, ODANNA_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class AIModel:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.is_loaded = False
        
    def load_model(self):
        """Загрузка модели (используется бесплатная версия через Hugging Face)"""
        try:
            logger.info("Загрузка модели...")
            
            # Используем более легкую модель для бесплатного использования
            model_name = "microsoft/DialoGPT-medium"  # Альтернатива для бесплатного использования
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Создание пайплайна для генерации текста
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=MAX_LENGTH,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            self.is_loaded = True
            logger.info("Модель загружена успешно")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            # Fallback на простую логику без нейросети
            self.is_loaded = False
    
    def analyze_message(self, text: str, user_gender: str = "unknown") -> Dict[str, Any]:
        """Анализ сообщения пользователя"""
        analysis = {
            "emotion": "neutral",
            "intent": "general",
            "urgency": "low",
            "tone": "neutral",
            "empathy_level": 50
        }
        
        # Простой анализ на основе ключевых слов
        text_lower = text.lower()
        
        # Анализ эмоций
        positive_words = ["спасибо", "хорошо", "отлично", "рад", "доволен", "люблю", "нравится"]
        negative_words = ["плохо", "ужасно", "ненавижу", "злой", "грустно", "разочарован", "бесит"]
        urgent_words = ["срочно", "помоги", "нужно", "важно", "критично", "проблема"]
        
        if any(word in text_lower for word in positive_words):
            analysis["emotion"] = "positive"
            analysis["empathy_level"] = 70
        elif any(word in text_lower for word in negative_words):
            analysis["emotion"] = "negative"
            analysis["empathy_level"] = 80
        elif any(word in text_lower for word in urgent_words):
            analysis["urgency"] = "high"
            analysis["empathy_level"] = 75
        
        # Анализ намерений
        if "забудь" in text_lower or "забыть" in text_lower:
            analysis["intent"] = "forget"
        elif "помоги" in text_lower or "помощь" in text_lower:
            analysis["intent"] = "help"
        elif "расскажи" in text_lower or "объясни" in text_lower:
            analysis["intent"] = "explain"
        
        # Анализ тона
        if any(word in text_lower for word in ["пожалуйста", "будьте добры", "извините"]):
            analysis["tone"] = "polite"
        elif any(word in text_lower for word in ["иди", "убирайся", "ненавижу"]):
            analysis["tone"] = "aggressive"
        
        # Учет пола пользователя для эмпатии
        if user_gender == "female":
            analysis["empathy_level"] = min(analysis["empathy_level"] + 10, 90)
        
        return analysis
    
    def generate_response(self, messages: List[Dict], user_gender: str = "unknown", empathy_level: int = 50) -> str:
        """Генерация ответа Оданны"""
        try:
            if not self.is_loaded:
                return self._generate_fallback_response(messages, user_gender, empathy_level)
            
            # Формирование контекста для модели
            context = self._build_context(messages, empathy_level)
            
            # Генерация ответа
            response = self.pipeline(context, max_length=len(context.split()) + 100)[0]['generated_text']
            
            # Извлечение только новой части ответа
            new_response = response[len(context):].strip()
            
            if not new_response:
                return self._generate_fallback_response(messages, user_gender, empathy_level)
            
            return new_response
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return self._generate_fallback_response(messages, user_gender, empathy_level)
    
    def _build_context(self, messages: List[Dict], empathy_level: int) -> str:
        """Построение контекста для модели"""
        # Системный промпт с учетом уровня эмпатии
        empathy_text = ""
        if empathy_level >= 70:
            empathy_text = " Проявляй высокую эмпатию и заботу."
        elif empathy_level >= 50:
            empathy_text = " Проявляй умеренную эмпатию."
        else:
            empathy_text = " Будь более сдержанным в проявлении эмоций."
        
        context = ODANNA_SYSTEM_PROMPT + empathy_text + "\n\n"
        
        # Добавление истории диалога
        for msg in messages[-10:]:  # Последние 10 сообщений
            if msg['is_from_user']:
                context += f"Пользователь: {msg['text']}\n"
            else:
                context += f"Оданна: {msg['text']}\n"
        
        context += "Оданна: "
        return context
    
    def _generate_fallback_response(self, messages: List[Dict], user_gender: str, empathy_level: int) -> str:
        """Fallback генерация ответа без нейросети"""
        if not messages:
            return "Добро пожаловать в Небесную Гостиницу. Чем могу быть полезен, уважаемый гость?"
        
        last_message = messages[-1]['text'].lower() if messages else ""
        
        # Анализ последнего сообщения
        analysis = self.analyze_message(last_message, user_gender)
        
        # Базовые ответы в стиле Оданны
        responses = {
            "greeting": [
                "Добро пожаловать в нашу гостиницу, уважаемый гость. Надеюсь, ваше пребывание будет приятным.",
                "Рад видеть вас в Небесной Гостинице. Как ваше самочувствие?",
                "Добро пожаловать. Надеюсь, наше гостеприимство вас не разочарует."
            ],
            "farewell": [
                "До свидания, уважаемый гость. Надеюсь, ваше пребывание было приятным.",
                "Благодарю за посещение нашей гостиницы. Возвращайтесь в любое время.",
                "До встречи. Пусть ваше путешествие будет безопасным."
            ],
            "thanks": [
                "Пожалуйста, уважаемый гость. Ваше удовлетворение — наша главная забота.",
                "Не стоит благодарности. Это моя обязанность как хозяина гостиницы.",
                "Рад быть полезным. Ваше благополучие — мой приоритет."
            ],
            "help": [
                "Конечно, уважаемый гость. Расскажите подробнее о вашей проблеме.",
                "Я здесь, чтобы помочь. Что именно вас беспокоит?",
                "Не беспокойтесь, я разберусь с этим. Расскажите детали."
            ],
            "complaint": [
                "Приношу извинения за неудобства. Я лично разберусь с этой ситуацией.",
                "Понимаю ваше недовольство. Позвольте исправить это немедленно.",
                "Сожалею о произошедшем. Это не соответствует стандартам нашей гостиницы."
            ],
            "question": [
                "Интересный вопрос, уважаемый гость. Позвольте объяснить...",
                "Хорошо, что вы спросили. Дело в том, что...",
                "Отличный вопрос. Позвольте прояснить ситуацию."
            ],
            "default": [
                "Понимаю, уважаемый гость. Продолжайте, я слушаю.",
                "Интересно, очень интересно. Расскажите подробнее.",
                "Хм, любопытно. Что вы имеете в виду?"
            ]
        }
        
        # Определение типа ответа
        response_type = "default"
        
        if any(word in last_message for word in ["привет", "здравствуй", "добрый"]):
            response_type = "greeting"
        elif any(word in last_message for word in ["пока", "до свидания", "прощай"]):
            response_type = "farewell"
        elif any(word in last_message for word in ["спасибо", "благодарю", "спасибо"]):
            response_type = "thanks"
        elif any(word in last_message for word in ["помоги", "помощь", "нужна помощь"]):
            response_type = "help"
        elif any(word in last_message for word in ["жалоба", "плохо", "ужасно", "недоволен"]):
            response_type = "complaint"
        elif "?" in last_message:
            response_type = "question"
        
        # Выбор ответа с учетом эмпатии
        import random
        base_responses = responses[response_type]
        
        # Модификация ответа в зависимости от уровня эмпатии
        if empathy_level >= 70:
            # Более теплый и заботливый тон
            if user_gender == "female":
                base_responses = [
                    "Дорогая гостья, позвольте мне позаботиться о вашем комфорте.",
                    "Не беспокойтесь, милая. Я сделаю все возможное для вашего удобства.",
                    "Уважаемая гостья, ваше благополучие — моя главная забота."
                ]
        elif empathy_level <= 30:
            # Более формальный и сдержанный тон
            base_responses = [
                "Понимаю, уважаемый гость. Что именно вас интересует?",
                "Хорошо. Продолжайте, я слушаю.",
                "Понятно. Есть ли еще вопросы?"
            ]
        
        response = random.choice(base_responses)
        
        # Добавление японских элементов
        if random.random() < 0.3:
            response += " どうぞよろしくお願いします。"  # Пожалуйста, будьте добры
        
        return response
    
    def summarize_chat(self, messages: List[Dict]) -> str:
        """Суммаризация чата"""
        if not messages:
            return "Пустой чат"
        
        # Простая суммаризация на основе ключевых слов
        user_messages = [msg['text'] for msg in messages if msg['is_from_user']]
        
        if not user_messages:
            return "Чат только с ответами бота"
        
        # Анализ основных тем
        all_text = ' '.join(user_messages).lower()
        
        # Подсчет частоты слов
        words = all_text.split()
        word_freq = {}
        stop_words = {'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о', 'об', 'а', 'но', 'или', 'что', 'как', 'где', 'когда', 'почему', 'зачем', 'это', 'то', 'так', 'вот', 'там', 'здесь', 'тут', 'там', 'где', 'куда', 'откуда'}
        
        for word in words:
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Топ-3 самых частых слов
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        
        summary = f"Чат с {len(messages)} сообщениями"
        if top_words:
            summary += f". Основные темы: {', '.join([word for word, _ in top_words])}"
        
        return summary