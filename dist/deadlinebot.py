import telebot
from telebot import types
import pymysql.cursors
import time
import pymysql
from config import host, user, password, db_name,bot_token

bot = telebot.TeleBot(bot_token)

user_dict = {"name_group": "",
             "Starosta": "",
             "Tg": "",        # for data in db
             "user_id": "",
             "students": ""}

db_adding_storage = {"group": "",  #IO-05
                    "subject": "", #TEMK
                  "type_work": "",  #lab 1                            #for data in table starosta
                  "deadline": ""}  #2022-04-23

id_dict = {"id_group": "",
           "id_subject": "",
           "id_typework": "",        # for id in all_id
           "id_deadline": ""}
all_deadlines = []
id_from_all_id = {"id_g": "",
           "id_s": "",
           "id_tow": "",        # for id in all_id
           "id_d": "",
            "id": ""}

test_list = []
old_deadline = []
old_id = []

max = 0
id = ""
try:
    connection = pymysql.connect(
        host=host,
        port=3306,
        user=user,
        password=password,  #conection to db
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    print("successfuly connected...")

except Exception as ex:
    print("Connection refused...")
    print(ex)

#welcome message & start program
@bot.message_handler(commands=['start'])
def start_bot(message):
    bot.send_message(message.chat.id, "Доброго дня, це бот для контролю дедлайнів у своїй групі."
                                      " Для старту натисніть або напишіть /start")
    markup2 = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup2.add("Я хочу побачити свої дедлайни")
    msg = bot.reply_to(message,
                       "Список доступних команд:\n /start ,"
                       " /help - Для початку роботи\n /about - Про бота та авторів",
                       reply_markup=markup2)
    bot.register_next_step_handler(msg, next_one)

def next_one(message): #start by button
    if message.text == "Я хочу побачити свої дедлайни":
        msg = bot.reply_to(message, "введіть вашу группу")
        bot.register_next_step_handler(msg, group_name)


@bot.message_handler(commands=['student'])
def start_group_name(message):  # start for student
    msg = bot.reply_to(message, "введіть вашу группу")
    bot.register_next_step_handler(msg, group_name)  #enter the name of groop

def group_name(message):
    try:
        chat_id = message.chat.id
        group = message.text
        bot.send_message(message.chat.id,  "ваша група - "+ group)
        #a = ["Группа:", " Предмет:","Задание:","Дедлайн:"]
        with connection.cursor() as cursor: #
            group_in_sql = f"select * from group_starosta where Group_name = '{group}';"  #сhecking group in db
            cursor.execute(group_in_sql)
            group_in_table = cursor.fetchall()
            if group_in_table:
                with connection.cursor() as cursor:  #here we get the entire table with data from the database
                    group_table = f"select \
                                    Group_name, Subject, type_work, deadline\
                                    from all_id \
                                    inner join group_starosta on all_id.g_id = group_starosta.Group_id and Group_name = '{group}'\
                                    inner join subjects on all_id.s_id = subjects.Subject_id\
                                    inner join works on all_id.tow_id = works.type_work_id\
                                    inner join deadlines on all_id.d_id = deadlines.deadline_id\
                                    order by deadline;"
                    cursor.execute(group_table)
                    rows = cursor.fetchall()
                    #print(rows)
                    if not rows:
                        bot.send_message(message.chat.id, "Гарні новини!\n"
                                                          f"Наразі у бд немає жодного запису стосовно твоєї групи - {group}\n"
                                                          "Тож звернися до старости та попроси додати дедлайни до бази")
                    else:
                        # print(rows)
                        table = ""
                        for row in rows:
                            #print(row)
                            for i in row:
                                table += str(row.get(i)) + "-"
                            table += "\n"
                        bot.send_message(message.chat.id, "Твої дедлайни: \n" + table)  #data output
            else:
                bot.reply_to(message, "вашої групи немає в бд, спробуйте ще раз натиснувши /student")
    except Exception as e:
       print(e.with_traceback())
       bot.reply_to(message, "вашої групи немає в бд")

@bot.message_handler(commands=['admin'])
def admin_panel(message):  #admin panel. output table with main info from group
    with connection.cursor() as cursor:
        admin_table = "select * from group_starosta;"
        cursor.execute(admin_table)
        rows = cursor.fetchall()
        table = ""
        for row in rows:
            for i in row:
                table+= str(row.get(i))+"-"
            table+="\n"
        bot.send_message(message.chat.id, table)


@bot.message_handler(commands=["starosta"])
def starosta_panel(message):                                       #start for starosta panel
    msg_starosta = bot.reply_to(message, "введіть вашу группу")
    bot.register_next_step_handler(msg_starosta,starosta_start)

def starosta_start(message):
    starosta_group = message.text
    try:
        with connection.cursor() as cursor:
            group_in_sql = f"select * from group_starosta where Group_name = '{starosta_group}';"
            cursor.execute(group_in_sql)
            group_in_table = cursor.fetchall()
            if group_in_table: #checking for the presence of a group in the database
                user_id = message.from_user.id
                starosta_true = f"select Group_id from group_starosta where user_id ='{user_id}' and Group_name = '{starosta_group}';"
                cursor.execute(starosta_true)
                starosta_in_db = cursor.fetchall()

                if starosta_in_db:
                    bot.send_message(message.chat.id, "Підтвердження старости. Перейдемо до справи...")  # дальше по циклу | проверка на старосту
                    time.sleep(1)
                    db_adding_storage["group"] = starosta_group
                    #add id group
                    for value in starosta_in_db:
                        for i in value:
                            id_dict["id_group"] = str(value[i])
                            #print("value group - ", value[i])
                            #print("id dict - ", id_dict["id_group"])
                            #print("type - ", type(id_dict["id_group"]))

                    markup3 = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                    markup3.add("Додати дедлайни", "Редагувати дедлайни","Мої поточні дедлайни")
                    msg = bot.send_message(message.chat.id, "Виберіть що хочете зробити", reply_markup=markup3)
                    bot.register_next_step_handler(msg, add_or_edit)
#checking on starosta. if user enter wrong group - he can't edit group, else - we go to nest step
                else:
                    bad_request = f"select Group_name from group_starosta where user_id ='{user_id}';"
                    cursor.execute(bad_request)
                    true_group_for_user = cursor.fetchall()
                    #print(true_group_for_user)
                    if true_group_for_user:
                        for value in true_group_for_user:
                            for i in value:
                                a = value[i]
                        bot.send_message(message.chat.id,
                                         f"Нажаль ви не можете редагувати групу *{starosta_group}*, так як ви староста групи- *{a}*",
                                         parse_mode='Markdown')
                    else:
                        bot.send_message(message.chat.id,
                                         f"Нажаль ви не можете редагувати групу *{starosta_group}*, так як ви не являєтеся старостою цієї групи",
                                         parse_mode='Markdown')
            else:
                bot.reply_to(message, "вашей группы нет в бд")  # влево по циклу
                time.sleep(1)
                markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard= True)
                markup.add("Додати мою групу", "Повернутися до головного меню")
                msg = bot.reply_to(message, "Бажаєте додати свою группу до бд?", reply_markup=markup)
                bot.register_next_step_handler(msg, add_to_db)
    except Exception as e:
        bot.send_message(message.chat.id, "Щось пішло не так. Про всяк випадок повідомляю, назва групи не може починатися на цифри або спеціальні знаки\nНатисніть /starosta та почніть процедуру наново")
        print(e.with_traceback())

