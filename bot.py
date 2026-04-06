import os
import re
import random
import logging
import time
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Получение токена из переменной окружения
VK_TOKEN = os.environ.get('VK_TOKEN')
if not VK_TOKEN:
    logging.error('Переменная окружения VK_TOKEN не установлена!')
    exit(1)

# Авторизация
vk_session = VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

def roll_dice(sides: int, modifier: int = 0) -> tuple:
    """Бросает куб с заданным числом граней, применяет модификатор.
    Возвращает (результат_броска, итоговая_сумма)"""
    result = random.randint(1, sides)
    total = result + modifier
    return result, total

def parse_command(text: str) -> tuple:
    """Разбирает команду вида /d4, /d20+2, /к, /к-1.
    Возвращает (число_граней, модификатор) или None, если команда не распознана."""
    text = text.strip().lower()
    # Поддерживаем латиницу d и кириллицу к
    match = re.match(r'^/([dк])(\d*)([+-]\d+)?$', text)
    if not match:
        return None
    cube_type, sides_str, mod_str = match.groups()
    
    # Если указано число граней, иначе по умолчанию 20 для /к и /d без цифры (но по заданию /d всегда с цифрой)
    if sides_str:
        sides = int(sides_str)
    else:
        # Для /к без цифры - d20, для /d без цифры не предусмотрено, но на всякий случай d20
        sides = 20
    
    # Проверка ограничения: грани не более 100
    if sides > 100:
        sides = 100  # принудительное ограничение
    
    modifier = int(mod_str) if mod_str else 0
    return sides, modifier

def attack_roll() -> str:
    """Бросок атаки d20: 1 - промах, 20 - крит, остальное - попадание."""
    roll = random.randint(1, 20)
    if roll == 1:
        return f"🎲 Результат атаки: **{roll}** — Промах!"
    elif roll == 20:
        return f"🎲 Результат атаки: **{roll}** — Критическое попадание!"
    else:
        return f"🎲 Результат атаки: **{roll}** — Попадание!"

def defense_roll() -> str:
    """Бросок защиты d20: 1 - провал, 20 - крит, остальное - успех."""
    roll = random.randint(1, 20)
    if roll == 1:
        return f"🛡️ Результат защиты: **{roll}** — Провал!"
    elif roll == 20:
        return f"🛡️ Результат защиты: **{roll}** — Критический успех!"
    else:
        return f"🛡️ Результат защиты: **{roll}** — Успех!"

def double_roll() -> str:
    """Куб удвоения d6: 1-5 - пусто, 6 - ×2."""
    roll = random.randint(1, 6)
    if roll == 6:
        return f"💥 Куб удвоения: **{roll}** — ×2"
    else:
        return f"💥 Куб удвоения: **{roll}** — пусто"

def handle_message(text: str, user_id: int):
    """Обрабатывает текстовое сообщение и отправляет ответ."""
    # Команда /attack
    if text == '/attack':
        answer = attack_roll()
        vk.messages.send(user_id=user_id, message=answer, random_id=0)
        return
    
    # Команда /defense
    if text == '/defense':
        answer = defense_roll()
        vk.messages.send(user_id=user_id, message=answer, random_id=0)
        return
    
    # Команда /double
    if text == '/double':
        answer = double_roll()
        vk.messages.send(user_id=user_id, message=answer, random_id=0)
        return
    
    # Команды кубов /d... или /к...
    parsed = parse_command(text)
    if parsed:
        sides, modifier = parsed
        roll_result, total = roll_dice(sides, modifier)
        if modifier == 0:
            answer = f"🎲 Бросок d{sides}: **{roll_result}**"
        else:
            sign = '+' if modifier > 0 else ''
            answer = f"🎲 Бросок d{sides}{sign}{modifier}: **{roll_result}** ({roll_result} {sign}{modifier} = **{total}**)"
        vk.messages.send(user_id=user_id, message=answer, random_id=0)
        return
    
    # Если команда не распознана – молчим или можно ответить подсказкой
    # (по желанию раскомментировать)
    # vk.messages.send(user_id=user_id, message="Неизвестная команда. Используйте /d4, /d20+2, /к, /attack, /defense, /double", random_id=0)

def main():
    logging.info("Бот запущен и слушает сообщения...")
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    msg_text = event.text.strip()
                    user_id = event.user_id
                    handle_message(msg_text, user_id)
        except Exception as e:
            logging.error(f"Ошибка в longpoll: {e}")
            time.sleep(5)  # пауза перед переподключением

if __name__ == '__main__':
    main()
