
#TOKEN = '6351919841:AAHitvb8fm2VmNnpq14IXIU3t_INlh7KTDg'
import logging
from telegram import Update, Bot, File
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pdf2docx import Converter
from PIL import Image
import os
import threading
import time
from tqdm import tqdm

# إعدادات تسجيل الدخول
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# إعدادات البوت
TOKEN = '6351919841:AAHitvb8fm2VmNnpq14IXIU3t_INlh7KTDg'
bot = Bot(token=TOKEN)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('مرحبا! هذه قائمة بالخدمات المتاحة:\n'
                              '/convert_pdf_to_word - لتحويل PDF إلى Word\n'
                              '/convert_images_to_pdf - لتحويل صور إلى PDF\n'
                              '/reduce_file_size - لتقليل حجم الملف\n'
                              'يرجى اختيار الخدمة المناسبة.')

def convert_pdf_to_docx(pdf_path: str, docx_path: str, update: Update, context: CallbackContext) -> None:
    try:
        update.message.reply_text('بدأ تحويل PDF إلى Word...')
        cv = Converter(pdf_path)
        for _ in tqdm(range(100), desc="تحويل PDF إلى Word"):
            time.sleep(0.01)  # لمحاكاة التحميل
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        update.message.reply_text('تم تحويل الملف بنجاح!')
    except Exception as e:
        update.message.reply_text(f'حدث خطأ أثناء التحويل: {e}')
        return
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    with open(docx_path, 'rb') as docx_file:
        update.message.reply_document(docx_file)

    if os.path.exists(docx_path):
        os.remove(docx_path)

def handle_document(update: Update, context: CallbackContext) -> None:
    document = update.message.document
    if document.mime_type == 'application/pdf':
        file = bot.get_file(document.file_id)
        pdf_path = os.path.join('downloads', f'{document.file_id}.pdf')
        docx_path = os.path.join('downloads', f'{document.file_id}.docx')

        file.download(pdf_path)
        threading.Thread(target=convert_pdf_to_docx, args=(pdf_path, docx_path, update, context)).start()
    else:
        update.message.reply_text('يرجى إرسال ملف PDF فقط.')

def convert_images_to_pdf(image_paths, pdf_path, update: Update, context: CallbackContext) -> None:
    try:
        images = [Image.open(image).convert('RGB') for image in image_paths]
        images[0].save(pdf_path, save_all=True, append_images=images[1:])
        for image in image_paths:
            os.remove(image)
    except Exception as e:
        update.message.reply_text(f'حدث خطأ أثناء تحويل الصور إلى PDF: {e}')
        return

    with open(pdf_path, 'rb') as pdf_file:
        update.message.reply_document(pdf_file)

    if os.path.exists(pdf_path):
        os.remove(pdf_path)

def handle_images(update: Update, context: CallbackContext) -> None:
    image_files = update.message.photo
    image_paths = []
    for image_file in image_files:
        file = bot.get_file(image_file.file_id)
        image_path = os.path.join('downloads', f'{image_file.file_id}.jpg')
        file.download(image_path)
        image_paths.append(image_path)

    pdf_path = os.path.join('downloads', f'{update.message.message_id}.pdf')
    threading.Thread(target=convert_images_to_pdf, args=(image_paths, pdf_path, update, context)).start()

def reduce_file_size(file_path: str, output_path: str, update: Update, context: CallbackContext) -> None:
    try:
        update.message.reply_text('بدأ تقليل حجم الملف...')
        with open(file_path, 'rb') as f:
            data = f.read()
        
        reduced_data = data[:len(data) // 2]

        with open(output_path, 'wb') as f:
            f.write(reduced_data)
        
        os.remove(file_path)
        update.message.reply_text('تم تقليل حجم الملف بنجاح!')
    except Exception as e:
        update.message.reply_text(f'حدث خطأ أثناء تقليل حجم الملف: {e}')
        return

    with open(output_path, 'rb') as out_file:
        update.message.reply_document(out_file)

    if os.path.exists(output_path):
        os.remove(output_path)

def handle_reduce_file_size(update: Update, context: CallbackContext) -> None:
    document = update.message.document
    file = bot.get_file(document.file_id)
    file_path = os.path.join('downloads', f'{document.file_id}')
    output_path = os.path.join('downloads', f'reduced_{document.file_id}')

    file.download(file_path)
    threading.Thread(target=reduce_file_size, args=(file_path, output_path, update, context)).start()

def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('convert_pdf_to_word', lambda update, context: update.message.reply_text('أرسل ملف PDF للتحويل إلى Word.')))
    dispatcher.add_handler(CommandHandler('convert_images_to_pdf', lambda update, context: update.message.reply_text('أرسل صور JPG للتحويل إلى PDF.')))
    dispatcher.add_handler(CommandHandler('reduce_file_size', lambda update, context: update.message.reply_text('أرسل ملف لتقليل حجمه.')))

    dispatcher.add_handler(MessageHandler(Filters.document.mime_type('application/pdf'), handle_document))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_images))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_reduce_file_size))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    main()