def add_to_db(message): #adding data in db, start
    text = message.text
    if text == "Додати мою групу":
        group_db = bot.reply_to(message, "введіть вашу группу, яку ви хочете додати в базу.\nВажливо: Писати потрібно або латиницею або українською")
        bot.register_next_step_handler(group_db, group_to_db)
    elif text =="Повернутися до головного меню":
        bot.send_message(message.chat.id,"Вы вернулись в главное меню\nДля того чтобы начать работу с ботом нажмите /help или /start")
    else:
        bot.send_message(message.chat.id, "Для того чтобы начать работу с ботом нажмите /help или /start")

def group_to_db(message):
    groupname_to_db = message.text
    user_dict["name_group"] = groupname_to_db #adding info
    msg = bot.reply_to(message,f"Група записана, Тепер мені потрібно прізвище старости.\n*Важливо, ця група("+user_dict['name_group']+") буде закріплена саме за цим прізвищем та аккаунтом*", parse_mode='Markdown')
    bot.register_next_step_handler(msg, starosta_to_db)

def starosta_to_db(message):
    user_dict["Starosta"] = message.text
    user_dict["Tg"] = message.from_user.username # collect info about user
    user_dict["user_id"] = message.from_user.id
    user_dict["students"] = '1' #amount of users. default - 1( starosta)
    markup1 = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup1.add("Так, зберегти", "Ні, редагувати")
    msg = bot.send_message(message.chat.id, f"Ви, {user_dict['Starosta']}, староста групи {user_dict['name_group']},правильно?", reply_markup=markup1)
    bot.register_next_step_handler(msg, check_n_add)

