from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import mysql.connector
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime

# Database connection configuration
db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '1111',
    'database': 'Mydb'
}

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'Sogoyn.p@gmail.com'
EMAIL_PASSWORD = 'Mafado_37Arm'

# Connect to the MySQL database
def connect_to_db():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# States for ConversationHandler
MAIN_MENU, INCOME, EXPENSES, CATEGORIES, REPORTS, SETTINGS, THEME, LANGUAGE, RESET_SETTINGS = range(9)
ADD_INCOME_AMOUNT, ADD_INCOME_CATEGORY, ADD_INCOME_DESCRIPTION = range(9, 12)
ADD_EXPENSE_AMOUNT, ADD_EXPENSE_CATEGORY, ADD_EXPENSE_DESCRIPTION = range(12, 15)
ADD_CATEGORY_NAME, EDIT_CATEGORY_ID, EDIT_CATEGORY_NAME, DELETE_CATEGORY_ID = range(15, 19)

translations = {
    'ru': {
        'main_menu': "🌟 *Главное меню* 🌟\nВыберите действие:",
        'income_menu': "📈 *Меню доходов* 📈\nВыберите действие:",
        'expenses_menu': "📉 *Меню расходов* 📉\nВыберите действие:",
        'categories_menu': "📂 *Меню категорий* 📂\nВыберите действие:",
        'reports_menu': "📊 *Меню отчетов* 📊\nВыберите действие:",
        'settings_menu': "⚙️ *Меню настроек* ⚙️\nВыберите действие:",
        'theme_settings': "🎨 *Оформление темы* 🎨\nВыберите тему:",
        'language_settings': "🌐 *Изменить язык* 🌐\nВыберите язык:",
        'reset_settings': "✅ Настройки сброшены к значениям по умолчанию.",
        'add_income': "💵 Введите сумму дохода:",
        'add_income_category': "📂 Введите категорию дохода:",
        'add_income_description': "📝 Введите описание дохода:",
        'add_expense': "💸 Введите сумму расхода:",
        'add_expense_category': "📂 Введите категорию расхода:",  # Добавлено
        'add_expense_description': "📝 Введите описание расхода:",  # Добавлено
        'add_category': "📝 Введите название категории:",
        'edit_category': "📝 Введите ID категории, которую хотите изменить:",
        'delete_category': "📝 Введите ID категории, которую хотите удалить:",
        'view_categories': "📂 *Категории* 📂\n",
        'view_income': "📊 *Доходы* 📊\n",
        'view_expenses': "📉 *Расходы* 📉\n",
        'generate_report': "✅ Отчет успешно сохранен в форматах PDF и Excel.",
        'send_report_email': "📧 Введите ваш email для отправки отчета:",
        'handle_email_input': "✅ Отчет успешно отправлен на email:",
        'apply_theme_light': "✅ Светлая тема применена.",
        'apply_theme_dark': "✅ Темная тема применена.",
        'apply_language_ru': "✅ Язык изменен на русский.",
        'apply_language_en': "✅ Language changed to English.",
    },
    'en': {
        'main_menu': "🌟 *Main Menu* 🌟\nChoose an action:",
        'income_menu': "📈 *Income Menu* 📈\nChoose an action:",
        'expenses_menu': "📉 *Expenses Menu* 📉\nChoose an action:",
        'categories_menu': "📂 *Categories Menu* 📂\nChoose an action:",
        'reports_menu': "📊 *Reports Menu* 📊\nChoose an action:",
        'settings_menu': "⚙️ *Settings Menu* ⚙️\nChoose an action:",
        'theme_settings': "🎨 *Theme Settings* 🎨\nChoose a theme:",
        'language_settings': "🌐 *Change Language* 🌐\nChoose a language:",
        'reset_settings': "✅ Settings have been reset to default.",
        'add_income': "💵 Enter the income amount:",
        'add_income_category': "📂 Enter the income category:",
        'add_income_description': "📝 Enter the income description:",
        'add_expense': "💸 Enter the expense amount:",
        'add_expense_category': "📂 Enter the expense category:",  # Добавлено
        'add_expense_description': "📝 Enter the expense description:",  # Добавлено
        'add_category': "📝 Enter the category name:",
        'edit_category': "📝 Enter the category ID you want to edit:",
        'delete_category': "📝 Enter the category ID you want to delete:",
        'view_categories': "📂 *Categories* 📂\n",
        'view_income': "📊 *Income* 📊\n",
        'view_expenses': "📉 *Expenses* 📉\n",
        'generate_report': "✅ Report successfully saved in PDF and Excel formats.",
        'send_report_email': "📧 Enter your email to send the report:",
        'handle_email_input': "✅ Report successfully sent to email:",
        'apply_theme_light': "✅ Light theme applied.",
        'apply_theme_dark': "✅ Dark theme applied.",
        'apply_language_ru': "✅ Language changed to Russian.",
        'apply_language_en': "✅ Language changed to English.",
    }
}

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')  # По умолчанию русский
    theme = context.user_data.get('theme', 'light')  # По умолчанию светлая тема
    keyboard = [
        ['💰 Доходы', '💸 Расходы'],
        ['📂 Категории', '📊 Отчеты'],
        ['⚙️ Настройки']
    ]
    if language == 'en':
        keyboard = [
            ['💰 Income', '💸 Expenses'],
            ['📂 Categories', '📊 Reports'],
            ['⚙️ Settings']
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        translations[language]['main_menu'],
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return MAIN_MENU

# Income menu
async def income_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    keyboard = [
        ['➕ Добавить доход', '👀 Просмотреть доход'],
        ['🔙 Назад']
    ]
    if language == 'en':
        keyboard = [
            ['➕ Add Income', '👀 View Income'],
            ['🔙 Back']
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        translations[language]['income_menu'],
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return INCOME

# Add income - step 1: запрос суммы дохода
async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    await update.message.reply_text(translations[language]['add_income'])
    return ADD_INCOME_AMOUNT

# Add income - step 2: обработка суммы дохода
async def add_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        if amount <= 0:
            language = context.user_data.get('language', 'ru')
            await update.message.reply_text("❌ Сумма должна быть больше нуля. Введите корректную сумму.")
            return ADD_INCOME_AMOUNT
        context.user_data['income_amount'] = amount
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text(translations[language]['add_income_category'])
        return ADD_INCOME_CATEGORY
    except ValueError:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Неверный формат суммы. Введите число.")
        return ADD_INCOME_AMOUNT

# Add income - step 3: обработка категории дохода
async def add_income_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')  # Получаем язык из context.user_data
    await update.message.reply_text(
        translations.get(language, {}).get('add_income_category', 'Введите категорию дохода:')
    )
    category = update.message.text
    context.user_data['income_category'] = category
    await update.message.reply_text(translations[language]['add_income_description'])
    return ADD_INCOME_DESCRIPTION

# Add income - step 4: обработка описания и сохранение в базу данных
async def add_income_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    amount = context.user_data.get('income_amount')
    category = context.user_data.get('income_category')

    conn = connect_to_db()
    if conn is None:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Ошибка подключения к базе данных.")
        return INCOME

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO incomes (date, amount, category, description) VALUES (%s, %s, %s, %s)",
            (datetime.now().date(), amount, category, description)
        )
        conn.commit()
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("✅ Доход успешно добавлен!")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ Ошибка при добавлении дохода: {err}")
    finally:
        cursor.close()
        conn.close()

    return INCOME

# View income
async def view_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = connect_to_db()
    if conn is None:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Ошибка подключения к базе данных.")
        return INCOME

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incomes")
    income_data = cursor.fetchall()
    cursor.close()
    conn.close()

    if income_data:
        response = translations[context.user_data.get('language', 'ru')]['view_income']
        for row in income_data:
            response += (
                f"🔹 *ID*: {row[0]}\n"
                f"📅 *Дата*: {row[1]}\n"
                f"💰 *Сумма*: {row[2]}\n"
                f"📂 *Категория*: {row[3]}\n"
                f"📝 *Описание*: {row[4]}\n\n"
            )
    else:
        response = "❌ Данные о доходах отсутствуют."

    await update.message.reply_text(response, parse_mode="Markdown")
    return INCOME

# Expenses menu
async def expenses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    keyboard = [
        ['➕ Добавить расход', '👀 Просмотреть расходы'],
        ['🔙 Назад']
    ]
    if language == 'en':
        keyboard = [
            ['➕ Add Expense', '👀 View Expenses'],
            ['🔙 Back']
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        translations[language]['expenses_menu'],
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return EXPENSES

# Add expense - step 1: запрос суммы расхода
async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    await update.message.reply_text(translations[language]['add_expense'])
    return ADD_EXPENSE_AMOUNT

# Add expense - step 2: обработка суммы расхода
async def add_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        if amount <= 0:
            language = context.user_data.get('language', 'ru')
            await update.message.reply_text("❌ Сумма должна быть больше нуля. Введите корректную сумму.")
            return ADD_EXPENSE_AMOUNT
        context.user_data['expense_amount'] = amount
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text(translations[language]['add_expense_category'])  # Теперь ключ существует
        return ADD_EXPENSE_CATEGORY
    except ValueError:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Неверный формат суммы. Введите число.")
        return ADD_EXPENSE_AMOUNT

# Add expense - step 3: обработка категории расхода
async def add_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    context.user_data['expense_category'] = category
    language = context.user_data.get('language', 'ru')
    await update.message.reply_text(translations[language]['add_expense_description'])
    return ADD_EXPENSE_DESCRIPTION

# Add expense - step 4: обработка описания и сохранение в базу данных
async def add_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    amount = context.user_data.get('expense_amount')
    category = context.user_data.get('expense_category')

    conn = connect_to_db()
    if conn is None:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Ошибка подключения к базе данных.")
        return EXPENSES

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO expenses (date, amount, category, description) VALUES (%s, %s, %s, %s)",
            (datetime.now().date(), amount, category, description)
        )
        conn.commit()
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("✅ Расход успешно добавлен!")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ Ошибка при добавлении расхода: {err}")
    finally:
        cursor.close()
        conn.close()

    return EXPENSES

# View expenses
async def view_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = connect_to_db()
    if conn is None:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Ошибка подключения к базе данных.")
        return EXPENSES

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    expenses_data = cursor.fetchall()
    cursor.close()
    conn.close()

    if expenses_data:
        response = translations[context.user_data.get('language', 'ru')]['view_expenses']
        for row in expenses_data:
            response += (
                f"🔹 *ID*: {row[0]}\n"
                f"📅 *Дата*: {row[1]}\n"
                f"💰 *Сумма*: {row[2]}\n"
                f"📂 *Категория*: {row[3]}\n"
                f"📝 *Описание*: {row[4]}\n\n"
            )
    else:
        response = "❌ Данные о расходах отсутствуют."

    await update.message.reply_text(response, parse_mode="Markdown")
    return EXPENSES

# Categories menu
async def categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    keyboard = [
        ['➕ Добавить категорию', '🗑 Удалить категорию'],
        ['✏️ Изменить категорию', '👀 Просмотреть категории'],
        ['🔙 Назад']
    ]
    if language == 'en':
        keyboard = [
            ['➕ Add Category', '🗑 Delete Category'],
            ['✏️ Edit Category', '👀 View Categories'],
            ['🔙 Back']
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        translations[language]['categories_menu'],
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return CATEGORIES

# Add category - step 1: запрос названия категории
async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    await update.message.reply_text(translations[language]['add_category'])
    return ADD_CATEGORY_NAME

# Add category - step 2: сохранение категории в базу данных
async def add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category_name = update.message.text

    conn = connect_to_db()
    if conn is None:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Ошибка подключения к базе данных.")
        return CATEGORIES

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO categories (name) VALUES (%s)",
            (category_name,)
        )
        conn.commit()
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("✅ Категория успешно добавлена!")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ Ошибка при добавлении категории: {err}")
    finally:
        cursor.close()
        conn.close()

    return CATEGORIES

# Edit category - step 1: запрос ID категории для изменения
async def edit_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    await update.message.reply_text(translations[language]['edit_category'])
    return EDIT_CATEGORY_ID

# Edit category - step 2: обработка ID категории
async def edit_category_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        category_id = int(update.message.text)
        context.user_data['edit_category_id'] = category_id
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text(translations[language]['edit_category_name'])
        return EDIT_CATEGORY_NAME
    except ValueError:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Неверный формат ID. Введите число.")
        return EDIT_CATEGORY_ID

# Edit category - step 3: обработка нового названия и обновление в базе данных
async def edit_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    category_id = context.user_data.get('edit_category_id')

    conn = connect_to_db()
    if conn is None:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Ошибка подключения к базе данных.")
        return CATEGORIES

    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE categories SET name = %s WHERE id = %s",
            (new_name, category_id)
        )
        conn.commit()
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("✅ Категория успешно изменена!")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"❌ Ошибка при изменении категории: {err}")
    finally:
        cursor.close()
        conn.close()

    return CATEGORIES

