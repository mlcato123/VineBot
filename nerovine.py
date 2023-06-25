# -*- coding: cp1251 -*-
import os
import logging
import telebot
from keras.models import load_model  # TensorFlow is required for Keras to work
from PIL import Image, ImageOps  # Install pillow instead of PIL
import numpy as np
import json
import firebase_admin
import datetime
import time
import random
from firebase_admin import storage
from firebase_admin import credentials
from firebase_admin import db
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

cred = credentials.Certificate("myqwer-9abe3-firebase-adminsdk-vzw4u-4b396b9c62.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://myqwer-9abe3-default-rtdb.asia-southeast1.firebasedatabase.app/',
    'storageBucket': 'myqwer-9abe3.appspot.com'
})

total_sectors = 27
sectors_per_page = 9
total_vines = 9
vines_per_page = 9
photo_data = {}
admin_ids = [853789956, 1822768141]
tconv = lambda x: time.strftime("%Y", time.localtime(x)) #Конвертация даты в читабельный вид

# Генерация кнопок для текущей страницы
def generate_buttons(page, total_items, items_per_page):
    buttons = []
    start_item = (page - 1) * items_per_page + 1
    end_item = min(start_item + items_per_page, total_items + 1)
    for item in range(start_item, end_item):
        button = KeyboardButton(f'Номер {item}')
        buttons.append(button)
    return buttons


def upload_photo_to_storage(photo_path):
    # Загрузка фотографии в хранилище Firebase Storage
    bucket = storage.bucket()
    blob = bucket.blob(photo_path)
    blob.upload_from_filename(photo_path)
    # Сделать фотографию общедоступной
    blob.make_public()
    # Получение URL-адреса загруженной фотографии
    photo_url = blob.public_url
    return photo_url

# Генерация клавиатуры с кнопками для текущей страницы
def generate_keyboard(page, total_items, items_per_page):
    keyboard = ReplyKeyboardMarkup(row_width=3)
    buttons = generate_buttons(page, total_items, items_per_page)
    keyboard.add(*buttons)
    if page > 1:
        prev_button = KeyboardButton('Назад')
        keyboard.add(prev_button)
    if page < total_items // items_per_page + 1:
        next_button = KeyboardButton('Вперед')
        keyboard.add(next_button)
    search_button = KeyboardButton('Поиск')
    keyboard.add(search_button)
    return keyboard

# Создание экземпляра бота
bot = telebot.TeleBot('6060999563:AAEcBNGXbAuiHc10xvj8KIOU8dGDazSCEJc')

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    global photo_data
    photo_data = {}  # Очищаем данные о фотографии при запуске бота
    keyboard = ReplyKeyboardMarkup(row_width=1)
    menu_button = KeyboardButton('Начать')
    keyboard.add(menu_button)
    bot.send_message(chat_id=message.chat.id, text='Привет! Нажми кнопку "Начать"', reply_markup=keyboard)

# Обработчик нажатия кнопки "Начать"
@bot.message_handler(func=lambda message: message.text == 'Начать')
def handle_burger_menu(message):
    page = 1
    keyboard = generate_keyboard(page, total_sectors, sectors_per_page)
    
    if int(message.from_user.id) in admin_ids:
        # Создаем клавиатуру для админа и отправляем ее вместе с сообщением 
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)    
        admin_button = KeyboardButton('Посмотреть зараженные')
        keyboard.add(admin_button)
        bot.send_message(chat_id=message.chat.id, text='Выбери сектор админ:', reply_markup=keyboard)
    else:
        # Создаем клавиатуру для выбора лозы или грозди
        keyboard = ReplyKeyboardMarkup(row_width=2)
        vine_button = KeyboardButton('Лоза')
        grape_button = KeyboardButton('Гроздь')
        keyboard.add(vine_button, grape_button)
        bot.send_message(chat_id=message.chat.id, text='Выберите лозу или гроздь:', reply_markup=keyboard)

# Обработчик выбора лозы или грозди
@bot.message_handler(func=lambda message: message.text == 'Лоза' or message.text == 'Гроздь')

#def handle_if(message):
    

    

