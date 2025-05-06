import sqlite3
import os
from tkinter import *
from tkinter import ttk, messagebox

class NoteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Context")
        self.db_folder = "db"
        self.conn = None
        self.cursor = None
        self.current_search_tags = []  # Для хранения тегов, по которым ведется поиск
        
        # Создаем папку для базы данных, если её нет
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)
        
        # Интерфейс
        self.setup_ui()
    
    def setup_ui(self):
        # Фрейм для подключения к базе
        db_frame = LabelFrame(self.root, text="Подключение к базе данных")
        db_frame.pack(pady=10, padx=10, fill=X)
        
        Label(db_frame, text="Имя:").grid(row=0, column=0, padx=5, pady=5)
        self.db_name_entry = Entry(db_frame, width=10)
        self.db_name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.db_name_entry.insert(0, "MyDiary.db")  # Пример имени по умолчанию
        
        self.notes_count_label = Label(db_frame, text="Заметок: 0")
        self.notes_count_label.grid(row=0, column=3, padx=5, pady=5)
        
        Button(db_frame, text="П", command=self.connect_db).grid(row=0, column=2, padx=5, pady=5)
        
        # Фрейм для поиска
        search_frame = LabelFrame(self.root, text="Поиск заметок")
        search_frame.pack(pady=10, padx=10, fill=X)
        
        # Поиск по тегам
        Label(search_frame, text="Слова:").grid(row=0, column=0, padx=5, pady=5)
        self.search_entry = Entry(search_frame, width=10)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Поиск по ID
        Label(search_frame, text="Номер заметки:").grid(row=1, column=0, padx=5, pady=5)
        self.id_search_entry = Entry(search_frame, width=10)
        self.id_search_entry.grid(row=1, column=1, padx=5, pady=5, sticky=W)
        
        Button(search_frame, text="Поиск", command=self.search_notes).grid(row=0, column=2, padx=5, pady=5, rowspan=2)
        
        # Результаты поиска (связанные ключевые слова)
        self.related_tags_label = Label(self.root, text="Слова:")
        self.related_tags_label.pack(anchor=W, padx=10)
        
        self.related_tags_listbox = Listbox(self.root, height=5)
        self.related_tags_listbox.pack(pady=5, padx=10, fill=X)
        self.related_tags_listbox.bind('<<ListboxSelect>>', self.show_notes_by_tag)
        
        # Список заметок (уменьшенный)
        self.notes_label = Label(self.root, text="Заметки:")
        self.notes_label.pack(anchor=W, padx=10)
        
        self.notes_listbox = Listbox(self.root, height=5)  # Уменьшили высоту
        self.notes_listbox.pack(pady=5, padx=10, fill=X)
        self.notes_listbox.bind('<<ListboxSelect>>', self.show_note_content)
        
        edit_frame = LabelFrame(self.root, text="Добавить/Редактировать заметку")
        edit_frame.pack(pady=10, padx=10, fill=BOTH, expand=True)
        
        Label(edit_frame, text="Слова:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.tags_entry = Entry(edit_frame)
        self.tags_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=EW)
        
        # Фрейм для кнопок и текстового поля
        text_row_frame = Frame(edit_frame)
        text_row_frame.grid(row=1, column=0, columnspan=3, sticky=NSEW, padx=5, pady=5)
        
        # Метка "Текст" и кнопки слева
        Label(text_row_frame, text="Текст:").grid(row=0, column=0, sticky=NW)
        
        # Фрейм для кнопок (прижат к левому краю)
        button_frame = Frame(text_row_frame)
        button_frame.grid(row=1, column=0, sticky=NS)
        
        # Кнопки "К" и "В" (вертикально)
        Button(button_frame, text="К", command=self.copy_text, width=2).pack(pady=2)
        Button(button_frame, text="В", command=self.paste_text, width=2).pack(pady=2)
        
        # Текстовое поле с прокруткой (занимает оставшееся пространство)
        text_frame = Frame(text_row_frame)
        text_frame.grid(row=1, column=1, sticky=NSEW)
        
        scroll_y = Scrollbar(text_frame)
        scroll_y.pack(side=RIGHT, fill=Y)
        
        self.note_text_entry = Text(
            text_frame, 
            width=50, 
            height=10,
            wrap=WORD,
            yscrollcommand=scroll_y.set
        )
        self.note_text_entry.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.config(command=self.note_text_entry.yview)
        
        # Настройка растягивания
        edit_frame.grid_columnconfigure(1, weight=1)
        edit_frame.grid_rowconfigure(1, weight=1)
        text_row_frame.grid_columnconfigure(1, weight=1)
        text_row_frame.grid_rowconfigure(1, weight=1)
        
        # Кнопки в отдельном фрейме
        button_frame = Frame(edit_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky=E)
        
        Button(button_frame, text="Добавить", command=self.add_note).pack(side=LEFT, padx=5)
        Button(button_frame, text="Сохранить", command=self.save_note).pack(side=LEFT, padx=5)
        Button(button_frame, text="Удалить", command=self.delete_note).pack(side=LEFT, padx=5)
        
        # Текущий ID заметки (для редактирования)
        self.current_note_id = None

    
    def connect_db(self):
        db_name = self.db_name_entry.get().strip()
        if not db_name:
            messagebox.showerror("Ошибка", "Введите имя базы данных")
            return
        
        db_path = os.path.join(self.db_folder, db_name)
        
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            
            # Создаем таблицу, если её нет
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tags TEXT,
                    content TEXT
                )
            ''')
            self.conn.commit()
            
            # Получаем количество заметок
            self.cursor.execute("SELECT COUNT(*) FROM notes")
            notes_count = self.cursor.fetchone()[0]
            self.notes_count_label.config(text=f"Заметок: {notes_count}")
            
            messagebox.showinfo("Успех", f"Подключено к базе: {db_name}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {str(e)}")
    
    def search_notes(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных")
            return
        
        # Проверяем поиск по ID
        id_search = self.id_search_entry.get().strip()
        if id_search:
            try:
                note_id = int(id_search)
                self.cursor.execute("SELECT id, tags FROM notes WHERE id = ?", (note_id,))
                notes = self.cursor.fetchall()
                
                if not notes:
                    messagebox.showinfo("Результат", "Заметка с таким ID не найдена")
                    return
                
                # Очищаем предыдущие результаты
                self.related_tags_listbox.delete(0, END)
                self.notes_listbox.delete(0, END)
                
                # Добавляем найденную заметку в список
                for note in notes:
                    note_id, tags = note
                    self.notes_listbox.insert(END, f"{note_id}: {tags}")
                
                # Показываем содержимое заметки
                if len(notes) == 1:
                    self.notes_listbox.selection_set(0)
                    self.show_note_content(None)
                
                return
            except ValueError:
                messagebox.showerror("Ошибка", "ID должен быть числом")
                return
        
        # Если поиск не по ID, ищем по тегам
        search_terms = self.search_entry.get().strip()
        if not search_terms:
            messagebox.showerror("Ошибка", "Введите ключевые слова для поиска или номер заметки")
            return
        
        # Сохраняем теги поиска
        self.current_search_tags = [tag.strip() for tag in search_terms.split(',') if tag.strip()]
        
        # Очищаем предыдущие результаты
        self.related_tags_listbox.delete(0, END)
        self.notes_listbox.delete(0, END)
        
        # Ищем заметки, содержащие хотя бы одно из ключевых слов
        query = "SELECT tags FROM notes WHERE "
        query += " OR ".join(["tags LIKE ?" for _ in self.current_search_tags])
        params = [f"%{tag}%" for tag in self.current_search_tags]
        
        self.cursor.execute(query, params)
        notes = self.cursor.fetchall()
        
        # Собираем все уникальные теги из найденных заметок
        all_tags = set()
        for note in notes:
            tags = note[0].split(',')
            for tag in tags:
                all_tags.add(tag.strip())
        
        # Удаляем исходные теги поиска
        for tag in self.current_search_tags:
            if tag in all_tags:
                all_tags.remove(tag)
        
        # Выводим связанные теги
        for tag in sorted(all_tags):
            self.related_tags_listbox.insert(END, tag)
    
    def show_notes_by_tag(self, event):
        if not self.conn:
            return
        
        selection = self.related_tags_listbox.curselection()
        if not selection:
            return
        
        selected_tag = self.related_tags_listbox.get(selection[0])
        
        # Ищем заметки, содержащие И тег поиска И выбранный тег
        query = "SELECT id, tags FROM notes WHERE "
        
        # Условия для тегов поиска
        search_conditions = []
        params = []
        for tag in self.current_search_tags:
            search_conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")
        
        # Добавляем условие для выбранного тега
        search_conditions.append("tags LIKE ?")
        params.append(f"%{selected_tag}%")
        
        # Объединяем все условия через AND
        query += " AND ".join(search_conditions)
        
        self.cursor.execute(query, params)
        notes = self.cursor.fetchall()
        
        # Очищаем список заметок
        self.notes_listbox.delete(0, END)
        
        # Добавляем заметки в список
        for note in notes:
            note_id, tags = note
            self.notes_listbox.insert(END, f"{note_id}: {tags}")
    
    def show_note_content(self, event):
        if not self.conn:
            return
        
        selection = self.notes_listbox.curselection()
        if not selection:
            return
        
        selected_note = self.notes_listbox.get(selection[0])
        note_id = int(selected_note.split(':')[0])
        
        # Получаем полные данные заметки
        self.cursor.execute("SELECT tags, content FROM notes WHERE id = ?", (note_id,))
        note = self.cursor.fetchone()
        
        if note:
            self.current_note_id = note_id
            self.tags_entry.delete(0, END)
            self.tags_entry.insert(0, note[0])
            self.note_text_entry.delete(1.0, END)
            self.note_text_entry.insert(1.0, note[1])
    
    def add_note(self):
        """Добавляет новую заметку с текущими данными"""
        if not self.conn:
            messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных")
            return
        
        tags = self.tags_entry.get().strip()
        content = self.note_text_entry.get("1.0", END).strip()
        
        if not tags or not content:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        # Очищаем теги от лишних пробелов
        cleaned_tags = ', '.join([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        # Добавляем новую заметку
        self.cursor.execute(
            "INSERT INTO notes (tags, content) VALUES (?, ?)",
            (cleaned_tags, content)
        )
        self.conn.commit()
        
        messagebox.showinfo("Успех", "Новая заметка добавлена")
        
        # Обновляем интерфейс
        self.current_note_id = None
        self.clear_fields()
        
        # Обновляем счетчик заметок
        self.cursor.execute("SELECT COUNT(*) FROM notes")
        notes_count = self.cursor.fetchone()[0]
        self.notes_count_label.config(text=f"Заметок: {notes_count}")
        
        # Обновляем список заметок
        #self.search_notes()
    
    def save_note(self):
        """Обновляет существующую заметку"""
        if not self.conn:
            messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных")
            return
        
        if not self.current_note_id:
            messagebox.showerror("Ошибка", "Не выбрана заметка для сохранения")
            return
        
        tags = self.tags_entry.get().strip()
        content = self.note_text_entry.get("1.0", END).strip()
        
        if not tags or not content:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        # Очищаем теги от лишних пробелов
        cleaned_tags = ', '.join([tag.strip() for tag in tags.split(',') if tag.strip()])
        
        # Обновляем существующую заметку
        self.cursor.execute(
            "UPDATE notes SET tags = ?, content = ? WHERE id = ?",
            (cleaned_tags, content, self.current_note_id)
        )
        self.conn.commit()
        
        messagebox.showinfo("Успех", "Заметка обновлена")
        
        # Обновляем интерфейс
        self.search_notes()
    
    def delete_note(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных")
            return
        
        if not self.current_note_id:
            messagebox.showerror("Ошибка", "Выберите заметку для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную заметку?"):
            self.cursor.execute("DELETE FROM notes WHERE id = ?", (self.current_note_id,))
            self.conn.commit()
            messagebox.showinfo("Успех", "Заметка удалена")
            self.clear_fields()
            self.current_note_id = None
            
            # Обновляем счетчик заметок
            self.cursor.execute("SELECT COUNT(*) FROM notes")
            notes_count = self.cursor.fetchone()[0]
            self.notes_count_label.config(text=f"Заметок: {notes_count}")
            
            # Обновляем список заметок
            #self.search_notes()
    
    def clear_fields(self):
        """Очищает поля ввода"""
        self.tags_entry.delete(0, END)
        self.note_text_entry.delete(1.0, END)

    def copy_text(self):
        """Копирует выделенный текст из текстового поля в буфер обмена"""
        if self.note_text_entry.tag_ranges("sel"):
            self.root.clipboard_clear()
            self.root.clipboard_append(self.note_text_entry.get("sel.first", "sel.last"))

    def paste_text(self):
        """Вставляет текст из буфера обмена в текстовое поле"""
        try:
            text = self.root.clipboard_get()
            self.note_text_entry.insert(INSERT, text)
        except TclError:
            pass

if __name__ == "__main__":
    root = Tk()
    root.geometry("700x700")  # Увеличиваем размер окна
    app = NoteApp(root)
    root.mainloop()
