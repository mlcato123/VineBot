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
from firebase_admin import storage
from firebase_admin import credentials
from firebase_admin import db
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

cred = credentials.Certificate('grapi-47cdc-firebase-adminsdk-w2zca-e36e2325ca.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://grapi-47cdc-default-rtdb.firebaseio.com/',
    'storageBucket': 'grapi-47cdc.appspot.com'
})

total_sectors = 27
sectors_per_page = 9
total_vines = 9
vines_per_page = 9
photo_data = {}
admin_ids = [853789956, 823556234]
tconv = lambda x: time.strftime("%Y", time.localtime(x)) #����������� ���� � ����������� ���

# ��������� ������ ��� ������� ��������
def generate_buttons(page, total_items, items_per_page):
    buttons = []
    start_item = (page - 1) * items_per_page + 1
    end_item = min(start_item + items_per_page, total_items + 1)
    for item in range(start_item, end_item):
        button = KeyboardButton(f'����� {item}')
        buttons.append(button)
    return buttons


def upload_photo_to_storage(photo_path):
    # �������� ���������� � ��������� Firebase Storage
    bucket = storage.bucket()
    blob = bucket.blob(photo_path)
    blob.upload_from_filename(photo_path)
    # ������� ���������� �������������
    blob.make_public()
    # ��������� URL-������ ����������� ����������
    photo_url = blob.public_url
    return photo_url

# ��������� ���������� � �������� ��� ������� ��������
def generate_keyboard(page, total_items, items_per_page):
    keyboard = ReplyKeyboardMarkup(row_width=3)
    buttons = generate_buttons(page, total_items, items_per_page)
    keyboard.add(*buttons)
    if page > 1:
        prev_button = KeyboardButton('�����')
        keyboard.add(prev_button)
    if page < total_items // items_per_page + 1:
        next_button = KeyboardButton('������')
        keyboard.add(next_button)
    search_button = KeyboardButton('�����')
    keyboard.add(search_button)
    return keyboard

# �������� ���������� ����
bot = telebot.TeleBot('6060999563:AAEcBNGXbAuiHc10xvj8KIOU8dGDazSCEJc')

# ���������� ������� /start
@bot.message_handler(commands=['start'])
def start(message):
    global photo_data
    photo_data = {}  # ������� ������ � ���������� ��� ������� ����
    keyboard = ReplyKeyboardMarkup(row_width=1)
    menu_button = KeyboardButton('������')
    keyboard.add(menu_button)
    bot.send_message(chat_id=message.chat.id, text='������! ����� ������ "������"', reply_markup=keyboard)

# ���������� ������� ������ "������"
@bot.message_handler(func=lambda message: message.text == '������')
def handle_burger_menu(message):
    page = 1
    keyboard = generate_keyboard(page, total_sectors, sectors_per_page)
    
    if int(message.from_user.id) in admin_ids:
        # ������� ���������� ��� ������ � ���������� �� ������ � ���������� 
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)    
        admin_button = KeyboardButton('���������� ����������')
        keyboard.add(admin_button)
        bot.send_message(chat_id=message.chat.id, text='������ ������ �����:', reply_markup=keyboard)
    else:
        # ������� ���������� ��� ������ ���� ��� ������
        keyboard = ReplyKeyboardMarkup(row_width=2)
        vine_button = KeyboardButton('����')
        grape_button = KeyboardButton('������')
        keyboard.add(vine_button, grape_button)
        bot.send_message(chat_id=message.chat.id, text='�������� ���� ��� ������:', reply_markup=keyboard)

# ���������� ������ ���� ��� ������
@bot.message_handler(func=lambda message: message.text == '����' or message.text == '������')

#def handle_if(message):
    

    

def handle_vine_grape_selection(message):
    global photo_data
    global vine_grape_id
    if message.text == '����':
        vine_grape_id = 0
        print(vine_grape_id)
    elif message.text == '������':
        vine_grape_id = 1
        print(vine_grape_id)
    # ��������� ����� � ������ � ����������
    photo_data['choice'] = message.text
    bot.send_message(chat_id=message.chat.id, text=f'�� ������� {message.text}')
    page = 1
    keyboard = generate_keyboard(page, total_sectors, sectors_per_page)
    bot.send_message(chat_id=message.chat.id, text='�������� ������:', reply_markup=keyboard)

current_page = 1  # ���������� ��� ������������ ������� ��������
global record_id