def check_n_add(message):
    text = message.text
    if text == "Так, зберегти":
        #markup1 = types.ReplyKeyboardMarkup(one_time_keyboard=False)
        #bot.send_message(message.chat.id, "ви прошли тест", reply_markup=markup1)# send message but not reply, check this
        #далее по циклу - добавление группы в бд
        bot.send_message(message.chat.id, "Додаю вас до бд...")
        time.sleep(1)
        try:
            with connection.cursor() as cursor: # adding to group_starosta new item
                insert_to_group_starosta = f'insert into group_starosta(Group_name, Starosta, Tg, students, user_id) values ("{user_dict["name_group"]}","{user_dict["Starosta"]}","{user_dict["Tg"]}", {user_dict["students"]}, {user_dict["user_id"]});'
                cursor.execute(insert_to_group_starosta)
                connection.commit()
            bot.send_message(message.chat.id, "Вас було успішно додано")
            #editing deadlines n adding
        except Exception as ex:
            bot.send_message(message.chat.id, "Щось пішло не так, спробуйте ще раз")
            print(ex)

    elif text == "Ні, редагувати":
        msg = bot.send_message(message.chat.id, "Тоді почнемо спочатку. Введіть назву своєї групи")
        bot.register_next_step_handler(msg, starosta_start)     #return to start
    else:
        bot.send_message(message.chat.id, "Для того чтобы начать работу с ботом нажмите /help или /start")

def add_or_edit(message):
    if message.text == "Додати дедлайни": # or message.text == "Додати ще один дедлайн"
        bot.send_message(message.chat.id, "Ви вибрали додати дедлайни")

        db_adding_storage["group"] = user_dict["name_group"]
        time.sleep(1)
        markup4 = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup4.add("Повернутися назад")
        msg = bot.reply_to(message," Введіть назву предмету")
        bot.register_next_step_handler(msg,first_step_add) #recording subject

    elif message.text == "Редагувати дедлайни":
        bot.send_message(message.chat.id, "Гаразд, подивимось які дедлайни зараз існують")
        time.sleep(1)
        bot.send_message(message.chat.id, text=showing_deadlines())
        time.sleep(2)

        markup5 = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup5.add( "Відредагувати дедлайни", "Видалити дедлайн")
        msg = bot.send_message(message.chat.id, "Виберіть що хочете зробити", reply_markup=markup5)
        bot.register_next_step_handler(msg, edit_or_delete)

        # msg = bot.reply_to(message, "Напишіть ЛИШЕ ОДНУ цифру дедлайну, який хочете змінити.\n Достатньо '1,2,3' або так далі")
        # bot.register_next_step_handler(msg, first_step_correct)

    elif message.text == "Мої поточні дедлайни":
        bot.send_message(message.chat.id, "Гаразд, подивимось які дедлайни зараз існують")
        time.sleep(1)
        bot.send_message(message.chat.id, text=showing_deadlines())


def edit_or_delete(message):
    # markup5 = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    # markup5.add( "Відредагувати дедлайни", "Видалити дедлайн")
    # msg = bot.send_message(message.chat.id, "Виберіть що хочете зробити", reply_markup=markup5)
    # bot.register_next_step_handler(msg, edit_or_delete)
    if message.text == "Відредагувати дедлайни":
        # bot.send_message(message.chat.id, "Гаразд, подивимось які дедлайни зараз існують")
        time.sleep(1)
        # bot.send_message(message.chat.id, text=showing_deadlines())
        # time.sleep(2)
        msg = bot.reply_to(message, "Напишіть ЛИШЕ ОДНУ цифру дедлайну, який хочете змінити.\n Достатньо '1,2,3' або так далі")
        bot.register_next_step_handler(msg, first_step_correct)

    elif message.text == "Видалити дедлайн":
        # bot.send_message(message.chat.id, "Гаразд, подивимось які дедлайни зараз існують")
        time.sleep(1)
        # bot.send_message(message.chat.id, text=showing_deadlines())
        # time.sleep(2)
        msg = bot.reply_to(message,
                           "Напишіть ЛИШЕ ОДНУ цифру дедлайну, який хочете видалити.\n Достатньо '1,2,3' або так далі")
        bot.register_next_step_handler(msg, first_step_delete)


def first_step_delete(message):
    #bot.send_message(message.chat.id, text="all works correctly")
    db_adding_storage["group"] = user_dict["name_group"]
    text = message.text
    user_id = message.from_user.id
    if is_or_not(text):
        text = text.split(",")
        if more_or_not(text):
            text = withour_repeated(text)
            test_list = [int(i) for i in text]
            num = int(test_list[0])
            text = ','.join(i for i in text)
            bot.send_message(message.chat.id, text = "Ви хочете видалити такі дедлайни: №{0}".format(text))
            old_deadline_txt = ""
            global old_deadline
            old_deadline = []
            for j in all_deadlines[num - 1]:
                old_deadline.append(all_deadlines[num - 1].get(j))
                old_deadline_txt += str(all_deadlines[num - 1].get(j)) + " - "
            bot.send_message(message.chat.id, text=old_deadline_txt[:-2])
            global old_id
            old_id = find_id_in_db(old_deadline_txt.split(" - "), user_id)

            markup5 = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            markup5.add("Так, видалити", "Ні, не видаляти")
            msg = bot.send_message(message.chat.id, "Чи точно ви хочете видалити цей дедлайн?", reply_markup=markup5)
            bot.register_next_step_handler(msg, second_step_delete)
        else:
            bot.send_message(message.chat.id,
                             "Введені вами данні повинні бути цифрами та не перевищувати - {0}".format(max))
    else:
        bot.send_message(message.chat.id, "Введені вами данні повинні бути цифрами")

