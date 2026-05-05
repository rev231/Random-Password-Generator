import random
import string
import json
import os
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox


class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Random Password Generator")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        self.history_file = "password_history.json"

        self.length_var = IntVar(value=12)
        self.digits_var = BooleanVar(value=True)
        self.letters_var = BooleanVar(value=True)
        self.specials_var = BooleanVar(value=True)

        self.charsets = {
            "digits": string.digits,
            "letters": string.ascii_letters,
            "specials": string.punctuation
        }

        self.create_widgets()
        self.load_history()

        self.digits_var.trace_add("write", lambda *_: self.update_min_length())
        self.letters_var.trace_add("write", lambda *_: self.update_min_length())
        self.specials_var.trace_add("write", lambda *_: self.update_min_length())

        self.update_min_length()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=BOTH, expand=True)

        length_frame = ttk.LabelFrame(main_frame, text="Длина пароля", padding="5")
        length_frame.pack(fill=X, pady=5)

        self.length_slider = Scale(
            length_frame, from_=4, to=64, orient=HORIZONTAL,
            variable=self.length_var, tickinterval=0, length=500
        )
        self.length_slider.pack(side=LEFT, fill=X, expand=True, padx=5)

        info_frame = ttk.Frame(length_frame)
        info_frame.pack(side=LEFT, padx=10)

        ttk.Label(info_frame, text="Значение:").pack(side=LEFT)
        self.length_value_label = ttk.Label(info_frame, textvariable=self.length_var, width=4, font=("Arial", 10, "bold"))
        self.length_value_label.pack(side=LEFT, padx=5)

        ttk.Label(info_frame, text=f"(мин: {self.length_slider.cget('from')}, макс: {self.length_slider.cget('to')})").pack(side=LEFT)

        chars_frame = ttk.LabelFrame(main_frame, text="Допустимые символы", padding="5")
        chars_frame.pack(fill=X, pady=5)

        ttk.Checkbutton(chars_frame, text="Цифры (0-9)", variable=self.digits_var).pack(side=LEFT, padx=15)
        ttk.Checkbutton(chars_frame, text="Буквы (A-Z, a-z)", variable=self.letters_var).pack(side=LEFT, padx=15)
        ttk.Checkbutton(chars_frame, text="Спецсимволы (!@#$%^&*...)", variable=self.specials_var).pack(side=LEFT, padx=15)

        gen_frame = ttk.LabelFrame(main_frame, text="Генерация пароля", padding="5")
        gen_frame.pack(fill=X, pady=5)

        self.generate_btn = ttk.Button(gen_frame, text="Сгенерировать пароль", command=self.generate_password)
        self.generate_btn.pack(side=LEFT, padx=5, pady=5)

        self.password_entry = Entry(gen_frame, font=("Courier New", 12), state="readonly", width=35)
        self.password_entry.pack(side=LEFT, fill=X, expand=True, padx=5, pady=5)

        self.copy_btn = ttk.Button(gen_frame, text="📋 Копировать", command=self.copy_current_password)
        self.copy_btn.pack(side=LEFT, padx=5, pady=5)

        history_frame = ttk.LabelFrame(main_frame, text="История паролей", padding="5")
        history_frame.pack(fill=BOTH, expand=True, pady=10)

        history_buttons_frame = ttk.Frame(history_frame)
        history_buttons_frame.pack(fill=X, pady=5)

        ttk.Button(history_buttons_frame, text="🗑 Очистить историю", command=self.clear_history).pack(side=LEFT, padx=5)
        ttk.Button(history_buttons_frame, text="❌ Удалить выбранное", command=self.delete_selected_history).pack(side=LEFT, padx=5)
        ttk.Button(history_buttons_frame, text="💾 Сохранить историю", command=self.save_history).pack(side=LEFT, padx=5)

        tree_frame = ttk.Frame(history_frame)
        tree_frame.pack(fill=BOTH, expand=True)

        columns = ("timestamp", "password", "length")
        self.history_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        self.history_tree.heading("timestamp", text="Дата и время")
        self.history_tree.heading("password", text="Пароль")
        self.history_tree.heading("length", text="Длина")
        
        self.history_tree.column("timestamp", width=150, anchor="center")
        self.history_tree.column("password", width=400, anchor="w")
        self.history_tree.column("length", width=60, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.history_tree.bind("<Double-1>", self.copy_selected_history_password)

        info_label = ttk.Label(main_frame, text="💡 Подсказка: Двойной клик по записи в истории копирует пароль", 
                               foreground="gray", font=("Arial", 9))
        info_label.pack(pady=5)

    def update_min_length(self):
        active_count = sum([self.digits_var.get(), self.letters_var.get(), self.specials_var.get()])
        min_len = max(4, active_count) if active_count > 0 else 4

        self.length_slider.config(from_=min_len)

        current_len = self.length_var.get()
        if current_len < min_len:
            self.length_var.set(min_len)
            self.length_slider.set(min_len)

    def generate_password(self):
        active_sets = []
        set_names = []
        
        if self.digits_var.get():
            active_sets.append(self.charsets["digits"])
            set_names.append("цифры")
        if self.letters_var.get():
            active_sets.append(self.charsets["letters"])
            set_names.append("буквы")
        if self.specials_var.get():
            active_sets.append(self.charsets["specials"])
            set_names.append("спецсимволы")

        if not active_sets:
            messagebox.showerror(
                "Ошибка", 
                "Не выбран ни один тип символов!\n\nВыберите хотя бы один вариант:\n• Цифры\n• Буквы\n• Спецсимволы"
            )
            return

        length = self.length_var.get()
        required = len(active_sets)

        if length < required:
            messagebox.showerror(
                "Ошибка",
                f"Недостаточная длина пароля!\n\n"
                f"Для выбранных наборов символов ({', '.join(set_names)}) "
                f"требуется длина не менее {required} символов.\n"
                f"Текущая длина: {length}\n"
                f"Рекомендуется увеличить длину пароля."
            )
            return

        if length > 64:
            messagebox.showwarning(
                "Предупреждение",
                f"Длина пароля {length} символов может быть избыточной.\n"
                f"Рекомендуется использовать 64 символа или меньше."
            )

        combined = "".join(active_sets)

        password_chars = [random.choice(charset) for charset in active_sets]

        for _ in range(length - required):
            password_chars.append(random.choice(combined))

        random.shuffle(password_chars)
        password = "".join(password_chars)

        self.password_entry.config(state="normal")
        self.password_entry.delete(0, END)
        self.password_entry.insert(0, password)
        self.password_entry.config(state="readonly")

        self.add_to_history(password)

    def add_to_history(self, password):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        length = len(password)
        self.history_tree.insert("", 0, values=(timestamp, password, length))
        self.save_history()

    def clear_history(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю паролей?"):
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            self.save_history()
            messagebox.showinfo("Успех", "История успешно очищена!")

    def delete_selected_history(self):
        selected_items = self.history_tree.selection()
        if not selected_items:
            messagebox.showinfo("Информация", "Нет выделенных записей для удаления.\n\nДля удаления: выберите запись(и) и нажмите кнопку.")
            return
        
        if messagebox.askyesno("Подтверждение", f"Удалить {len(selected_items)} выбранную(ые) запись(и)?"):
            for item in selected_items:
                self.history_tree.delete(item)
            self.save_history()
            messagebox.showinfo("Успех", "Выбранные записи удалены!")

    def copy_current_password(self):
        password = self.password_entry.get()
        if password:
            self.copy_to_clipboard(password)
            messagebox.showinfo("Успех", "Пароль скопирован в буфер обмена!")
        else:
            messagebox.showwarning("Предупреждение", "Нет сгенерированного пароля для копирования.\n\nСначала сгенерируйте пароль.")

    def copy_selected_history_password(self, event):
        selected_item = self.history_tree.selection()
        if selected_item:
            item = selected_item[0]
            password = self.history_tree.item(item, "values")[1]
            self.copy_to_clipboard(password)
            messagebox.showinfo("Успех", f"Пароль из истории скопирован в буфер обмена!")
        else:
            messagebox.showwarning("Предупреждение", "Выберите запись в истории для копирования.")

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def save_history(self):
        history_data = []
        for item in self.history_tree.get_children():
            timestamp, password, length = self.history_tree.item(item, "values")
            history_data.append({
                "timestamp": timestamp,
                "password": password,
                "length": int(length)
            })
        
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю:\n{str(e)}")

    def load_history(self):
        if not os.path.exists(self.history_file):
            return
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            for entry in reversed(history_data):
                self.history_tree.insert("", 0, 
                    values=(entry["timestamp"], entry["password"], entry["length"]))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить историю:\n{str(e)}")


def main():
    root = Tk()
    app = PasswordGeneratorApp(root)
    
    def on_closing():
        if messagebox.askokcancel("Выход", "Сохранить историю перед выходом?"):
            app.save_history()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
