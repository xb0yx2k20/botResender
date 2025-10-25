#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from telethon import TelegramClient, events

API_ID = 25635259
API_HASH = "67bec902e3505eb233a268dde834d554"

# Конфигурация пересылки: {исходный_чат: [список_целевых_чатов]}
FORWARD_CONFIG = {
    # Чат менеджеров WB ПВЗ -> Группа "Никита" (с фильтром по ключевым словам)
    -1001191038500: {
        'targets': [
            # Тесты Бота
            -4930610312,
            
            # # Никита
            # -1002205402814, 
            # -1002618488886, 
            # -1003149425740, 
            # -1002968528544, 
            # -1002597039230, 
            
            # # Елена
            # -1002324418495,
            # -1002415883693,
            # -1002473600494,
            # -1002493722860,
            # -1002266126897,
            
            # # Андрей
            # -1002294684549,
            # -1002324418495,
            # -1002282191777,
            # -1002300812487,
            # -1002350563218,
            # -1002497371035,
            
            # # Настя
            # -1002407856400,
            # -1002358346270,
            # -1002706496818,
            # -1002292190065,
            # -4890126309,
            # -1002477977258,

            # # Руководство
            # -1002809230924

            


        ],
        'filter_type': 'keyword',
        'keywords': ['Команда WB ПВЗ'],
        'description': 'Чат менеджеров WB ПВЗ -> Группа "Никита" (фильтр по ключевым словам)'
    },
    
    # Ozon -> Тесты Бота (пересылка всех сообщений)
    -1001748528023: {
        'targets': [
            -4930610312,

            # -1002516895147,
            # -1002672906777,
            # -4936691149,
            # -1003197373336,
            # -1002582421399,
            # -1002881100657,
            # -1003141777887,
            # -1002891646032,
            # -1002914741018,
            # -1002628279539,
            # -1002809230924,
            # -1002535518423,
            # -1002424637483,
            # -1003194219395,
            # -1002629256846,
            # -4861152542,
            # -1003060038107,
            # -1003086940888,
            # -1002724285922,
            # -1002610317569,
            # -1002968528544,
            # -4612394646,
            # -4701220110,
            # -1003073231886

            
            
            ],
        'filter_type': 'all',
        'description': 'Исходный чат -> Тесты Бота (все сообщения)'
    }
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Уменьшаем уровень логирования Telethon для скрытия служебных сообщений
logging.getLogger('telethon').setLevel(logging.WARNING)

# Создаем клиент с уникальным именем сессии
client = TelegramClient('unified_bot_session', API_ID, API_HASH)

async def forward_messages_with_keyword(source_chat_id, target_chat_ids, keywords, limit=2000):
    """Пересылает последние сообщения по ключевым словам (включая медиагруппы)"""
    try:
        print(f"🔍 Поиск сообщений с ключевыми словами в чате {source_chat_id}...")

        chat = await client.get_entity(source_chat_id)
        print(f"📡 Чат: {getattr(chat, 'title', 'Без названия')}")

        matching_messages = []

        # Обходим сообщения от новых к старым
        async for message in client.iter_messages(source_chat_id, limit=limit):
            if not message.message:
                continue

            text_lower = message.message.lower()
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matching_messages.append(message)
                    print(f"🎯 Найдено сообщение с '{keyword}': ID {message.id}")
                    break
            
            # Небольшая задержка для предотвращения flood wait (только каждые 10 сообщений)
            if len(matching_messages) % 10 == 0:
                await asyncio.sleep(0.05)

        if not matching_messages:
            print("❌ Сообщений с ключевыми словами не найдено.")
            return

        # Берём самое новое совпадение
        last_matching_message = matching_messages[0]
        print(f"📨 Последнее подходящее сообщение: ID {last_matching_message.id}")

        # Проверяем, медиагруппа ли это
        messages_to_forward = []

        if last_matching_message.grouped_id:
            gid = last_matching_message.grouped_id
            print(f"🖼 Это часть медиагруппы (grouped_id={gid}) — ищу все части...")

            # Собираем все сообщения с тем же grouped_id
            all_grouped_messages = []
            async for msg in client.iter_messages(source_chat_id, limit=limit):
                if msg.grouped_id == gid:
                    all_grouped_messages.append(msg)
                # Небольшая задержка для предотвращения flood wait (только каждые 5 сообщений)
                if len(all_grouped_messages) % 5 == 0:
                    await asyncio.sleep(0.03)

            # Сортируем по ID для правильного порядка (от старых к новым)
            all_grouped_messages.sort(key=lambda x: x.id)
            messages_to_forward = all_grouped_messages
            print(f"📸 Собрано частей медиагруппы: {len(messages_to_forward)}")
            
            # Логируем найденные сообщения
            for i, msg in enumerate(messages_to_forward):
                print(f"   {i+1}. ID {msg.id}, дата: {msg.date}")
        else:
            messages_to_forward = [last_matching_message]
            print("✉️ Это одиночное сообщение")

        # Пересылаем во все целевые чаты
        success_count = 0
        for target_chat_id in target_chat_ids:
            try:
                await client.forward_messages(target_chat_id, messages_to_forward)
                print(f"✅ Переслано {len(messages_to_forward)} сообщений в {target_chat_id}")
                success_count += 1
            except Exception as e:
                print(f"❌ Ошибка пересылки в {target_chat_id}: {e}")

        print(f"🎉 Пересылка завершена! Успешно переслано в {success_count} чатов.")

    except Exception as e:
        print(f"❌ Ошибка пересылки по ключевым словам: {e}")
async def forward_all_messages(source_chat_id, target_chat_ids, limit=50):
    """Пересылает последнее сообщение из чата"""
    try:
        print(f"🔍 Пересылаю последнее сообщение из чата {source_chat_id}...")
        
        # Получаем информацию о чате
        chat = await client.get_entity(source_chat_id)
        print(f"📡 Чат: {getattr(chat, 'title', 'Без названия')}")
        
        # Получаем только последнее сообщение
        last_message = None
        async for message in client.iter_messages(source_chat_id, limit=1):
            last_message = message
            break
        
        if not last_message:
            print("❌ Сообщений не найдено")
            return
        
        print(f"📨 Найдено последнее сообщение: ID {last_message.id}")
        
        # Получаем информацию об отправителе
        sender = await last_message.get_sender()
        sender_name = getattr(sender, "first_name", "") or getattr(sender, "title", "Без имени")
        text = last_message.text or "<медиа>"
        
        print(f"👤 Отправитель: {sender_name}")
        print(f"📝 Текст: {text[:100]}...")
        
        # Пересылаем последнее сообщение во все целевые чаты
        success_count = 0
        for target_chat_id in target_chat_ids:
            try:
                await client.forward_messages(target_chat_id, last_message)
                print(f"✅ Последнее сообщение переслано в {target_chat_id}")
                success_count += 1
            except Exception as e:
                print(f"❌ Ошибка пересылки в {target_chat_id}: {e}")
        
        print(f"\n🎉 Пересылка завершена! Успешно переслано в {success_count} чатов")
        
    except Exception as e:
        print(f"❌ Ошибка пересылки последнего сообщения: {e}")

@client.on(events.NewMessage)
async def handle_new_message(event):
    """Обрабатывает новые сообщения для всех настроенных чатов"""
    try:
        source_chat_id = event.chat_id
        
        # Проверяем, есть ли конфигурация для этого чата
        if source_chat_id not in FORWARD_CONFIG:
            return
        
        config = FORWARD_CONFIG[source_chat_id]
        target_chat_ids = config['targets']
        filter_type = config['filter_type']
        
        # Получаем информацию об отправителе
        sender = await event.get_sender()
        sender_name = getattr(sender, "first_name", "") or getattr(sender, "title", "Без имени")
        text = event.message.text or ""
        
        # Применяем фильтр
        should_forward = False
        
        if filter_type == 'all':
            # Пересылаем все сообщения
            should_forward = True
            print(f"\n📨 Новое сообщение из {source_chat_id}")
            
        elif filter_type == 'keyword':
            # Проверяем ключевые слова
            keywords = config['keywords']
            text_lower = text.lower()
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    should_forward = True
                    print(f"\n🎯 Сообщение с ключевым словом '{keyword}' из {source_chat_id}")
                    break
            
            if not should_forward:
                print(f"🎯 Сообщение не содержит ключевых слов - пропускаем")
                print(f"📝 Текст: {text[:50]}...")
                return
        
        if should_forward:
            # Определяем, что пересылать
            messages_to_forward = []
            
            if event.message.grouped_id:
                # Это медиагруппа - собираем все части
                gid = event.message.grouped_id
                print(f"🖼 Обнаружена медиагруппа (grouped_id={gid}) — собираю все части...")
                
                # Собираем все сообщения с тем же grouped_id
                all_grouped_messages = []
                async for msg in client.iter_messages(source_chat_id, limit=1000):
                    if msg.grouped_id == gid:
                        all_grouped_messages.append(msg)
                    # Небольшая задержка для предотвращения flood wait (только каждые 5 сообщений)
                    if len(all_grouped_messages) % 5 == 0:
                        await asyncio.sleep(0.03)
                
                # Сортируем по ID для правильного порядка (от старых к новым)
                all_grouped_messages.sort(key=lambda x: x.id)
                messages_to_forward = all_grouped_messages
                print(f"📸 Собрано частей медиагруппы: {len(messages_to_forward)}")
                
                # Логируем найденные сообщения
                for i, msg in enumerate(messages_to_forward):
                    print(f"   {i+1}. ID {msg.id}, дата: {msg.date}")
            else:
                # Одиночное сообщение
                messages_to_forward = [event.message]
                print("✉️ Одиночное сообщение")
            
            # Пересылаем во все целевые чаты
            success_count = 0
            for target_chat_id in target_chat_ids:
                try:
                    await client.forward_messages(target_chat_id, messages_to_forward)
                    print(f"✅ Переслано {len(messages_to_forward)} сообщений в {target_chat_id}!")
                    success_count += 1
                except Exception as e:
                    print(f"❌ Ошибка пересылки в {target_chat_id}: {e}")
            
            print(f"👤 От: {sender_name}")
            print(f"💬 Текст: {text}")
            print(f"📤 В чаты: {target_chat_ids}")
            print(f"📋 Конфигурация: {config['description']}")
            print(f"🎉 Успешно переслано в {success_count} чатов")
            print("-" * 50)
        
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")

async def main():
    print("🚀 Запуск универсального бота (множественная пересылка)...")
    print("📱 При первом запуске потребуется авторизация")
    print("📞 Введите номер телефона в формате +79123456789")
    print("🔐 Введите код из SMS")
    print("🔑 При необходимости введите пароль двухфакторной аутентификации")
    print()
    
    try:
        await client.start()
        print("✅ Бот подключен!")
        
        # Показываем конфигурацию
        print("\n📋 Настроенные пересылки:")
        for source, config in FORWARD_CONFIG.items():
            print(f"📡 {source} -> {config['targets']}")
            print(f"   Тип: {config['filter_type']}")
            print(f"   Описание: {config['description']}")
            if config['filter_type'] == 'keyword':
                print(f"   Ключевые слова: {', '.join(config['keywords'])}")
            print()
        
        print("\n🎯 Выберите режим работы:")
        print("1. Переслать ПОСЛЕДНИЕ сообщения из всех чатов (для проверки)")
        print("2. Мониторинг новых сообщений (режим по умолчанию)")
        
        try:
            choice = input("\nВведите номер (1-2): ").strip()
            
            if choice == "1":
                print("\n🔄 Пересылка последних сообщений из всех чатов...")
                
                for source_chat_id, config in FORWARD_CONFIG.items():
                    target_chat_ids = config['targets']
                    filter_type = config['filter_type']
                    
                    print(f"\n📡 Обрабатываю чат {source_chat_id}...")
                    
                    if filter_type == 'keyword':
                        await forward_messages_with_keyword(
                            source_chat_id, 
                            target_chat_ids, 
                            config['keywords']
                        )
                    elif filter_type == 'all':
                        await forward_all_messages(source_chat_id, target_chat_ids)
                
                print("\n✅ Пересылка завершена! Теперь запускаю мониторинг...")
                print("🔄 Мониторинг новых сообщений...")
                print("⏳ Жду новые сообщения...")
                await client.run_until_disconnected()
            else:
                print("🔄 Мониторинг новых сообщений...")
                print("⏳ Жду новые сообщения...")
                await client.run_until_disconnected()
                
        except KeyboardInterrupt:
            print("\n🛑 Остановка по Ctrl+C")
        except Exception as e:
            print(f"❌ Ошибка ввода: {e}")
            print("🔄 Запускаю мониторинг...")
            await client.run_until_disconnected()
            
    except KeyboardInterrupt:
        print("🛑 Остановка по Ctrl+C")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()
        print("👋 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())