def handle_vine_grape_selection(message):
    global photo_data
    global vine_grape_id
    if message.text == 'Лоза':
        vine_grape_id = 0
        print(vine_grape_id)
    elif message.text == 'Гроздь':
        vine_grape_id = 1
        print(vine_grape_id)
    # Сохраняем выбор в данных о фотографии
    photo_data['choice'] = message.text
    bot.send_message(chat_id=message.chat.id, text=f'Вы выбрали {message.text}')
    page = 1
    keyboard = generate_keyboard(page, total_sectors, sectors_per_page)
    bot.send_message(chat_id=message.chat.id, text='Выберите сектор:', reply_markup=keyboard)

current_page = 1  # Переменная для отслеживания текущей страницы
global record_id

# Функция-обработчик сообщений
@bot.message_handler(func=lambda message: message.text == 'Посмотреть зараженные')
def handle_admin_button(message):
    ref = db.reference('GrApi')
    snapshot = ref.order_by_child('sick').equal_to('да').get()
    for key, value in snapshot.items():
        cell = value['cell']
        comment = value['comment']
        numVine = value['numVine']
        photoUrl = value['photoUrl']
        record_id=key 
        markup_inline = types.InlineKeyboardMarkup()
        
        # Создаем сообщение с карточкой
        
        message_text = f"Номер ряда: {numVine}\nКомментарий: {comment}\nСектор: {cell}\nСсылка на фото: {photoUrl}"
        message = bot.send_photo(chat_id=message.chat.id, photo=value['photoUrl'], caption=message_text)

        # Создаем кнопку для изменения значения "sick"
        keyboard = types.InlineKeyboardMarkup()
        button_no = types.InlineKeyboardButton(text="Не болеет", callback_data=f"update_sick нет {record_id}")

        keyboard.add(button_no)

        # Добавляем кнопку на сообщение с карточкой
        bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id, reply_markup=keyboard)


# Обработчик колбэка от кнопки "Нет"
@bot.callback_query_handler(func=lambda call: call.data.startswith('update_sick'))
def update_sick(call):
    # Разбиваем строку с колбэком на части
    _, new_value, record_id = call.data.split()
    
    # Получаем ID записи из callback_data

    print(record_id)

    
    # Обновляем значение поля "sick" в базе данных
    ref = db.reference('GrApi').child(record_id)
    ref.update({'sick': new_value})
    
    # Отправляем пользователю сообщение о том, что значение было обновлено
    bot.answer_callback_query(callback_query_id=call.id, text=f'Значение sick изменено на {new_value}')


# Обработчик выбора сектора или номера лозы
@bot.message_handler(func=lambda message: message.text.startswith('Номер '))
def handle_sector_selection(message):
    
    item_number = int(message.text.split()[1])
    if 'cell' not in photo_data:
        # Сохраняем выбранный сектор в данных о фотографии
        photo_data['cell'] = item_number
        bot.send_message(chat_id=message.chat.id, text=f'Вы выбрали сектор {item_number}')
        page = 1
        keyboard = generate_keyboard(page, total_vines, vines_per_page)
        bot.send_message(chat_id=message.chat.id, text='Выберите ряд:', reply_markup=keyboard)
    else:
        # Сохраняем выбранный номер лозы в данных о фотографии
        photo_data['numVine'] = item_number
        bot.send_message(chat_id=message.chat.id, text=f'Вы выбрали ряд номер {item_number}')
        keyboard = ReplyKeyboardMarkup(row_width=1)
        take_photo_button = KeyboardButton('Сделать снимок')
        select_photo_button = KeyboardButton('Выбрать фото из галереи')
        cancel_button = KeyboardButton('Прервать')
        keyboard.add(take_photo_button, select_photo_button, cancel_button)
        bot.send_message(chat_id=message.chat.id, text='Выберите действие:', reply_markup=keyboard)

# Обработчик нажатия кнопки "Вперед"
@bot.message_handler(func=lambda message: message.text == 'Вперед')
def handle_next_page(message):
    global current_page
    current_page += 1
    if 'cell' not in photo_data:
        keyboard = generate_keyboard(current_page, total_sectors, sectors_per_page)
        bot.send_message(chat_id=message.chat.id, text='Выбери сектор:', reply_markup=keyboard)
    else:
        keyboard = generate_keyboard(current_page, total_vines, vines_per_page)
        bot.send_message(chat_id=message.chat.id, text='Выберите номер ряда:', reply_markup=keyboard)