# Delete category - step 1: запрос ID категории для удаления
async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    await update.message.reply_text(translations[language]['delete_category'])
    return DELETE_CATEGORY_ID

# Delete category - step 2: обработка ID категории и удаление из базы данных
async def delete_category_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        category_id = int(update.message.text)

        conn = connect_to_db()
        if conn is None:
            language = context.user_data.get('language', 'ru')
            await update.message.reply_text("❌ Ошибка подключения к базе данных.")
            return CATEGORIES

        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM categories WHERE id = %s",
                (category_id,)
            )
            conn.commit()
            language = context.user_data.get('language', 'ru')
            await update.message.reply_text("✅ Категория успешно удалена!")
        except mysql.connector.Error as err:
            await update.message.reply_text(f"❌ Ошибка при удалении категории: {err}")
        finally:
            cursor.close()
            conn.close()

    except ValueError:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Неверный формат ID. Введите число.")
        return DELETE_CATEGORY_ID

    return CATEGORIES

# View categories
async def view_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = connect_to_db()
    if conn is None:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Ошибка подключения к базе данных.")
        return CATEGORIES

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    categories_data = cursor.fetchall()
    cursor.close()
    conn.close()

    if categories_data:
        response = translations[context.user_data.get('language', 'ru')]['view_categories']
        for row in categories_data:
            response += f"🔹 *ID*: {row[0]}\n📝 *Название*: {row[1]}\n\n"
    else:
        response = "❌ Данные о категориях отсутствуют."

    await update.message.reply_text(response, parse_mode="Markdown")
    return CATEGORIES