# �������-���������� ���������
@bot.message_handler(func=lambda message: message.text == '���������� ����������')
def handle_admin_button(message):
    ref = db.reference('GrApi')
    snapshot = ref.order_by_child('sick').equal_to('��').get()
    for key, value in snapshot.items():
        cell = value['cell']
        comment = value['comment']
        numVine = value['numVine']
        photoUrl = value['photoUrl']
        record_id=key 
        print(record_id)
        markup_inline = types.InlineKeyboardMarkup()
        
        # ������� ��������� � ���������
        message_text = f"����� ����: {numVine}\n�����������: {comment}\n������: {cell}\n������ �� ����: {photoUrl}"
        message = bot.send_photo(chat_id=message.chat.id, photo=value['photoUrl'], caption=message_text)

        # ������� ������ ��� ��������� �������� "sick"
        keyboard = types.InlineKeyboardMarkup()
        button_no = types.InlineKeyboardButton(text="�� ������", callback_data=f"update_sick ��� {record_id}")

        keyboard.add(button_no)

        # ��������� ������ �� ��������� � ���������
        bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id, reply_markup=keyboard)


# ���������� ������� �� ������ "���"
@bot.callback_query_handler(func=lambda call: call.data.startswith('update_sick'))
def update_sick(call):
    # ��������� ������ � �������� �� �����
    _, new_value, record_id = call.data.split()
    
    # �������� ID ������ �� callback_data

    print(record_id)

    
    # ��������� �������� ���� "sick" � ���� ������
    ref = db.reference('GrApi').child(record_id)
    ref.update({'sick': new_value})
    
    # ���������� ������������ ��������� � ���, ��� �������� ���� ���������
    bot.answer_callback_query(callback_query_id=call.id, text=f'�������� sick �������� �� {new_value}')


# ���������� ������ ������� ��� ������ ����
@bot.message_handler(func=lambda message: message.text.startswith('����� '))
def handle_sector_selection(message):
    
    item_number = int(message.text.split()[1])
    if 'cell' not in photo_data:
        # ��������� ��������� ������ � ������ � ����������
        photo_data['cell'] = item_number
        bot.send_message(chat_id=message.chat.id, text=f'�� ������� ������ {item_number}')
        page = 1
        keyboard = generate_keyboard(page, total_vines, vines_per_page)
        bot.send_message(chat_id=message.chat.id, text='�������� ���:', reply_markup=keyboard)
    else:
        # ��������� ��������� ����� ���� � ������ � ����������
        photo_data['numVine'] = item_number
        bot.send_message(chat_id=message.chat.id, text=f'�� ������� ��� ����� {item_number}')
        keyboard = ReplyKeyboardMarkup(row_width=1)
        take_photo_button = KeyboardButton('������� ������')
        select_photo_button = KeyboardButton('������� ���� �� �������')
        cancel_button = KeyboardButton('��������')
        keyboard.add(take_photo_button, select_photo_button, cancel_button)
        bot.send_message(chat_id=message.chat.id, text='�������� ��������:', reply_markup=keyboard)

# ���������� ������� ������ "������"
@bot.message_handler(func=lambda message: message.text == '������')
def handle_next_page(message):
    global current_page
    current_page += 1
    if 'cell' not in photo_data:
        keyboard = generate_keyboard(current_page, total_sectors, sectors_per_page)
        bot.send_message(chat_id=message.chat.id, text='������ ������:', reply_markup=keyboard)
    else:
        keyboard = generate_keyboard(current_page, total_vines, vines_per_page)
        bot.send_message(chat_id=message.chat.id, text='�������� ����� ����:', reply_markup=keyboard)

# ���������� ������� ������ "�����"
@bot.message_handler(func=lambda message: message.text == '�����')
def handle_prev_page(message):
    global current_page
    current_page -= 1
    if 'cell' not in photo_data:
        keyboard = generate_keyboard(current_page, total_sectors, sectors_per_page)
        bot.send_message(chat_id=message.chat.id, text='������ ������:', reply_markup=keyboard)
    else:
        keyboard = generate_keyboard(current_page, total_vines, vines_per_page)
        bot.send_message(chat_id=message.chat.id, text='�������� ����� ����:', reply_markup=keyboard)

# ���������� ������� ������ "�����"
@bot.message_handler(func=lambda message: message.text == '�����')
def handle_search(message):
    if 'cell' not in photo_data:
        bot.send_message(chat_id=message.chat.id, text='������� ����� ������� (�����):')
    else:
        bot.send_message(chat_id=message.chat.id, text='������� ����� ���� (�����):')