# Обработчик нажатия кнопки "Назад"
@bot.message_handler(func=lambda message: message.text == 'Назад')
def handle_prev_page(message):
    global current_page
    current_page -= 1
    if 'cell' not in photo_data:
        keyboard = generate_keyboard(current_page, total_sectors, sectors_per_page)
        bot.send_message(chat_id=message.chat.id, text='Выбери сектор:', reply_markup=keyboard)
    else:
        keyboard = generate_keyboard(current_page, total_vines, vines_per_page)
        bot.send_message(chat_id=message.chat.id, text='Выберите номер ряда:', reply_markup=keyboard)

# Обработчик нажатия кнопки "Поиск"
@bot.message_handler(func=lambda message: message.text == 'Поиск')
def handle_search(message):
    if 'cell' not in photo_data:
        bot.send_message(chat_id=message.chat.id, text='Введите номер сектора (число):')
    else:
        bot.send_message(chat_id=message.chat.id, text='Введите номер ряда (число):')

# Обработчик ввода номера сектора или лозы
@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_search_number(message):
    global photo_data
    item_number = int(message.text)
    if 'cell' not in photo_data:
        if 1 <= item_number <= total_sectors:
            # Сохраняем выбранный сектор в данных о фотографии
            photo_data['cell'] = item_number
            bot.send_message(chat_id=message.chat.id, text=f'Вы выбрали сектор {item_number}')
            page = 1
            keyboard = generate_keyboard(page, total_vines, vines_per_page)
            bot.send_message(chat_id=message.chat.id, text='Выберите номер ряда:', reply_markup=keyboard)
        else:
            bot.send_message(chat_id=message.chat.id, text='Некорректный номер сектора')
    else:
        if 1 <= item_number <= total_vines:
            # Сохраняем выбранный номер лозы в данных о фотографии
            photo_data['numVine'] = item_number
            bot.send_message(chat_id=message.chat.id, text=f'Вы выбрали ряд номер {item_number}')
            keyboard = ReplyKeyboardMarkup(row_width=1)
            take_photo_button = KeyboardButton('Сделать снимок')
            select_photo_button = KeyboardButton('Выбрать фото из галереи')
            cancel_button = KeyboardButton('Прервать')
            keyboard.add(take_photo_button, select_photo_button, cancel_button)
            bot.send_message(chat_id=message.chat.id, text='Выберите действие:', reply_markup=keyboard)
        else:
            bot.send_message(chat_id=message.chat.id, text='Некорректный номер ряда')

# Обработчик нажатия кнопки "Сделать снимок"
@bot.message_handler(func=lambda message: message.text == 'Сделать снимок')
def handle_take_photo(message):
    # Отправляем запрос пользователю с просьбой сделать фотографию
    bot.send_message(chat_id=message.chat.id, text='Пожалуйста, сделайте фотографию и отправьте ее.')

# Обработчик нажатия кнопки "Выбрать фото из галереи"
@bot.message_handler(func=lambda message: message.text == 'Выбрать фото из галереи')
def handle_select_photo(message):
    # Отправляем запрос пользователю с просьбой выбрать фотографии из галереи
    bot.send_message(chat_id=message.chat.id, text='Пожалуйста, выберите фотографию из галереи и отправьте')
    photo_data = {}

# Обработчик получения фотографии
@bot.message_handler(content_types=['photo'])
def handle_received_photo(message):
    global photo_data
    # Получаем информацию о фотографии
    photo = message.photo[-1]  # Берем последнюю (самую большую) фотографию из списка
    file_id = photo.file_id

    # Скачиваем фотографию
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Сохраняем фотографию на сервере
    a = random.randint (0,9999999999999)
    photo_path = f'photos/{a}.jpg'  # Путь для сохранения фотографии
    with open(photo_path, 'wb') as file:
        file.write(downloaded_file)

    # Сохраняем информацию о фотографии в данных
    photo_data['idPhoto'] = photo_path

    # Отправляем сообщение с подтверждением и показываем полученную фотографию
    bot.send_message(chat_id=message.chat.id, text='Фотография успешно сохранена!')
    with open(photo_path, 'rb') as file:
        bot.send_photo(chat_id=message.chat.id, photo=file)

    # Показываем кнопки для удаления фотографии и ввода комментария
    keyboard = ReplyKeyboardMarkup(row_width=1)
    delete_button = KeyboardButton('Удалить фото')
    comment_button_text = 'Отредактировать комментарий' if 'comment' in photo_data else 'Ввести комментарий'
    comment_button = KeyboardButton(comment_button_text)
    keyboard.add(delete_button, comment_button)
    bot.send_message(chat_id=message.chat.id, text='Выберите действие:', reply_markup=keyboard)