def second_step_delete(message):
    if message.text == "Так, видалити":
        try:
            with connection.cursor() as cursor:
                delete_query = f"delete from all_id where id ='{old_id[4]}';"
                cursor.execute(delete_query)
                connection.commit()
                bot.send_message(message.chat.id, text="Дедлайн видалено, операція успішна")
        except Exception as ex:
            bot.send_message(message.chat.id, text="Щось пішло не так, операція не вдалася")
            print(ex)

    elif message.text == "Ні, не видаляти":
        # bot.send_message(message.chat.id, "Гаразд, подивимось які дедлайни зараз існують")
        time.sleep(1)
        bot.send_message(message.chat.id, text="Для початку роботи з ботом натисніть /help або /start")
        # time.sleep(2)



def first_step_add(message):   #recording type of work
    db_adding_storage["subject"] = message.text
    markup4 = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup4.add("Повернутися назад")
    msg = bot.reply_to(message, "Дякую, тепер введіть тип роботи.\n"
                                "Приклад: \n"
                                "- Лабораторна робота №;\n"
                                "- Лаб №;\n"
                                "- Модульна контрольна робота №;\n"
                                "- МРК №\n"
                                "- Курсова\n"
                                "і так далі.")
    bot.register_next_step_handler(msg, second_step_add)

def second_step_add(message): # recording deadline
    db_adding_storage["type_work"] = message.text
    msg = bot.reply_to(message, "Дякую, тепер введіть дату делайну.\n"
                                "*Важливо:\n"
                                "Дата може бути записана ЛИШЕ у форматі: YYYY-MM-DD*", parse_mode='Markdown')
    bot.register_next_step_handler(msg, trird_step_add)

def trird_step_add(message): #confirm info
    db_adding_storage["deadline"] = message.text
    bot.send_message(message.chat.id, "Отже, для групи {} треба зробити {} з {} до {}".format(db_adding_storage["group"],db_adding_storage["type_work"],db_adding_storage["subject"],db_adding_storage["deadline"]))
    time.sleep(1)
    markup6 = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup6.add("Так, все вірно", "Ні, відредагувати")
    msg = bot.reply_to(message, "Все вірно?", reply_markup=markup6)
    bot.register_next_step_handler(msg, fourth_step_add)