# Reports menu
async def reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    keyboard = [
        ['📧 Отправить отчет на email', '💾 Сохранить отчет (PDF, Excel)'],
        ['🔙 Назад']
    ]
    if language == 'en':
        keyboard = [
            ['📧 Send Report via Email', '💾 Save Report (PDF, Excel)'],
            ['🔙 Back']
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        translations[language]['reports_menu'],
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return REPORTS

# Save report as PDF
def save_report_as_pdf(data, filename="report.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica", 12)
    y = 750
    for row in data:
        line = f"ID: {row[0]}, Дата: {row[1]}, Сумма: {row[2]}, Категория: {row[3]}, Описание: {row[4]}"
        c.drawString(50, y, line)
        y -= 20
        if y < 50:
            c.showPage()
            y = 750
            c.setFont("Helvetica", 12)
    c.save()

# Save report as Excel
def save_report_as_excel(data, filename="report.xlsx"):
    df = pd.DataFrame(data, columns=["ID", "Дата", "Сумма", "Категория", "Описание"])
    df.to_excel(filename, index=False)

# Send email with attachment
def send_email_with_attachment(to_email, subject, body, attachment_path):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with open(attachment_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={os.path.basename(attachment_path)}'
        )
        msg.attach(part)

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Generate and save report
async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = connect_to_db()
    if conn is None:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Ошибка подключения к базе данных.")
        return REPORTS

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incomes")
    incomes = cursor.fetchall()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()

    if not incomes and not expenses:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Данные для отчета отсутствуют.")
        return REPORTS

    save_report_as_pdf(incomes + expenses, "financial_report.pdf")
    await update.message.reply_document(document=open("financial_report.pdf", "rb"))
    os.remove("financial_report.pdf")

    save_report_as_excel(incomes + expenses, "financial_report.xlsx")
    await update.message.reply_document(document=open("financial_report.xlsx", "rb"))
    os.remove("financial_report.xlsx")

    language = context.user_data.get('language', 'ru')
    await update.message.reply_text(translations[language]['generate_report'])
    return REPORTS

# Send report via email
async def send_report_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    await update.message.reply_text(translations[language]['send_report_email'])
    return REPORTS

# Handle email input
async def handle_email_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_email = update.message.text

    conn = connect_to_db()
    if conn is None:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Ошибка подключения к базе данных.")
        return REPORTS

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incomes")
    incomes = cursor.fetchall()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()

    if not incomes and not expenses:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Данные для отчета отсутствуют.")
        return REPORTS

    save_report_as_pdf(incomes + expenses, "financial_report.pdf")

    if send_email_with_attachment(
        user_email,
        "Ваш финансовый отчет",
        "Пожалуйста, найдите вложенный финансовый отчет.",
        "financial_report.pdf"
    ):
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text(f"✅ Отчет успешно отправлен на email: {user_email}.")
    else:
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text("❌ Ошибка при отправке отчета на email.")

    os.remove("financial_report.pdf")
    return REPORTS

# Settings menu
async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    keyboard = [
        ['🎨 Оформление темы', '🌐 Изменить язык'],
        ['🔄 Сброс настроек', '🔙 Назад']
    ]
    if language == 'en':
        keyboard = [
            ['🎨 Theme Settings', '🌐 Change Language'],
            ['🔄 Reset Settings', '🔙 Back']
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        translations[language]['settings_menu'],
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SETTINGS

# Theme settings
async def theme_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    keyboard = [
        ['🌞 Светлая тема', '🌚 Темная тема'],
        ['🔙 Назад']
    ]
    if language == 'en':
        keyboard = [
            ['🌞 Light Theme', '🌚 Dark Theme'],
            ['🔙 Back']
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        translations[language]['theme_settings'],
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return THEME

# Apply theme
async def apply_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    theme = update.message.text
    if theme == '🌞 Светлая тема' or theme == '🌞 Light Theme':
        context.user_data['theme'] = 'light'
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text(translations[language]['apply_theme_light'])
    elif theme == '🌚 Темная тема' or theme == '🌚 Dark Theme':
        context.user_data['theme'] = 'dark'
        language = context.user_data.get('language', 'ru')
        await update.message.reply_text(translations[language]['apply_theme_dark'])
    return SETTINGS

# Language settings
async def language_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'ru')
    theme = context.user_data.get('theme', 'light')
    keyboard = [
        ['🇷🇺 Русский', '🇺🇸 Английский'],
        ['🔙 Назад']
    ]
    if language == 'en':
        keyboard = [
            ['🇷🇺 Russian', '🇺🇸 English'],
            ['🔙 Back']
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        translations[language]['language_settings'],
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return LANGUAGE

# Apply language
async def apply_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = update.message.text
    if language == '🇷🇺 Русский' or language == '🇷🇺 Russian':
        context.user_data['language'] = 'ru'
        await update.message.reply_text(translations['ru']['apply_language_ru'])
    elif language == '🇺🇸 Английский' or language == '🇺🇸 English':
        context.user_data['language'] = 'en'
        await update.message.reply_text(translations['en']['apply_language_en'])
    return SETTINGS

# Reset settings
async def reset_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    language = context.user_data.get('language', 'ru')
    await update.message.reply_text(translations[language]['reset_settings'])
    return SETTINGS

# Main function to run the bot
def main():
    # Замените 'YOUR_BOT_TOKEN' на ваш токен
    application = Application.builder().token "8138334469:AAHajB4lCWU9MWVOF6oBVF5Rkcc-3wyGXGc"

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Text("💰 Доходы") | filters.Text("💰 Income"), income_menu),
                MessageHandler(filters.Text("💸 Расходы") | filters.Text("💸 Expenses"), expenses_menu),
                MessageHandler(filters.Text("📂 Категории") | filters.Text("📂 Categories"), categories_menu),
                MessageHandler(filters.Text("📊 Отчеты") | filters.Text("📊 Reports"), reports_menu),
                MessageHandler(filters.Text("⚙️ Настройки") | filters.Text("⚙️ Settings"), settings_menu),
            ],
            INCOME: [
                MessageHandler(filters.Text("➕ Добавить доход") | filters.Text("➕ Add Income"), add_income),
                MessageHandler(filters.Text("👀 Просмотреть доход") | filters.Text("👀 View Income"), view_income),
                MessageHandler(filters.Text("🔙 Назад") | filters.Text("🔙 Back"), start),
            ],
            ADD_INCOME_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_income_amount),
            ],
            ADD_INCOME_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_income_category),
            ],
            ADD_INCOME_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_income_description),
            ],
            EXPENSES: [
                MessageHandler(filters.Text("➕ Добавить расход") | filters.Text("➕ Add Expense"), add_expense),
                MessageHandler(filters.Text("👀 Просмотреть расходы") | filters.Text("👀 View Expenses"), view_expenses),
                MessageHandler(filters.Text("🔙 Назад") | filters.Text("🔙 Back"), start),
            ],
            ADD_EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_amount),
            ],
            ADD_EXPENSE_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_category),
            ],
            ADD_EXPENSE_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_description),
            ],
            CATEGORIES: [
                MessageHandler(filters.Text("➕ Добавить категорию") | filters.Text("➕ Add Category"), add_category),
                MessageHandler(filters.Text("🗑 Удалить категорию") | filters.Text("🗑 Delete Category"), delete_category),
                MessageHandler(filters.Text("✏️ Изменить категорию") | filters.Text("✏️ Edit Category"), edit_category),
                MessageHandler(filters.Text("👀 Просмотреть категории") | filters.Text("👀 View Categories"), view_categories),
                MessageHandler(filters.Text("🔙 Назад") | filters.Text("🔙 Back"), start),
            ],
            ADD_CATEGORY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name),
            ],
            EDIT_CATEGORY_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_category_id),
            ],
            EDIT_CATEGORY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_category_name),
            ],
            DELETE_CATEGORY_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_category_id),
            ],
            REPORTS: [
                MessageHandler(filters.Text("💾 Сохранить отчет (PDF, Excel)") | filters.Text("💾 Save Report (PDF, Excel)"), generate_report),
                MessageHandler(filters.Text("📧 Отправить отчет на email") | filters.Text("📧 Send Report via Email"), send_report_email),
                MessageHandler(filters.Text("🔙 Назад") | filters.Text("🔙 Back"), start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email_input),
            ],
            SETTINGS: [
                MessageHandler(filters.Text("🎨 Оформление темы") | filters.Text("🎨 Theme Settings"), theme_settings),
                MessageHandler(filters.Text("🌐 Изменить язык") | filters.Text("🌐 Change Language"), language_settings),
                MessageHandler(filters.Text("🔄 Сброс настроек") | filters.Text("🔄 Reset Settings"), reset_settings),
                MessageHandler(filters.Text("🔙 Назад") | filters.Text("🔙 Back"), start),
            ],
            THEME: [
                MessageHandler(filters.Text("🌞 Светлая тема") | filters.Text("🌞 Light Theme"), apply_theme),
                MessageHandler(filters.Text("🌚 Темная тема") | filters.Text("🌚 Dark Theme"), apply_theme),
                MessageHandler(filters.Text("🔙 Назад") | filters.Text("🔙 Back"), settings_menu),
            ],
            LANGUAGE: [
                MessageHandler(filters.Text("🇷🇺 Русский") | filters.Text("🇷🇺 Russian"), apply_language),
                MessageHandler(filters.Text("🇺🇸 Английский") | filters.Text("🇺🇸 English"), apply_language),
                MessageHandler(filters.Text("🔙 Назад") | filters.Text("🔙 Back"), settings_menu),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()