# Обработчик нажатия кнопки "Удалить фото"
@bot.message_handler(func=lambda message: message.text == 'Удалить фото')
def handle_delete_photo(message):
    global photo_data
    if 'idPhoto' in photo_data:
        # Удаляем файл с фотографией с сервера
        os.remove(photo_data['idPhoto'])
        # Удаляем информацию о фотографии из данных
        del photo_data['idPhoto']
        bot.send_message(chat_id=message.chat.id, text='Фотография успешно удалена!')
        keyboard = ReplyKeyboardMarkup(row_width=1)
        take_photo_button = KeyboardButton('Сделать снимок')
        select_photo_button = KeyboardButton('Выбрать фото из галереи')
        cancel_button = KeyboardButton('Прервать')
        keyboard.add(take_photo_button, select_photo_button, cancel_button)
        bot.send_message(chat_id=message.chat.id, text='Выберите действие:', reply_markup=keyboard)
    else:
        bot.send_message(chat_id=message.chat.id, text='Нет загруженной фотографии')

# Обработчик нажатия кнопки "Ввести комментарий" или "Отредактировать комментарий"
@bot.message_handler(func=lambda message: message.text == 'Ввести комментарий' or message.text == 'Отредактировать комментарий')
def handle_input_comment(message):
    global photo_data 
    if 'idPhoto' in photo_data:
        bot.send_message(chat_id=message.chat.id, text='Введите комментарий к фотографии:')
    else:
        bot.send_message(chat_id=message.chat.id, text='Нет загруженной фотографии')

# Обработчик ввода комментария
@bot.message_handler(func=lambda message: True)
def handle_comment(message):
    global date_mes
    global photo_data
    if 'idPhoto' in photo_data:
        # Сохраняем комментарий в данных о фотографии
        photo_data['comment'] = message.text.strip()
        bot.send_message(chat_id=message.chat.id, text='Комментарий успешно сохранен!')
        keyboard = InlineKeyboardMarkup(row_width=1)
        finish_button = InlineKeyboardButton('Завершить отчет', callback_data='finish')
        keyboard.add(finish_button)
        bot.send_message(chat_id=message.chat.id, text='Нажмите "Завершить отчет" для завершения выбора', reply_markup=keyboard)
        tconv = lambda x: time.strftime("%Y", time.localtime(x)) #Конвертация даты в читабельный вид
        date_mes = tconv(message.date)
        print(tconv(message.date)) # Вывод даты типо 20:58:30 05.07.2020