def fourth_step_add(message): #adding to db info
    if message.text == "Так, все вірно":
        with connection.cursor() as cursor:
            """
            
            check_group_id = f"select Group_id from group_starosta where Group_name = '{db_adding_storage['group']}';"
            cursor.execute(check_group_id)
            group_in_db = cursor.fetchall()
            try:
                if group_in_db:
                    for value in group_in_db:
                        for i in value:
                            id_dict["id_group"] = str(value[i])
                            print("value group - ", value[i])
                            print('id dict - ', id_dict["id_group"])
                            print("type - ", type(id_dict["id_group"]))

                else:
                    bot.send_message(message.chat.id, "OOOOOPs, something with group identification")
            except Exception as ex:
                bot.send_message(message.chat.id, "OOOps, something with adding group")
                print(ex.with_traceback())
            
            """
            #check group_id


            # checking subject id & adding
            check_subject_id = f"select Subject_id from subjects where Subject = '{str(db_adding_storage['subject'])}';"
            cursor.execute(check_subject_id)
            subject_id_in_db = cursor.fetchall()
            if subject_id_in_db:
                for value in subject_id_in_db:
                    for i in value:
                        id_dict["id_subject"] = str(value[i])
                        #print("value subject - ", value[i])
                        #print("id dict - ", id_dict["id_subject"])
                        #print("type - ", type(id_dict["id_subject"]))
            else:
                try:
                    adding_subject = f"insert into subjects(subject) values ('{str(db_adding_storage['subject'])}');"
                    cursor.execute(adding_subject)
                    connection.commit()
                    bot.send_message(message.chat.id, "Предмет додано")

                    check_subject_id = f"select Subject_id from subjects where Subject = '{str(db_adding_storage['subject'])}';"
                    cursor.execute(check_subject_id)
                    subject_id_in_db = cursor.fetchall()
                    if subject_id_in_db:
                        for value in subject_id_in_db:
                            for i in value:
                                id_dict["id_subject"] = str(value[i])
                                #print("value subject - ", value[i])
                                #print("id dict - ", id_dict["id_subject"])
                                #print("type - ", type(id_dict["id_subject"]))
                except Exception as ex:
                    bot.send_message(message.chat.id, "Ooopss, щось пішло не так з додаванням предмету")
                    print(ex)


            #checking typework id
            check_typework_id = f"select type_work_id from works where type_work = '{str(db_adding_storage['type_work'])}';"
            cursor.execute(check_typework_id)
            typework_id_in_db = cursor.fetchall()
            if typework_id_in_db:
                for value in typework_id_in_db:
                    for i in value:
                        id_dict["id_typework"] = str(value[i])
                        #print("value typework - ", value[i])
                        #print("id dict - ", id_dict["id_typework"])
                        #print("type - ", type(id_dict["id_typework"]))

            else:
                try:
                    adding_typework = f"insert into works(type_work) values ('{str(db_adding_storage['type_work'])}');"
                    cursor.execute(adding_typework)
                    connection.commit()
                    bot.send_message(message.chat.id, "завдання додано")

                    check_typework_id = f"select type_work_id from works where type_work = '{str(db_adding_storage['type_work'])}';"
                    cursor.execute(check_typework_id)
                    typework_id_in_db = cursor.fetchall()
                    if typework_id_in_db:
                        for value in typework_id_in_db:
                            for i in value:
                                id_dict["id_typework"] = str(value[i])
                                #print("value typework - ", value[i])
                                #print("id dict - ", id_dict["id_typework"])
                                #print("type - ", type(id_dict["id_typework"]))

                except Exception as ex:
                    bot.send_message(message.chat.id, "Ooopss, щось пішло не так з доданням типу роботи")
                    print(ex)

            #checking id_deadline
            check_deadline_id = f"select deadline_id from deadlines where deadline = '{str(db_adding_storage['deadline'])}';"
            cursor.execute(check_deadline_id)
            deadline_id_in_db = cursor.fetchall()
            if deadline_id_in_db:
                for value in deadline_id_in_db:
                    for i in value:
                        id_dict["id_deadline"] = str(value[i])
                        #print("value deadline - ", value[i])
                        #print("id dict - ", id_dict["id_deadline"])
                        #print("type - ", type(id_dict["id_deadline"]))
            else:
                try:
                    adding_deadline = f"insert into deadlines(deadline) values('{str(db_adding_storage['deadline'])}');"
                    cursor.execute(adding_deadline)
                    connection.commit()
                    bot.send_message(message.chat.id, "дедлайн додано")

                    check_deadline_id = f"select deadline_id from deadlines where deadline = '{str(db_adding_storage['deadline'])}';"
                    cursor.execute(check_deadline_id)
                    deadline_id_in_db = cursor.fetchall()
                    if deadline_id_in_db:
                        for value in deadline_id_in_db:
                            for i in value:
                                id_dict["id_deadline"] = str(value[i])
                                #print("value deadline - ", value[i])
                                #print("id dict - ", id_dict["id_deadline"])
                                #print("type - ", type(id_dict["id_deadline"]))

                except Exception as ex:
                    bot.send_message(message.chat.id, "Ooopss, щось пішло не так з додаванням дедлайну")
                    print(ex)

            #adding all id to table with all id
            try:
                check_all_id = f"select * from all_id where g_id = '{id_dict['id_group']}' and s_id = '{id_dict['id_subject']}' and tow_id = '{id_dict['id_typework']}' and d_id = '{id_dict['id_deadline']}';"
                cursor.execute(check_all_id)
                all_id_in_db = cursor.fetchall()
                if all_id_in_db:
                    bot.send_message(message.chat.id, "Така комбінація вже існує. Почніть спочатку або відредагуйте дедлайн")
                else:
                    try:
                        adding_all = f"insert into all_id(g_id, s_id, tow_id, d_id) values ('{str(id_dict['id_group'])}','{str(id_dict['id_subject'])}','{str(id_dict['id_typework'])}','{str(id_dict['id_deadline'])}');"
                        cursor.execute(adding_all)
                        connection.commit()
                        #print("id_dict['id_group']%type - ", id_dict['id_group'],type(id_dict['id_group']))
                        #print("id_dict['id_subject']%type - ", id_dict['id_subject'], type(id_dict['id_subject']))
                        #print("id_dict['id_typework']%type - ", id_dict['id_typework'], type(id_dict['id_typework']))
                        #print("id_dict['id_deadline']%type - ", id_dict['id_deadline'], type(id_dict['id_deadline']))
                        bot.send_message(message.chat.id, "Додано до фінальної бд")

                    except Exception as ex:
                        bot.send_message(message.chat.id, "Ooopss, щось пішло не так з додаванням до фінальної бд")
                        print(ex)
            except Exception as ex:
                bot.send_message(message.chat.id, "Ooopss, щось пішло не так з додаванням у кінцеву бд")
                print(ex)
        bot.send_message(message.chat.id, "Операція успішна")
    ##############################################################################################################
    #printing existed deadlines
    elif message.text == "Ні, відредагувати":
        bot.send_message(message.chat.id, "Гаразд, подивимось які дедлайни зараз існують")
        time.sleep(0.5)
        bot.send_message(message.chat.id, text = showing_deadlines())
        msg = bot.reply_to(message, "Напишіть ЛИШЕ ОДНУ цифру дедлайну, який хочете змінити.\n Достатньо '1,2,3' або так далі")
        bot.register_next_step_handler(msg, first_step_correct)
    else:
        pass


