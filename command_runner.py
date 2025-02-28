import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import json
import os
import sys
import ctypes


class CommandRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("Komut.exe")
        self.root.geometry("600x500")
        
        # AppData klasöründe uygulama verileri için dizin oluştur
        app_name = "Komut.exe"
        appdata = os.getenv('APPDATA')
        self.app_data_dir = os.path.join(appdata, app_name)
        os.makedirs(self.app_data_dir, exist_ok=True)
        
        # Komutları saklayacağımız dosya yolu
        self.commands_file = os.path.join(self.app_data_dir, "saved_commands.json")
        
        # Thread kontrolü için bayrak
        self.is_closing = False
        
        # Stil ve tema ayarları
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabelframe', background='#f0f0f0')
        self.style.configure('TLabelframe.Label', font=('Arial', 10, 'bold'))
        self.style.configure('TButton', 
                           padding=5, 
                           font=('Arial', 9),
                           background='#2196F3')
        
        # Ana container
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.configure(bg='#f0f0f0')
        
        # Komut girişi
        self.command_frame = ttk.LabelFrame(self.main_frame, text="Yeni Komut", padding="10")
        self.command_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.command_entry = ttk.Entry(self.command_frame, width=60, font=('Arial', 10))
        self.command_entry.grid(row=0, column=0, padx=5)
        
        self.add_button = ttk.Button(self.command_frame, 
                                   text="Ekle",
                                   style='Accent.TButton',
                                   command=self.add_command)
        self.add_button.grid(row=0, column=1, padx=5)
        
        # Komut listesi
        self.list_frame = ttk.LabelFrame(self.main_frame, text="Kayıtlı Komutlar", padding="10")
        self.list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Liste işlemleri için butonlar
        self.list_buttons_frame = ttk.Frame(self.list_frame)
        self.list_buttons_frame.grid(row=1, column=0, pady=(5,0))
        
        # Seçileni Çalıştır butonu
        self.run_selected_button = ttk.Button(self.list_buttons_frame,
                                           text="▶️ Seçileni Çalıştır",
                                           command=self.run_selected_command)
        self.run_selected_button.grid(row=0, column=0, padx=5)
        
        # Seçileni Düzenle butonu
        self.edit_button = ttk.Button(self.list_buttons_frame,
                                    text="✏️ Seçileni Düzenle",
                                    command=self.edit_selected_command)
        self.edit_button.grid(row=0, column=1, padx=5)
        
        self.delete_button = ttk.Button(self.list_buttons_frame,
                                      text="🗑 Seçileni Sil",
                                      command=self.delete_selected)
        self.delete_button.grid(row=0, column=2, padx=5)
        
        self.command_list = tk.Listbox(self.list_frame, 
                                     width=75,
                                     height=8,
                                     font=('Arial', 10),
                                     selectmode=tk.SINGLE,
                                     bg='white',
                                     selectbackground='#2196F3')
        self.command_list.grid(row=0, column=0, columnspan=3)
        
        # Çift tıklama ile komutu çalıştır
        self.command_list.bind('<Double-1>', lambda event: self.run_selected_command())
        
        # Sağ tıklama menüsü için olay bağla
        self.command_list.bind('<Button-3>', self.show_context_menu)
        
        # Scrollbar for listbox
        self.list_scrollbar = ttk.Scrollbar(self.list_frame, 
                                          orient=tk.VERTICAL, 
                                          command=self.command_list.yview)
        self.command_list.configure(yscrollcommand=self.list_scrollbar.set)
        self.list_scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        
        # Kontrol butonları
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=3, column=0, pady=10)
        
        # Tümünü Çalıştır butonu
        self.run_all_button = ttk.Button(self.button_frame,
                                       text="▶️▶️ Tümünü Çalıştır",
                                       command=self.run_all_commands)
        self.run_all_button.grid(row=0, column=0, padx=5)
        
        # Sıradaki Komutu Çalıştır butonu
        self.next_button = ttk.Button(self.button_frame,
                                    text="⏭ Sıradaki Komutu Çalıştır",
                                    command=self.run_next_command)
        self.next_button.grid(row=0, column=1, padx=5)
        
        # Temizle butonu
        self.clear_button = ttk.Button(self.button_frame, 
                                     text="🗑 Temizle",
                                     command=self.clear_list)
        self.clear_button.grid(row=0, column=2, padx=5)
        
        # Çıktı alanı
        self.output_frame = ttk.LabelFrame(self.main_frame, text="Çıktı", padding="10")
        self.output_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.output_area = scrolledtext.ScrolledText(
            self.output_frame,
            width=65,
            height=12,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#ffffff'
        )
        self.output_area.grid(row=0, column=0)
        
        # Başlangıç dizinini göster (CMD benzeri prompt)
        self.show_cmd_prompt()
        
        # Durum çubuğu frame'i
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=5, column=0, pady=(5, 0), sticky=(tk.W, tk.E))
        
        # Mevcut dizin göstergesi
        self.current_dir_label = tk.Label(self.status_frame,
                                        text=f"📁 {os.getcwd()}",
                                        font=('Consolas', 9),
                                        bg='#f0f0f0',
                                        fg='#0066cc')
        self.current_dir_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Durum mesajı
        self.status_label = tk.Label(self.status_frame,
                                    text="Hazır",
                                    font=('Arial', 9),
                                    bg='#f0f0f0',
                                    fg='#666666')
        self.status_label.pack(side=tk.LEFT)
        
        self.commands = []
        self.current_command_index = 0
        
        # Kaydedilmiş komutları yükle
        self.load_saved_commands()
        
        # İlerleme göstergesi
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.grid(row=6, column=0, pady=(5,0), sticky=(tk.W, tk.E))
        
        self.progress_label = tk.Label(self.progress_frame,
                                     text="0/0",
                                     font=('Arial', 9),
                                     bg='#f0f0f0',
                                     fg='#666666')
        self.progress_label.pack(side=tk.RIGHT)
        
        # Grid yapılandırması
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Pencere kapatılırken komutları kaydet
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_cmd_prompt(self):
        """CMD benzeri prompt göster"""
        self.output_area.insert(tk.END, f"{os.getcwd()}>")
        self.output_area.see(tk.END)

    def update_ui_safely(self, func, *args, **kwargs):
        """UI güncellemelerini ana thread üzerinden güvenli şekilde yap"""
        if not self.root.winfo_exists() or self.is_closing:
            return
        
        # Fonksiyonu ve parametrelerini kabul ederek ana thread'de çalıştır
        def wrapped_func():
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"UI güncelleme hatası: {str(e)}")
        
        try:
            self.root.after(0, wrapped_func)
        except tk.TclError as e:
            # Tcl interpreter kapatılmış olabilir
            print(f"Tcl hatası: {str(e)}")

    def load_saved_commands(self):
        """Kaydedilmiş komutları JSON dosyasından yükler"""
        try:
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r', encoding='utf-8') as f:
                    self.commands = json.load(f)
                    # Komutları listeye ekle
                    for cmd in self.commands:
                        self.command_list.insert(tk.END, cmd)
                    self.status_label.config(text=f"{len(self.commands)} komut yüklendi")
                    self.update_progress()
        except Exception as e:
            self.status_label.config(text=f"Komutlar yüklenirken hata: {str(e)}")

    def save_commands(self):
        """Komutları JSON dosyasına kaydeder"""
        try:
            with open(self.commands_file, 'w', encoding='utf-8') as f:
                json.dump(self.commands, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.status_label.config(text=f"Komutlar kaydedilirken hata: {str(e)}")

    def add_command(self):
        command = self.command_entry.get().strip()
        if command:
            self.commands.append(command)
            self.command_list.insert(tk.END, command)
            self.command_entry.delete(0, tk.END)
            self.status_label.config(text=f"Komut eklendi: {command}")
            self.save_commands()  # Yeni komut eklenince kaydet

    def update_progress(self):
        total = len(self.commands)
        self.progress_label.config(text=f"{self.current_command_index}/{total}")

    def handle_cd_command(self, command):
        """CD komutunu CMD gibi işler"""
        # CD komutunu ayıkla
        cd_args = command[2:].strip()
        
        try:
            # Sadece 'cd' yazıldıysa mevcut dizini göster
            if not cd_args:
                return f"Geçerli dizin: {os.getcwd()}\n", True
                
            # cd .. (üst dizine git)
            elif cd_args == "..":
                os.chdir("..")
                
            # cd / veya cd \ (kök dizine git)
            elif cd_args == "/" or cd_args == "\\":
                # Windows'ta kök dizine git
                os.chdir(os.path.abspath(os.path.splitdrive(os.getcwd())[0] + "\\"))
                
            # cd /d X: veya cd X: (sürücü değiştir)
            elif "/d" in cd_args.lower() and ":" in cd_args:
                drive = cd_args.split()[-1]
                os.chdir(drive)
            elif len(cd_args) == 2 and cd_args[1] == ":":
                os.chdir(cd_args)
                
            # Normal dizin değişimi
            else:
                # Tırnak işaretlerini temizle (varsa)
                if (cd_args.startswith('"') and cd_args.endswith('"')) or \
                   (cd_args.startswith("'") and cd_args.endswith("'")):
                    cd_args = cd_args[1:-1]
                
                # Dizini değiştir
                os.chdir(os.path.abspath(os.path.expanduser(cd_args)))
            
            return "", True  # Başarılı, çıktı yok (CMD gibi)
            
        except Exception as e:
            return f"Dizin değiştirme hatası: {str(e)}\n", False

    def execute_command(self, command):
        """Herhangi bir komutu çalıştır (seçilen veya sıradaki)"""
        try:
            # Komut başlangıcını göster (CMD gibi)
            self.root.after(0, lambda: [
                self.output_area.insert(tk.END, f"{command}\n")
            ])
            
            try:
                # CD komutunu özel olarak işle
                if command.strip().lower().startswith('cd ') or command.strip().lower() == 'cd':
                    output, success = self.handle_cd_command(command)
                    
                    def show_cd_result():
                        if output:  # Sadece çıktı varsa göster
                            self.output_area.insert(tk.END, output)
                        
                        # Dizin bilgisini güncelle
                        self.update_current_dir_display()
                        
                        # CMD benzeri prompt göster
                        self.show_cmd_prompt()
                    
                    self.root.after(0, show_cd_result)
                    
                else:
                    # Diğer komutları çalıştır
                    process = subprocess.run(
                        f'cmd /c {command}',
                        shell=True,
                        capture_output=True,
                        text=True,
                        encoding='cp857',  # Türkçe karakter desteği için
                        errors='replace',
                        cwd=os.getcwd()  # Güncel dizini kullan
                    )
                    
                    def show_cmd_output():
                        # Çıktıları göster
                        if process.stdout:
                            self.output_area.insert(tk.END, f"{process.stdout}")
                            
                        if process.stderr:
                            self.output_area.insert(tk.END, f"{process.stderr}")
                            
                        # CMD benzeri prompt göster
                        self.show_cmd_prompt()
                        self.output_area.see(tk.END)
                    
                    self.root.after(0, show_cmd_output)
                
            except Exception as e:
                self.root.after(0, lambda: [
                    self.output_area.insert(tk.END, f"Hata: {str(e)}\n"),
                    self.show_cmd_prompt(),
                    self.status_label.config(text="Hata oluştu!")
                ])
                
            return True  # Başarılı çalıştırma
                
        except Exception as e:
            self.root.after(0, lambda: [
                self.output_area.insert(tk.END, f"Komut çalıştırma hatası: {str(e)}\n"),
                self.show_cmd_prompt()
            ])
            return False  # Başarısız çalıştırma

    def run_selected_command(self):
        """Listede seçili olan komutu çalıştır"""
        selection = self.command_list.curselection()
        if not selection:
            self.status_label.config(text="Lütfen bir komut seçin!")
            return
            
        index = selection[0]
        command = self.commands[index]
        
        # UI'ı başlangıç durumuna getir
        self.run_selected_button.state(['disabled'])
        self.next_button.state(['disabled'])
        self.run_all_button.state(['disabled'])
        
        def execute_selected():
            try:
                success = self.execute_command(command)
                
                # UI'ı güncelle
                def finish():
                    self.run_selected_button.state(['!disabled'])
                    self.next_button.state(['!disabled'])
                    self.run_all_button.state(['!disabled'])
                    if success:
                        self.status_label.config(text=f"Seçili komut çalıştırıldı: {command}")
                    else:
                        self.status_label.config(text=f"Seçili komut çalıştırılırken hata oluştu")
                
                self.root.after(0, finish)
                
            except Exception as e:
                # UI'ı güncelle
                def show_error():
                    self.run_selected_button.state(['!disabled'])
                    self.next_button.state(['!disabled'])
                    self.run_all_button.state(['!disabled'])
                    self.status_label.config(text=f"Hata: {str(e)}")
                
                self.root.after(0, show_error)
        
        # Thread'i başlat
        threading.Thread(target=execute_selected, daemon=True).start()

    def run_next_command(self):
        if not self.commands:
            self.status_label.config(text="Çalıştırılacak komut bulunamadı!")
            return
        
        if self.current_command_index >= len(self.commands):
            self.status_label.config(text="Tüm komutlar tamamlandı!")
            self.current_command_index = 0
            self.update_progress()
            # Seçimi temizle
            self.command_list.selection_clear(0, tk.END)
            return
        
        # Çalışacak komutu listede seç
        self.command_list.selection_clear(0, tk.END)
        self.command_list.selection_set(self.current_command_index)
        self.command_list.see(self.current_command_index)  # Seçili komutu görünür yap
        
        command = self.commands[self.current_command_index]
        
        # UI'ı başlangıç durumuna getir
        self.run_selected_button.state(['disabled'])
        self.next_button.state(['disabled'])
        self.run_all_button.state(['disabled'])
        
        def execute_next():
            try:
                success = self.execute_command(command)
                
                # UI'ı güncelle
                def finish():
                    self.run_selected_button.state(['!disabled'])
                    self.next_button.state(['!disabled'])
                    self.run_all_button.state(['!disabled'])
                    self.current_command_index += 1
                    self.update_progress()
                    if success:
                        self.status_label.config(text=f"Komut tamamlandı: {command}")
                    else:
                        self.status_label.config(text=f"Komut çalıştırılırken hata oluştu")
                    self.output_area.see(tk.END)
                
                self.root.after(0, finish)
                
            except Exception as e:
                # UI'ı güncelle
                def show_error():
                    self.run_selected_button.state(['!disabled'])
                    self.next_button.state(['!disabled'])
                    self.run_all_button.state(['!disabled'])
                    self.current_command_index += 1  # Yine de ilerle
                    self.update_progress()
                    self.status_label.config(text=f"Hata: {str(e)}")
                
                self.root.after(0, show_error)
        
        # Thread'i başlat
        threading.Thread(target=execute_next, daemon=True).start()
        
    def run_all_commands(self):
        """Tüm komutları sırayla çalıştırır"""
        if not self.commands:
            self.status_label.config(text="Çalıştırılacak komut bulunamadı!")
            return
        
        # İlerleme sayacını sıfırla
        self.current_command_index = 0
        self.update_progress()
        
        # UI butonlarını devre dışı bırak
        self.run_selected_button.state(['disabled'])
        self.next_button.state(['disabled'])
        self.run_all_button.state(['disabled'])
        
        def run_commands_recursively():
            if self.current_command_index >= len(self.commands) or self.is_closing:
                # Tüm komutlar tamamlandığında butonları aktif et
                def enable_buttons():
                    self.run_selected_button.state(['!disabled'])
                    self.next_button.state(['!disabled'])
                    self.run_all_button.state(['!disabled'])
                    self.status_label.config(text="Tüm komutlar tamamlandı!")
                
                self.root.after(0, enable_buttons)
                return
            
            # Çalışacak komutu listede seç
            self.command_list.selection_clear(0, tk.END)
            self.command_list.selection_set(self.current_command_index)
            self.command_list.see(self.current_command_index)
            
            command = self.commands[self.current_command_index]
            
            def execute_and_continue():
                try:
                    success = self.execute_command(command)
                    
                    # Sıradaki komuta geç
                    def next_command():
                        self.current_command_index += 1
                        self.update_progress()
                        # Bir sonraki komuta geçmeden önce kısa bir gecikme ekle
                        self.root.after(500, run_commands_recursively)
                    
                    self.root.after(0, next_command)
                    
                except Exception as e:
                    # Hata durumunda bir sonraki komuta geç
                    def handle_error():
                        self.output_area.insert(tk.END, f"Hata: {str(e)}\n")
                        self.show_cmd_prompt()
                        self.current_command_index += 1
                        self.update_progress()
                        # Bir sonraki komuta geçmeden önce kısa bir gecikme ekle
                        self.root.after(500, run_commands_recursively)
                    
                    self.root.after(0, handle_error)
            
            # Komutu çalıştır
            threading.Thread(target=execute_and_continue, daemon=True).start()
        
        # İlk komutu başlat
        run_commands_recursively()

    def clear_list(self):
        # Onay penceresi göster
        if messagebox.askokcancel("Onay", "Tüm komutları silmek istediğinize emin misiniz?"):
            self.command_list.delete(0, tk.END)
            self.commands.clear()
            self.output_area.delete(1.0, tk.END)
            self.current_command_index = 0
            self.update_progress()
            self.status_label.config(text="Liste temizlendi")
            self.save_commands()  # Liste temizlenince kaydet
            # Temizlikten sonra yeni prompt göster
            self.show_cmd_prompt()

    def delete_selected(self):
        """Seçili komutu listeden siler"""
        selection = self.command_list.curselection()
        if selection:
            index = selection[0]
            self.command_list.delete(index)
            self.commands.pop(index)
            self.save_commands()
            self.status_label.config(text="Seçili komut silindi")
            
            # Eğer silinen komut, mevcut sıradaki komuttan önceyse indeksi güncelle
            if index < self.current_command_index:
                self.current_command_index -= 1
                
            # Eğer son komut silindiyse ve sıradaki komut indeksi sınırın dışına çıktıysa düzelt
            if self.current_command_index >= len(self.commands) and len(self.commands) > 0:
                self.current_command_index = len(self.commands) - 1
                
            self.update_progress()

    def edit_selected_command(self):
        """Seçili komutu düzenler"""
        selection = self.command_list.curselection()
        if not selection:
            self.status_label.config(text="Lütfen düzenlenecek bir komut seçin!")
            return
            
        index = selection[0]
        current_command = self.commands[index]
        
        # Düzenleme dialogu oluştur
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Komutu Düzenle")
        edit_window.geometry("500x120")
        edit_window.resizable(False, False)
        edit_window.transient(self.root)  # Ana pencereye bağlı olarak göster
        edit_window.grab_set()  # Modalı zorla
        
        # Pencere içeriği
        edit_frame = ttk.Frame(edit_window, padding="10")
        edit_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(edit_frame, text="Komutu düzenleyin:").pack(anchor=tk.W, pady=(0, 5))
        
        # Düzenleme alanı
        edit_entry = ttk.Entry(edit_frame, width=80, font=('Arial', 10))
        edit_entry.pack(fill=tk.X, padx=5, pady=5)
        edit_entry.insert(0, current_command)
        edit_entry.select_range(0, tk.END)
        edit_entry.focus_set()
        
        # Butonlar için frame
        button_frame = ttk.Frame(edit_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # İptal ve Kaydet butonları
        cancel_button = ttk.Button(
            button_frame, 
            text="İptal", 
            command=edit_window.destroy
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        def save_edited():
            edited_command = edit_entry.get().strip()
            if edited_command:
                # Komutu güncelle
                self.commands[index] = edited_command
                # Listboxta göster
                self.command_list.delete(index)
                self.command_list.insert(index, edited_command)
                self.command_list.selection_set(index)
                # Komutları kaydet
                self.save_commands()
                self.status_label.config(text=f"Komut düzenlendi: {edited_command}")
            edit_window.destroy()
        
        save_button = ttk.Button(
            button_frame, 
            text="Kaydet", 
            command=save_edited
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # Enter tuşuyla kaydetme
        edit_window.bind("<Return>", lambda event: save_edited())
        
        # Escape tuşuyla iptal
        edit_window.bind("<Escape>", lambda event: edit_window.destroy())
        
        # Pencereyi ortala
        edit_window.update_idletasks()
        width = edit_window.winfo_width()
        height = edit_window.winfo_height()
        x = (edit_window.winfo_screenwidth() // 2) - (width // 2)
        y = (edit_window.winfo_screenheight() // 2) - (height // 2)
        edit_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def show_context_menu(self, event):
        """Sağ tıklama menüsünü gösterir"""
        # Önce tıklanan öğeyi seç
        clicked_index = self.command_list.nearest(event.y)
        if clicked_index >= 0:
            self.command_list.selection_clear(0, tk.END)
            self.command_list.selection_set(clicked_index)
            self.command_list.activate(clicked_index)
            
            # Menü oluştur
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Çalıştır", command=self.run_selected_command)
            context_menu.add_command(label="Düzenle", command=self.edit_selected_command)
            context_menu.add_command(label="Sil", command=self.delete_selected)
            context_menu.add_separator()
            context_menu.add_command(label="Tümünü Temizle", command=self.clear_list)
            
            # Menüyü göster
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

    def on_closing(self):
        """Uygulama kapanırken temizlik yap"""
        self.is_closing = True
        self.save_commands()
        self.root.destroy()

    def update_current_dir_display(self):
        """Mevcut dizin göstergesini güncelle"""
        try:
            current_dir = os.getcwd()
            self.update_ui_safely(
                lambda: self.current_dir_label.config(text=f"📁 {current_dir}")
            )
        except Exception as e:
            print(f"Dizin göstergesi güncellenirken hata: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CommandRunner(root)
    root.mainloop()