# Обработчик нажатия кнопки "Завершить отчет"
@bot.callback_query_handler(func=lambda call: call.data == 'finish')
def handle_finish_selection(call):
    
    global photo_data
    if vine_grape_id == 0:
            if 'idPhoto' in photo_data:
                # Загрузка фотографии в хранилище Firebase Storage
                photo_url = upload_photo_to_storage(photo_data['idPhoto'])
                # Сохранение URL-адреса фотографии в данных о фотографии
                photo_data['photoUrl'] = photo_url

                        # Disable scientific notation for clarity
                np.set_printoptions(suppress=True)

                # Load the model
                model = load_model("keras_Model.h5", compile=False)

                # Load the labels
                class_names = open("labels.txt", "r").readlines()

                # Create the array of the right shape to feed into the keras model
                # The 'length' or number of images you can put into the array is
                # determined by the first position in the shape tuple, in this case 1
                data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

                # Replace this with the path to your image
                image = Image.open(photo_data['idPhoto']).convert("RGB")

                # resizing the image to be at least 224x224 and then cropping from the center
                size = (224, 224)
                image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)

                # turn the image into a numpy array
                image_array = np.asarray(image)

                # Normalize the image
                normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

                # Load the image into the array
                data[0] = normalized_image_array

                # Predicts the model
                prediction = model.predict(data)
                index = np.argmax(prediction)
                class_name = class_names[index]
                confidence_score = prediction[0][index]

                # Print prediction and confidence score

                print("Class:", class_name[2:], end="")
                print("Confidence Score:", confidence_score)
                print('test', class_name[2:])
                if class_name == 'Good':
                    photo_data['sick'] = 'нет'
                else:
                    photo_data['sick'] = 'да'

                # Сохраняем данные о фотографии в базе данных Firebase
                ref = db.reference('GrApi')
                photo_data ['dateYear'] = date_mes
                print(date_mes, "date_mes")
                ref.push(photo_data)
                bot.send_message(chat_id=call.message.chat.id, text='Отчет успешно завершен!')
                # Очищаем данные о фотографии
                photo_data = {}
                keyboard = ReplyKeyboardMarkup(row_width=1)
                menu_button = KeyboardButton('Начать')
                keyboard.add(menu_button)
                bot.send_message(chat_id=call.message.chat.id, text='Нажмите кнопку "Начать" для начала нового выбора', reply_markup=keyboard)
            else:
                # Отправляем сообщение об отсутствии загруженной фотографии
                bot.send_message(chat_id=call.message.chat.id, text='Нет загруженной фотографии')

    else:
        if 'idPhoto' in photo_data:
                # Загрузка фотографии в хранилище Firebase Storage
                photo_url = upload_photo_to_storage(photo_data['idPhoto'])
                # Сохранение URL-адреса фотографии в данных о фотографии
                photo_data['photoUrl'] = photo_url
                # Disable scientific notation for clarity
                np.set_printoptions(suppress=True)

                # Load the model
                model = load_model("keras_Model2.h5", compile=False)

                # Load the labels
                class_names = open("labels2.txt", "r").readlines()

                # Create the array of the right shape to feed into the keras model
                # The 'length' or number of images you can put into the array is
                # determined by the first position in the shape tuple, in this case 1
                data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

                # Replace this with the path to your image
                image = Image.open(photo_data['idPhoto']).convert("RGB")

                # resizing the image to be at least 224x224 and then cropping from the center
                size = (224, 224)
                image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)

                # turn the image into a numpy array
                image_array = np.asarray(image)

                # Normalize the image
                normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

                # Load the image into the array
                data[0] = normalized_image_array

                # Predicts the model
                prediction = model.predict(data)
                index = np.argmax(prediction)
                class_nameVine = class_names[index]
                confidence_score = prediction[0][index]

                # Print prediction and confidence score
                print("Class:", [class_nameVine[2:]], end="")
                print("Confidence Score:", confidence_score)
                print(class_nameVine, "         ", class_nameVine[2:])
                photo_data['phenopause'] = class_nameVine[2:]

                
                # Сохраняем данные о фотографии в базе данных Firebase
                ref = db.reference('GrApi')
                photo_data ['dateYear'] = date_mes
                print(date_mes, "date_mes")
                ref.push(photo_data)
                bot.send_message(chat_id=call.message.chat.id, text='Отчет успешно завершен!')
                # Очищаем данные о фотографии
                photo_data = {}
                keyboard = ReplyKeyboardMarkup(row_width=1)
                menu_button = KeyboardButton('Начать')
                keyboard.add(menu_button)
                bot.send_message(chat_id=call.message.chat.id, text='Нажмите кнопку "Начать" для начала нового выбора', reply_markup=keyboard)
        else:
                # Отправляем сообщение об отсутствии загруженной фотографии
                bot.send_message(chat_id=call.message.chat.id, text='Нет загруженной фотографии')
                



# Обработчик нажатия кнопки "Прервать"
@bot.message_handler(func=lambda message: message.text == 'Прервать')
def handle_cancel(message):
    global photo_data
    if 'idPhoto' in photo_data:
        # Удаляем файл с фотографией с сервера
        os.remove(photo_data['idPhoto'])
    # Очищаем данные о фотографии при прерывании выбора
    photo_data = {}
    keyboard = ReplyKeyboardMarkup(row_width=1)
    menu_button = KeyboardButton('Начать')
    keyboard.add(menu_button)
    bot.send_message(chat_id=message.chat.id, text='Выбор прерван. Нажмите кнопку "Начать" для начала нового выбора', reply_markup=keyboard)

# Функция для сохранения данных на диске
def save_data(data):
    with open('data.json', 'w') as file:
        json.dump(data, file)



# Запуск бота
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    bot.polling()