def first_step_correct(message):
    db_adding_storage["group"] = user_dict["name_group"]
    text = message.text
    user_id = message.from_user.id
    if is_or_not(text):
        text = text.split(",")
        # print(enter)
        if more_or_not(text):
            text = withour_repeated(text)
            #print(new)
            test_list = [int(i) for i in text]
            num = int(test_list[0])
            #print(new2)
            text = ",".join(i for i in text)
            #print(text)
            bot.send_message(message.chat.id, text = "Ви хочете виправити такі дедлайни: {0}".format(text))

            old_deadline_txt = ""
            global old_deadline
            old_deadline = []
            for j in all_deadlines[num - 1]:
                old_deadline.append(all_deadlines[num - 1].get(j))
                old_deadline_txt += str(all_deadlines[num - 1].get(j)) + " - "
            bot.send_message(message.chat.id, text=old_deadline_txt[:-2])
            global old_id
            old_id = find_id_in_db(old_deadline_txt.split(" - "), user_id)
            #print("func start")
            bot.send_message(message.chat.id, " Введіть новий дедлай по прикладу вище: ")
            bot.register_next_step_handler(message, second_step_correct)

            # for i in test_list:
            #     old_deadline_txt = ""
            #     global old_deadline
            #     old_deadline = []
            #     for j in all_deadlines[i-1]:
            #         old_deadline.append(all_deadlines[i - 1].get(j))
            #         old_deadline_txt+= str(all_deadlines[i-1].get(j))+" - "
            #     bot.send_message(message.chat.id, text=old_deadline_txt[:-2])
            #     old_id = find_id_in_db(old_deadline_txt.split(" - "), user_id)
            #     print("func start")
            #     a = 1
            #     if a>0:
            #         bot.send_message(message.chat.id, " Введіть новий дедлай по прикладу вище: ")
            #         bot.register_next_step_handler(message, second_step_correct)
            #         a-=100
            #     print("func end")
            #     print("jkfnkjf"*10)
            # bot.send_message(message.chat.id, text = "Усі дедлайни були змінені")
        else:
            bot.send_message(message.chat.id, "Введені вами данні повинні бути цифрами та не перевищувати - {0}".format(max))
    else:
        bot.send_message(message.chat.id, "Введені вами данні повинні бути цифрами")

# def middle_step_correct(message):
#     bot.send_message(message.chat.id, " Введіть новий дедлай по прикладу вище: ")
#     bot.register_next_step_handler(message, second_step_correct)

def second_step_correct(message):
    #print("second_step_correct start")
    #print("old_id - ", old_id)
    new_deadline = message.text.split(" - ")
    #new_deadline = message
    #print("8new deadline - ",new_deadline)
    user_id = message.from_user.id
    new_id = find_id_in_db(new_deadline,user_id)
    if type(new_id) == list:
        #update data
        # print(new_deadline[0], new_deadline[1],new_deadline[2],new_deadline[3])
        # print("9text - ",new_id)
        with connection.cursor() as cursor:
            edit_query = f"update all_id set g_id = '{new_id[0]}', s_id = '{new_id[1]}', tow_id = '{new_id[2]}', d_id ='{new_id[3]}' where id = '{old_id[4]}';"
            cursor.execute(edit_query)
            connection.commit()
            bot.send_message(message.chat.id, text = "Новий дедлайн додано, операція успішна")
            # return "Новий дедлайн додано, операція успішна"
    elif type(new_id) == str:
        #bot.send_message(message.chat.id, text = new_id)
        return new_id
    else:
        bot.send_message(message.chat.id, text = "Щось пішло не так, операція не вдалася")
        #return "Щось пішло не так, операція не вдалася"