# ���������� ����� ������ ������� ��� ����
@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_search_number(message):
    global photo_data
    item_number = int(message.text)
    if 'cell' not in photo_data:
        if 1 <= item_number <= total_sectors:
            # ��������� ��������� ������ � ������ � ����������
            photo_data['cell'] = item_number
            bot.send_message(chat_id=message.chat.id, text=f'�� ������� ������ {item_number}')
            page = 1
            keyboard = generate_keyboard(page, total_vines, vines_per_page)
            bot.send_message(chat_id=message.chat.id, text='�������� ����� ����:', reply_markup=keyboard)
        else:
            bot.send_message(chat_id=message.chat.id, text='������������ ����� �������')
    else:
        if 1 <= item_number <= total_vines:
            # ��������� ��������� ����� ���� � ������ � ����������
            photo_data['numVine'] = item_number
            bot.send_message(chat_id=message.chat.id, text=f'�� ������� ��� ����� {item_number}')
            keyboard = ReplyKeyboardMarkup(row_width=1)
            take_photo_button = KeyboardButton('������� ������')
            select_photo_button = KeyboardButton('������� ���� �� �������')
            cancel_button = KeyboardButton('��������')
            keyboard.add(take_photo_button, select_photo_button, cancel_button)
            bot.send_message(chat_id=message.chat.id, text='�������� ��������:', reply_markup=keyboard)
        else:
            bot.send_message(chat_id=message.chat.id, text='������������ ����� ����')

# ���������� ������� ������ "������� ������"
@bot.message_handler(func=lambda message: message.text == '������� ������')
def handle_take_photo(message):
    # ���������� ������ ������������ � �������� ������� ����������
    bot.send_message(chat_id=message.chat.id, text='����������, �������� ���������� � ��������� ��.')

# ���������� ������� ������ "������� ���� �� �������"
@bot.message_handler(func=lambda message: message.text == '������� ���� �� �������')
def handle_select_photo(message):
    # ���������� ������ ������������ � �������� ������� ���������� �� �������
    bot.send_message(chat_id=message.chat.id, text='����������, �������� ���������� �� ������� � ���������')
    photo_data = {}

# ���������� ��������� ����������
@bot.message_handler(content_types=['photo'])
def handle_received_photo(message):
    global photo_data
    # �������� ���������� � ����������
    photo = message.photo[-1]  # ����� ��������� (����� �������) ���������� �� ������
    file_id = photo.file_id

    # ��������� ����������
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # ��������� ���������� �� �������
    photo_path = f'photos/{message.from_user.id}.jpg'  # ���� ��� ���������� ����������
    with open(photo_path, 'wb') as file:
        file.write(downloaded_file)

    # ��������� ���������� � ���������� � ������
    photo_data['idPhoto'] = photo_path

    # ���������� ��������� � �������������� � ���������� ���������� ����������
    bot.send_message(chat_id=message.chat.id, text='���������� ������� ���������!')
    with open(photo_path, 'rb') as file:
        bot.send_photo(chat_id=message.chat.id, photo=file)

    # ���������� ������ ��� �������� ���������� � ����� �����������
    keyboard = ReplyKeyboardMarkup(row_width=1)
    delete_button = KeyboardButton('������� ����')
    comment_button_text = '��������������� �����������' if 'comment' in photo_data else '������ �����������'
    comment_button = KeyboardButton(comment_button_text)
    keyboard.add(delete_button, comment_button)
    bot.send_message(chat_id=message.chat.id, text='�������� ��������:', reply_markup=keyboard)

# ���������� ������� ������ "������� ����"
@bot.message_handler(func=lambda message: message.text == '������� ����')
def handle_delete_photo(message):
    global photo_data
    if 'idPhoto' in photo_data:
        # ������� ���� � ����������� � �������
        os.remove(photo_data['idPhoto'])
        # ������� ���������� � ���������� �� ������
        del photo_data['idPhoto']
        bot.send_message(chat_id=message.chat.id, text='���������� ������� �������!')
        keyboard = ReplyKeyboardMarkup(row_width=1)
        take_photo_button = KeyboardButton('������� ������')
        select_photo_button = KeyboardButton('������� ���� �� �������')
        cancel_button = KeyboardButton('��������')
        keyboard.add(take_photo_button, select_photo_button, cancel_button)
        bot.send_message(chat_id=message.chat.id, text='�������� ��������:', reply_markup=keyboard)
    else:
        bot.send_message(chat_id=message.chat.id, text='��� ����������� ����������')

