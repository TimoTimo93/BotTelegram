import subprocess
import sys
import pkg_resources
import json
from datetime import datetime, time
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue
import pytz
from openpyxl import load_workbook, Workbook

# Hàm để kiểm tra và cài đặt hoặc nâng cấp thư viện
def install_or_upgrade(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])

# Danh sách các thư viện cần thiết
required_packages = [
    "python-telegram-bot[job-queue]",
    "pytz",
    "openpyxl",
    "pandas",
    "nest_asyncio",
    "watchdog",
    "schedule"
]

# Kiểm tra và cài đặt hoặc nâng cấp các thư viện cần thiết
def check_and_install_packages():
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    updated_successfully = False

    for package in required_packages:
        package_name = package.split('[')[0].lower()
        if package_name not in installed_packages:
            print(f"Đang cài đặt {package}...")
            if install_or_upgrade(package):
                updated_successfully = True
        else:
            print(f"Đang kiểm tra cập nhật cho {package}...")
            if install_or_upgrade(package):
                updated_successfully = True

    return updated_successfully

# Gọi hàm kiểm tra và cài đặt thư viện
if check_and_install_packages():
    # Làm sạch cửa sổ CMD
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Tất cả các thư viện đã được cài đặt thành công.")  # In thông báo thành công

# Khởi tạo nest_asyncio để giải quyết vấn đề vòng lặp sự kiện
try:
    import nest_asyncio
except ImportError:
    print("Nest_asyncio chưa được cài đặt. Đang cài đặt...")
    install_or_upgrade('nest_asyncio')
    import nest_asyncio  # Thử lại sau khi cài đặt

nest_asyncio.apply()

# Import các thư viện cần thiết sau khi đã cài đặt
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from openpyxl.styles import PatternFill, Alignment
from openpyxl import load_workbook, Workbook
from telegram import Update, ChatMember
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, JobQueue
import pandas as pd  # Đảm bảo import pandas sau khi cài đặt
import pytz
from datetime import time

# Tiếp tục với định nghĩa class và các phần còn lại của mã
class RestartBotHandler(FileSystemEventHandler):
    # Định nghĩa các phương thức trong class này
    pass

# Tạo file lưu trữ lịch sử giao dịch và số dư
data_file = 'balance_data.json'
transaction_file = 'transaction_history.json'
authorized_users_file = 'authorized_users.json'