def showing_deadlines():
    with connection.cursor() as cursor:  #
        group_in_sql = f"select * from group_starosta where Group_name = '{db_adding_storage['group']}';"  # сhecking group in db
        cursor.execute(group_in_sql)
        group_in_table = cursor.fetchall()
        if group_in_table:
            with connection.cursor() as cursor:  # here we get the entire table with data from the database
                group_table = f"select \
                                        Group_name, Subject, type_work, deadline\
                                        from all_id \
                                        inner join group_starosta on all_id.g_id = group_starosta.Group_id and Group_name = '{db_adding_storage['group']}'\
                                        inner join subjects on all_id.s_id = subjects.Subject_id\
                                        inner join works on all_id.tow_id = works.type_work_id\
                                        inner join deadlines on all_id.d_id = deadlines.deadline_id\
                                        order by deadline"
                cursor.execute(group_table)
                rows = cursor.fetchall()
                # print(rows)
                global max  # for next step - editing
                max = len(rows)
                global all_deadlines
                all_deadlines = rows
                if not rows:
                    text = f"Гарні новини!\nНаразі у бд немає жодного запису стосовно твоєї групи - {db_adding_storage['group']}\nТож додай дедлайни до бази"
                    return text
                else:
                    # print(rows)
                    t = 1
                    table = ""
                    for row in rows:

                        # print(row)
                        table += str(t) + ") "
                        for i in row:
                            table += str(row.get(i)) + " - "
                        t += 1
                        table = table[:-2]
                        table += "\n"
                    text = "Твої дедлайни: \n" + table
                    return text
        else:
            text = "вашей группы нет в бд, попробуйте еще раз нажав /starosta"
            return text


def is_or_not(text):
    list_digits = text.split(",")
    flag = True
    for i in list_digits:
        if i.isdigit():
            continue
        else:
            flag = False
            break
    return flag

def more_or_not(text):
    flag = True
    for i in text:
        if int(i) > max and int(i) > 0:
            flag = False
            break
        else:
            continue
    return flag

def the_same_is(text):
    flag = True
    for i in range(len(text)-1):
        for j in range(i+1, len(text)):
            if text[i] == text[j]:
                flag = False
                return flag
    return flag

def withour_repeated(text):
    new_text = []
    for item in text:
        if item not in new_text:
            new_text.append(item)
    return new_text