# ���������� ������� ������ "������ �����������" ��� "��������������� �����������"
@bot.message_handler(func=lambda message: message.text == '������ �����������' or message.text == '��������������� �����������')
def handle_input_comment(message):
    global photo_data 
    if 'idPhoto' in photo_data:
        bot.send_message(chat_id=message.chat.id, text='������� ����������� � ����������:')
    else:
        bot.send_message(chat_id=message.chat.id, text='��� ����������� ����������')

# ���������� ����� �����������
@bot.message_handler(func=lambda message: True)
def handle_comment(message):
    global date_mes
    global photo_data
    if 'idPhoto' in photo_data:
        # ��������� ����������� � ������ � ����������
        photo_data['comment'] = message.text.strip()
        bot.send_message(chat_id=message.chat.id, text='����������� ������� ��������!')
        keyboard = InlineKeyboardMarkup(row_width=1)
        finish_button = InlineKeyboardButton('��������� �����', callback_data='finish')
        keyboard.add(finish_button)
        bot.send_message(chat_id=message.chat.id, text='������� "��������� �����" ��� ���������� ������', reply_markup=keyboard)
        tconv = lambda x: time.strftime("%Y", time.localtime(x)) #����������� ���� � ����������� ���
        date_mes = tconv(message.date)
        print(tconv(message.date)) # ����� ���� ���� 20:58:30 05.07.2020

# ���������� ������� ������ "��������� �����"
@bot.callback_query_handler(func=lambda call: call.data == 'finish')
def handle_finish_selection(call):
    
    global photo_data
    if vine_grape_id == 0:
            if 'idPhoto' in photo_data:
                # �������� ���������� � ��������� Firebase Storage
                photo_url = upload_photo_to_storage(photo_data['idPhoto'])
                # ���������� URL-������ ���������� � ������ � ����������
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

                if class_name == 'Good':
                    photo_data['sick'] = '���'
                else:
                    photo_data['sick'] = '��'

                # ��������� ������ � ���������� � ���� ������ Firebase
                ref = db.reference('GrApi')
                photo_data ['dateYear'] = date_mes
                print(date_mes, "date_mes")
                ref.push(photo_data)
                bot.send_message(chat_id=call.message.chat.id, text='����� ������� ��������!')
                # ������� ������ � ����������
                photo_data = {}
                keyboard = ReplyKeyboardMarkup(row_width=1)
                menu_button = KeyboardButton('������')
                keyboard.add(menu_button)
                bot.send_message(chat_id=call.message.chat.id, text='������� ������ "������" ��� ������ ������ ������', reply_markup=keyboard)
            else:
                # ���������� ��������� �� ���������� ����������� ����������
                bot.send_message(chat_id=call.message.chat.id, text='��� ����������� ����������')

    else:
        if 'idPhoto' in photo_data:
                # �������� ���������� � ��������� Firebase Storage
                photo_url = upload_photo_to_storage(photo_data['idPhoto'])
                # ���������� URL-������ ���������� � ������ � ����������
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

                
                # ��������� ������ � ���������� � ���� ������ Firebase
                ref = db.reference('GrApi')
                photo_data ['dateYear'] = date_mes
                print(date_mes, "date_mes")
                ref.push(photo_data)
                bot.send_message(chat_id=call.message.chat.id, text='����� ������� ��������!')
                # ������� ������ � ����������
                photo_data = {}
                keyboard = ReplyKeyboardMarkup(row_width=1)
                menu_button = KeyboardButton('������')
                keyboard.add(menu_button)
                bot.send_message(chat_id=call.message.chat.id, text='������� ������ "������" ��� ������ ������ ������', reply_markup=keyboard)
        else:
                # ���������� ��������� �� ���������� ����������� ����������
                bot.send_message(chat_id=call.message.chat.id, text='��� ����������� ����������')
                



# ���������� ������� ������ "��������"
@bot.message_handler(func=lambda message: message.text == '��������')
def handle_cancel(message):
    global photo_data
    if 'idPhoto' in photo_data:
        # ������� ���� � ����������� � �������
        os.remove(photo_data['idPhoto'])
    # ������� ������ � ���������� ��� ���������� ������
    photo_data = {}
    keyboard = ReplyKeyboardMarkup(row_width=1)
    menu_button = KeyboardButton('������')
    keyboard.add(menu_button)
    bot.send_message(chat_id=message.chat.id, text='����� �������. ������� ������ "������" ��� ������ ������ ������', reply_markup=keyboard)

# ������� ��� ���������� ������ �� �����
def save_data(data):
    with open('data.json', 'w') as file:
        json.dump(data, file)



# ������ ����
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    bot.polling()