# Hàm để load dữ liệu từ file
def load_data(file_name):
    try:
        with open(file_name, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Hàm để lưu dữ liệu vào file
def save_data(data, file_name):
    with open(file_name, 'w') as file:
        json.dump(data, file)

# Hàm lấy danh sách thành viên có quyền
def get_authorized_users():
    return load_data(authorized_users_file)

# Hàm kiểm tra xem người dùng có quyền hay không
def is_user_authorized(user_id):
    authorized_users = get_authorized_users()
    return str(user_id) in authorized_users

# Hàm kiểm tra xem người dùng có phải là chủ nhóm không
async def is_user_owner(chat, user_id):
    admins = await chat.get_administrators()
    for admin in admins:
        if admin.user.id == user_id and admin.status == 'creator':
            return True
    return False

# Hàm cấp quyền cho người dùng
def authorize_user(user_id):
    authorized_users = get_authorized_users()
    authorized_users[str(user_id)] = True
    save_data(authorized_users, authorized_users_file)

# Hàm hủy quyền của người dùng
def unauthorize_user(user_id):
    authorized_users = get_authorized_users()
    if str(user_id) in authorized_users:
        del authorized_users[str(user_id)]
    save_data(authorized_users, authorized_users_file)

# Hàm kiểm tra xem tin nhắn có yêu cầu cấp quyền hay không
def is_authorization_request(text):
    return text in ["授权", "给权限", "报权限", "cấp quyền"]

# Hàm để cập nhật số dư và lịch sử giao dịch
def update_balance_and_transaction(user_id, amount, user_name, now):
    # Cập nhật số dư
    balance_data = load_data(data_file)
    if str(user_id) not in balance_data:
        balance_data[str(user_id)] = 0
    balance_data[str(user_id)] += amount
    save_data(balance_data, data_file)

    # Cập nhật lịch sử giao dịch
    transaction_history = load_data(transaction_file)
    if str(user_id) not in transaction_history:
        transaction_history[str(user_id)] = []
    transaction_history[str(user_id)].append({
        "user_name": user_name,
        "time": now,
        "amount": amount
    })
    save_data(transaction_history, transaction_file)

# Hàm để lưu ID nhóm chat vào file riêng
def save_group_chat_id(chat_id):
    with open('group_chat_id.txt', 'w') as file:
        file.write(str(chat_id))

# Hàm để kiểm tra và lưu ID nhóm chat nếu chưa được lưu
def check_and_save_group_chat_id(chat_id):
    try:
        with open('group_chat_id.txt', 'r') as file:
            saved_chat_id = file.read().strip()
            if saved_chat_id == str(chat_id):
                return  # ID đã được lưu, không cần lưu lại
    except FileNotFoundError:
        pass  # File chưa tồn tại, sẽ tạo mới

    # Lưu ID nhóm chat
    save_group_chat_id(chat_id)

# Biến để lưu trạng thái bắt đầu cho mỗi nhóm
group_start_status = {}

# Hàm để kiểm tra và cập nhật trạng thái bắt đầu
def set_group_start_status(chat_id, status):
    group_start_status[chat_id] = status

def is_group_started(chat_id):
    return group_start_status.get(chat_id, False)

# Handler để xử lý tin nhắn và lưu ID nhóm chat
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    check_and_save_group_chat_id(chat_id)  # Kiểm tra và lưu ID nhóm chat

    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name  # Lấy tên người dùng
    text = update.message.text.strip()
    chat = update.effective_chat

    # Kiểm tra nếu tin nhắn là lệnh "Bắt đầu"
    if text.lower() in ["bắt đầu", "开始"]:
        if await is_user_owner(chat, user_id) or is_user_authorized(user_id):
            set_group_start_status(chat_id, True)
            await update.message.reply_text("设置成功：开始")  # Thông báo sau khi gửi lệnh "Bắt đầu"
        else:
            await update.message.reply_text("您没有权限执行此操作。")
        return

    # Kiểm tra xem nhóm đã gửi lệnh "Bắt đầu" chưa
    if not is_group_started(chat_id):
        await update.message.reply_text(
            "状态：记账失败！\n"
            "原因：本群组今日还没有设置「开始记账」状态。\n"
            "提示：如需记账，请您发送「开始」二字。"
        )
        return

    # Kiểm tra xem người dùng có quyền không
    if not await is_user_owner(chat, user_id) and not is_user_authorized(user_id):
        # Kiểm tra nếu tin nhắn là lệnh cộng tiền, trừ tiền hoặc cấp quyền
        if text.startswith('+') or text.startswith('-') or text.startswith("入款 -") or text.startswith("下发 -"):
            await asyncio.sleep(0.2)
            await update.message.reply_text("您没有权限执行此操作。")
            return

    # Kiểm tra nếu là câu cấp quyền
    if update.message.reply_to_message and is_authorization_request(text):
        target_user = update.message.reply_to_message.from_user
        target_user_id = target_user.id
        target_user_name = target_user.username or target_user.first_name
        if not await is_user_owner(chat, user_id) and not is_user_authorized(user_id):  # Kiểm tra quyền trước khi cấp quyền
            await asyncio.sleep(0.2)
            await update.message.reply_text("您没有权限执行此操作。")
            return
        authorize_user(target_user_id)
        await asyncio.sleep(0.2)
        await update.message.reply_text(f"已授予用户 {target_user_name} 权限。")
        return

    # Xử lý cng hoặc trừ tiền
    now = datetime.now().strftime('%H:%M:%S')
    if text.startswith('+') or text.startswith('-'):
        try:
            amount = int(text[1:].strip())
            if text.startswith('-'):
                amount = -amount

            # Cập nhật số dư và lịch sử giao dịch
            update_balance_and_transaction(user_id, amount, user_name, now)

            # Xuất file Excel
            group_chat_id = update.effective_chat.id
            excel_file_name = f'{group_chat_id}.xlsx'
            export_to_excel(excel_file_name)

            # Gửi báo cáo tổng kết
            await send_summary(update)
        except ValueError:
            await asyncio.sleep(0.2)
            await update.message.reply_text("Vui lòng nhập số tiền hợp lệ.")

    elif text.startswith("入款 -") or text.startswith("下发 -"):
        parts = text.split()
        if len(parts) != 2:
            await asyncio.sleep(0.2)
            await update.message.reply_text("Định dạng không hợp lệ")
            return

        command, amount_str = parts
        amount = int(amount_str)

        if command == "入款":
            # Xử lý hủy giao dịch nạp tiền
            amount = -abs(amount)
        elif command == "下发":
            # Xử lý hủy giao dịch rút tiền (cộng ngược lại)
            amount = abs(amount)

        # Cập nhật số dư và lịch sử giao dịch
        update_balance_and_transaction(user_id, amount, user_name, now)

        # Xuất file Excel
        group_chat_id = update.effective_chat.id
        excel_file_name = f'{group_chat_id}.xlsx'
        export_to_excel(excel_file_name)

        # Gửi báo cáo tổng kết
        await send_summary(update)

# Lệnh cấp quyền cho thành viên
async def grant_permission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user_id = update.message.from_user.id

    # Chỉ cho phép chủ nhóm thực hiện
    if not await is_user_owner(chat, user_id):
        await asyncio.sleep(0.2)
        await update.message.reply_text("您没有权限执行此操作。")
        return

    if context.args:
        target_user_id = context.args[0]
        # Lấy thông tin của người dùng được cấp quyền
        target_user = await context.bot.get_chat_member(chat.id, target_user_id)
        target_user_name = target_user.user.username or target_user.user.first_name  # Lấy username hoặc tên nếu không có username

        authorize_user(target_user_id)
        await asyncio.sleep(0.2)
        await update.message.reply_text(f"已授予用户 {target_user_name} 权限。")  # Sử dụng tên tài khoản mục tiêu
    else:
        await asyncio.sleep(0.2)
        await update.message.reply_text("请指定用户。")

# Lệnh hủy quyền thành viên
async def revoke_permission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user_id = update.message.from_user.id

    # Chỉ cho phép chủ nhóm thực hiện
    if not await is_user_owner(chat, user_id):
        await asyncio.sleep(0.2)
        await update.message.reply_text("您没有权限执行此操作。")
        return

    if context.args:
        target_user_id = context.args[0]
        # Lấy thông tin của người dùng được hủy quyền
        target_user = await context.bot.get_chat_member(chat.id, target_user_id)
        target_user_name = target_user.user.username or target_user.user.first_name  # Lấy username hoặc tên nếu không có username

        unauthorize_user(target_user_id)
        await asyncio.sleep(0.2)
        await update.message.reply_text(f"已撤销用户 {target_user_name} 的权限。")  # Sử dụng tên tài khoản mục tiêu
    else:
        await asyncio.sleep(0.2)
        await update.message.reply_text("请指定用户ID。")


# Hàm gửi báo cáo tổng kết
async def send_summary(update: Update):
    transaction_history = load_data(transaction_file)
    deposits = []
    withdrawals = []
    total_deposit = 0
    total_withdraw = 0

    # Lọc giao dịch và tạo danh sách nạp và rút
    for user_id, transactions in transaction_history.items():
        for transaction in transactions:
            if transaction['amount'] > 0:
                deposits.append(transaction)
                total_deposit += transaction['amount']
            else:
                withdrawals.append(transaction)
                total_withdraw += abs(transaction['amount'])

    # Sắp xếp lại giao dịch theo thời gian
    deposits = sorted(deposits, key=lambda x: x['time'])
    withdrawals = sorted(withdrawals, key=lambda x: x['time'])

    # Lấy 5 giao dịch nạp và rút gần nhất
    recent_deposit = deposits[-5:]
    recent_withdrawals = withdrawals[-5:]

    # Tạo nội dung báo cáo với số tiền có màu xanh lục
    deposit_summary = "入款 {} 笔（显示最近 5 笔）：\n".format(len(deposits))
    for dep in recent_deposit:
        deposit_summary += f"    {dep['user_name']}    {dep['time']}    <code style='color:green;'>{dep['amount']}</code>\n"

    withdraw_summary = "下发 {} 笔（显示最近 5 笔）：\n".format(len(withdrawals))
    for wd in recent_withdrawals:
        withdraw_summary += f"    {wd['user_name']}    {wd['time']}    <code style='color:green;'>{wd['amount']}</code>\n"

    total_summary = (
        f"总入款：<code style='color:green;'>{total_deposit}</code>\n"
        f"总下发：<code style='color:green;'>{total_withdraw}</code>\n"
        f"余款：<code style='color:green;'>{total_deposit - total_withdraw}</code>"
    )

    # Gửi báo cáo vào nhóm với chế độ phân tích HTML
    await asyncio.sleep(0.2)
    await update.message.reply_text(deposit_summary + "\n" + withdraw_summary + "\n" + total_summary, parse_mode='HTML')


# Hàm để lấy ID nhóm chat từ file
def get_saved_group_chat_id():
    try:
        with open('group_chat_id.txt', 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        print("Không tìm thấy file group_chat_id.txt")
        return None
    except ValueError:
        print("ID nhóm chat không hợp lệ trong file")
        return None

# Hàm xuất báo cáo ra file Excel theo định dạng yêu cầu
def export_to_excel(excel_file_name):
    transactions = load_data(transaction_file)

    deposit_data = []
    withdraw_data = []
    deposit_summary = {}
    withdraw_summary = {}

    for user_id, user_transactions in transactions.items():
        for transaction in user_transactions:
            amount = transaction['amount']
            user_name = transaction['user_name']
            time_str = transaction['time']

            if amount > 0:
                deposit_data.append([user_name, time_str, amount])
                deposit_summary[user_name] = deposit_summary.get(user_name, 0) + amount
            else:
                withdraw_data.append([user_name, time_str, abs(amount)])
                withdraw_summary[user_name] = withdraw_summary.get(user_name, 0) + abs(amount)

    total_deposit = sum(deposit_summary.values())
    total_withdraw = sum(withdraw_summary.values())
    balance = total_deposit - total_withdraw

    # Lấy ID nhóm chat để đặt tên file
    group_chat_id = get_saved_group_chat_id()
    if group_chat_id is None:
        group_chat_id = "unknown_chat_id"

    # Đặt tên file Excel theo ID nhóm chat
    excel_file_name = f'{group_chat_id}.xlsx'

    with pd.ExcelWriter(excel_file_name, engine='openpyxl') as writer:
        workbook = writer.book
        worksheet = workbook.create_sheet(title='Sheet1')

        today_str = datetime.now().strftime('%Y-%m-%d')
        worksheet['A1'] = today_str

        worksheet['B2'] = f'下 {len(withdraw_data)} 笔'

        for idx, row in enumerate(withdraw_data, start=4):
            worksheet[f'B{idx}'] = row[0]
            worksheet[f'C{idx}'] = row[1]
            worksheet[f'D{idx}'] = row[2]

        worksheet['F2'] = '下发分类：'

        for idx, (user, total_amount) in enumerate(withdraw_summary.items(), start=4):
            total_transactions = sum(1 for row in withdraw_data if row[0] == user)
            worksheet[f'F{idx}'] = user
            worksheet[f'G{idx}'] = f'共 {total_transactions} 笔'
            worksheet[f'H{idx}'] = total_amount

        worksheet['K2'] = f'入款 {len(deposit_data)} 笔'

        for idx, row in enumerate(deposit_data, start=4):
            worksheet[f'K{idx}'] = row[0]
            worksheet[f'L{idx}'] = row[1]
            worksheet[f'M{idx}'] = row[2]

        worksheet['O2'] = '入款分类：'

        for idx, (user, total_amount) in enumerate(deposit_summary.items(), start=4):
            total_transactions = sum(1 for row in deposit_data if row[0] == user)
            worksheet[f'O{idx}'] = user
            worksheet[f'P{idx}'] = f'共 {total_transactions} 笔'
            worksheet[f'Q{idx}'] = total_amount

        worksheet['S3'] = '总入款'
        worksheet['S4'] = '总下发'
        worksheet['S5'] = '余款'

        worksheet['T3'] = total_deposit
        worksheet['T4'] = total_withdraw
        worksheet['T5'] = balance

        # Đặt độ rộng các cột theo yêu cầu
        column_widths = {
            'A': 12, 'B': 18, 'C': 9, 'D': 9, 'F': 18, 'G': 9, 'H': 9,
            'K': 18, 'L': 9, 'M': 9, 'O': 18, 'P': 9, 'Q': 9, 'S': 9, 'T': 9
        }

        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width

        # Ẩn cột I
        worksheet.column_dimensions['I'].hidden = True

        # Merge and center các ô
        merge_ranges = ['B2:D2', 'F2:H2', 'K2:M2', 'O2:Q2']
        lime_fill = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")

        for merge_range in merge_ranges:
            worksheet.merge_cells(merge_range)
            for cell in worksheet[merge_range]:
                cell[0].fill = lime_fill
                cell[0].alignment = Alignment(horizontal="center", vertical="center")

        # Tô màu các ô S3, S4, S5, T3, T4, T5
        cells_to_color = ['S3', 'S4', 'S5', 'T3', 'T4', 'T5']
        for cell in cells_to_color:
            worksheet[cell].fill = lime_fill
            worksheet[cell].alignment = Alignment(horizontal="center", vertical="center")

# Hàm gửi báo cáo hàng ngày
async def send_daily_report(context):
    group_chat_id = context.bot_data.get('group_chat_id')
    if group_chat_id is None:
        print("Không thể lấy ID nhóm chat.")
        return

    # Đặt tên file Excel theo ID nhóm chat
    excel_file_name = f'{group_chat_id}.xlsx'
    export_to_excel(excel_file_name)  # Xuất file Excel với tên file mới

    # Gửi báo cáo hàng ngày
    with open(excel_file_name, 'rb') as f:
        await context.bot.send_document(chat_id=group_chat_id, document=f)

# Hàm đặt lại dữ liệu hàng ngày
async def reset_data():
    save_data({}, data_file)  
    save_data({}, transaction_file)  
    print("Dữ liệu đã được đặt lại khi có thay đổi cần thiết.")

# Giám sát reset_data
async def scheduled_reset():
    while True:
        current_time = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%H:%M')
        if current_time == "23:00":  
            await reset_data()  
            await asyncio.sleep(60)  
        await asyncio.sleep(0.2)  

# Lập lịch gửi báo cáo và reset lịch sử giao dịch
def job_send_report(application):
    asyncio.run(send_daily_report(application))

def job_reset(application):
    export_to_excel()
    save_data({}, data_file)  
    save_data({}, transaction_file)  
    print("Dữ liệu đã được reset và báo cáo đã được xuât ra.")

def schedule_tasks(application):
    schedule.every().day.at("23:00").do(job_send_report, application)
    schedule.every().day.at("23:00").do(job_reset, application)

def run_schedule(application):
    while True:
        schedule.run_pending()
        time.sleep(0.2)

# Lệnh bắt đầu ghi chép
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    update_balance(user_id, 0)  
    await update.message.reply_text("记账已开始。请使用 +/入款 或 -/下发 来记录交易。")

# Giám sát file bot.py để tự động khởi động lại khi có thay đổi
class RestartBotHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('bot.py'):
            print(f'{event.src_path} has been modified. Restarting bot...')
            os.execv(sys.executable, ['python'] + sys.argv)

def watch_for_changes():
    event_handler = RestartBotHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Định nghĩa hàm pause_daily_report
async def pause_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jobs = context.job_queue.get_jobs_by_name('daily_report')
    if jobs:
        for job in jobs:
            job.schedule_removal()
        await update.message.reply_text("Đã tạm dừng gửi báo cáo hàng ngày.")
    else:
        await update.message.reply_text("Không có báo cáo hàng ngày nào đang chạy.")

# Định nghĩa hàm resume_daily_report
async def resume_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    setup_daily_job(context.application)
    await update.message.reply_text("Đã khôi phục gửi báo cáo hàng ngày.")

# Định nghĩa hàm send_excel_report
async def send_excel_report(context: ContextTypes.DEFAULT_TYPE):
    print(f"Bắt đầu gửi báo cáo Excel vào lúc {datetime.now()}")
    group_chat_id = get_saved_group_chat_id()
    if group_chat_id is None:
        print("Không thể lấy ID nhóm chat.")
        return

    excel_file_name = f'{group_chat_id}.xlsx'
    export_to_excel(excel_file_name)

    try:
        with open(excel_file_name, 'rb') as file:
            await context.bot.send_document(chat_id=group_chat_id, document=file)
        print(f"Đã gửi file Excel vào nhóm {group_chat_id}")
    except Exception as e:
        print(f"Lỗi khi gửi file Excel: {e}")

    # Đảm bảo file được đóng trước khi xóa
    await asyncio.sleep(1)  # Thêm thời gian chờ ngắn để đảm bảo file không còn được sử dụng
    try:
        if os.path.exists(excel_file_name):
            os.remove(excel_file_name)
            print(f"Đã xóa file {excel_file_name} sau khi gửi")
    except PermissionError as e:
        print(f"Không thể xóa file {excel_file_name}: {e}")

    print(f"Đã gửi xong báo cáo Excel vào lúc {datetime.now()}")

# Hàm để xóa file Excel và file transaction_history.json
async def delete_old_files(context: ContextTypes.DEFAULT_TYPE):
    # Xóa file Excel
    group_chat_id = get_saved_group_chat_id()
    if group_chat_id is not None:
        excel_file_name = f'{group_chat_id}.xlsx'
        await asyncio.sleep(1)  # Thêm thời gian chờ ngắn để đảm bảo file không còn được sử dụng
        try:
            if os.path.exists(excel_file_name):
                os.remove(excel_file_name)
                print(f"Đã xóa file {excel_file_name}")
        except PermissionError as e:
            print(f"Không thể xóa file {excel_file_name}: {e}")

    # Xóa file transaction_history.json
    try:
        if os.path.exists(transaction_file):
            os.remove(transaction_file)
            print("Đã xóa file transaction_history.json")
    except PermissionError as e:
        print(f"Không thể xóa file transaction_history.json: {e}")

# Định nghĩa hàm setup_daily_job
def setup_daily_job(application):
    job_queue = application.job_queue
    if job_queue is None:
        print("Job queue is not initialized.")
        return

    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    job_time = time(hour=2, minute=45, tzinfo=vietnam_tz)
    job_queue.run_daily(send_excel_report, time=job_time, name='daily_report')
    job_queue.run_daily(delete_old_files, time=job_time, name='delete_old_files')

# Hàm main
def main():
    TOKEN = "7941025829:AAEJmUDK3Jr5cbNpNjeTxIim35LZEmWr2DY"
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("grant", grant_permission))
    application.add_handler(CommandHandler("revoke", revoke_permission))
    application.add_handler(CommandHandler("pause_report", pause_daily_report))
    application.add_handler(CommandHandler("resume_report", resume_daily_report))

    setup_daily_job(application)

    application.run_polling()

if __name__ == "__main__":
    main()