def find_id_in_db(deadline_list, user_id):
    new_list_id = []

    with connection.cursor() as cursor:
        #print("10 - group in id - ", deadline_list[0])
        check_group_id = f"select Group_id from group_starosta where Group_name = '{deadline_list[0]}';"
        cursor.execute(check_group_id)
        group_in_db = cursor.fetchall()
        if group_in_db:
            # user_id = message.from_user.id
            starosta_true = f"select Group_id from group_starosta where user_id ='{user_id}' and Group_name = '{deadline_list[0]}';"
            cursor.execute(starosta_true)
            starosta_is_true = cursor.fetchall()
            if starosta_is_true:
                try:
                    for value in group_in_db:
                        for i in value:
                            new_list_id.append(str(value[i]))
                            #print("group", new_list_id)
                            id_from_all_id["id_g"] = str(value[i])
                            # print("value group - ", value[i])
                            # print('id dict - ', id_dict["id_group"])
                            # print("type - ", type(id_dict["id_group"]))
                except Exception as ex:
                    print(ex.with_traceback())
                    return "Ви не можете додавати дедлай до цієї групи"
        # chek subjects
        #print("10subject in id- ", deadline_list[1])
        check_subject_id = f"select Subject_id from subjects where Subject = '{str(deadline_list[1])}';"
        cursor.execute(check_subject_id)
        subject_id_in_db = cursor.fetchall()
        if subject_id_in_db:
            for value in subject_id_in_db:
                for i in value:
                    new_list_id.append(str(value[i]))
                    #print("11group+subj", new_list_id)
                    id_from_all_id["id_s"] = str(value[i])
                    # print("value subject - ", value[i])
                    # print("id dict - ", id_dict["id_subject"])
                    # print("type - ", type(id_dict["id_subject"]))
        else:
            try:
                adding_subject = f"insert into subjects(subject) values ('{str(deadline_list[1])}');"
                cursor.execute(adding_subject)
                connection.commit()
                # bot.send_message(message.chat.id, "Ви додали новий предмет - {0}".format(deadline_list[1]))

                check_subject_id = f"select Subject_id from subjects where Subject = '{str(deadline_list[1])}';"
                cursor.execute(check_subject_id)
                subject_id_in_db = cursor.fetchall()
                if subject_id_in_db:
                    for value in subject_id_in_db:
                        for i in value:
                            new_list_id.append(str(value[i]))
                            #print("12group+subj", new_list_id)
                            id_from_all_id["id_s"] = str(value[i])
                            # print("value subject - ", value[i])
                            # print("id dict - ", id_dict["id_subject"])
                            # print("type - ", type(id_dict["id_subject"]))
            except Exception as ex:
                print(ex)
                return "Ooopss, щось пішло не так з додаванням предмету"

        # checking typework id
        #print("13tow in id - ", deadline_list[2])
        check_typework_id = f"select type_work_id from works where type_work = '{str(deadline_list[2])}';"
        cursor.execute(check_typework_id)
        typework_id_in_db = cursor.fetchall()
        if typework_id_in_db:
            for value in typework_id_in_db:
                for i in value:
                    new_list_id.append(str(value[i]))
                    #print("14group+subj+tow", new_list_id)
                    id_from_all_id["id_tow"] = str(value[i])
                    # print("value typework - ", value[i])
                    # print("id dict - ", id_dict["id_typework"])
                    # print("type - ", type(id_dict["id_typework"]))

        else:
            try:
                adding_typework = f"insert into works(type_work) values ('{str(deadline_list[2])}');"
                cursor.execute(adding_typework)
                connection.commit()
                # bot.send_message(message.chat.id, "Ви додали новий тип роботи - {0}".format(deadline_list[2]))

                check_typework_id = f"select type_work_id from works where type_work = '{str(deadline_list[2])}';"
                cursor.execute(check_typework_id)
                typework_id_in_db = cursor.fetchall()
                if typework_id_in_db:
                    for value in typework_id_in_db:
                        for i in value:
                            new_list_id.append(str(value[i]))
                            #print("15group+subj+tow", new_list_id)
                            id_from_all_id["id_tow"] = str(value[i])
                            # print("value typework - ", value[i])
                            # print("id dict - ", id_dict["id_typework"])
                            # print("type - ", type(id_dict["id_typework"]))
            except Exception as ex:
                print(ex)
                return "Ooopss, щось пішло не так з доданням типу роботи"

        # checking id_deadline
        # print("16group - ", deadline_list[3])
        check_deadline_id = f"select deadline_id from deadlines where deadline = '{str(deadline_list[3])}';"
        cursor.execute(check_deadline_id)
        deadline_id_in_db = cursor.fetchall()
        if deadline_id_in_db:
            for value in deadline_id_in_db:
                for i in value:
                    new_list_id.append(str(value[i]))
                    #print("16group+subj+tow+deadline", new_list_id)
                    id_from_all_id["id_d"] = str(value[i])
                    # print("value deadline - ", value[i])
                    # print("id dict - ", id_dict["id_deadline"])
                    # print("type - ", type(id_dict["id_deadline"]))
        else:
            try:
                adding_deadline = f"insert into deadlines(deadline) values('{str(deadline_list[3])}');"
                cursor.execute(adding_deadline)
                connection.commit()
                # bot.send_message(message.chat.id, "Ви додали новий дедлайн - {0}".format(deadline_list[3]))

                check_deadline_id = f"select deadline_id from deadlines where deadline = '{str(deadline_list[3])}';"
                cursor.execute(check_deadline_id)
                deadline_id_in_db = cursor.fetchall()
                if deadline_id_in_db:
                    for value in deadline_id_in_db:
                        for i in value:
                            new_list_id.append(str(value[i]))
                            #print("17group+subj+tow+deadline", new_list_id)
                            id_from_all_id["id_d"] = str(value[i])
                            # print("value deadline - ", value[i])
                            # print("id dict - ", id_dict["id_deadline"])
                            # print("type - ", type(id_dict["id_deadline"]))

            except Exception as ex:
                print(ex)
                return "Ooopss, щось пішло не так з додаванням дедлайну"

        # find id
        #print("18id-dict - ", id_dict)
        #print("18,5 text_list -", new_list_id)
        #print("18,75 - old_deadlines - ", old_deadlines)
        #old_deadlines_id = find_id_in_db(old_deadline, user_id)
        #print("18,8 - old_deadlines_id - ", old_deadlines_id)
        check_id = f"select id from all_id where g_id = '{new_list_id[0]}' and s_id = '{new_list_id[1]}' and tow_id = '{new_list_id[2]}' and d_id = '{new_list_id[3]}';"
        cursor.execute(check_id)
        indentificate = cursor.fetchall()
        #print("19indentificate - ", indentificate)
        if indentificate:
            for row in indentificate:
                for id in row:
                    new_list_id.append(str(row[id]))
                    #print("20group+subj+tow+deadline+id", new_list_id)
                    id_from_all_id["id"] = str(value[i])

    return new_list_id



if __name__ == '__main__':
    bot.infinity_polling()