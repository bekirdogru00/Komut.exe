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
        self.root.geometry("600x600")
        
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
        
        self.delete_button = ttk.Button(self.list_buttons_frame,
                                      text="🗑 Seçileni Sil",
                                      command=self.delete_selected)
        self.delete_button.grid(row=0, column=0, padx=5)
        
        self.edit_button = ttk.Button(self.list_buttons_frame,
                                    text="✏️ Düzenle",
                                    command=self.edit_selected)
        self.edit_button.grid(row=0, column=1, padx=5)
        
        self.command_list = tk.Listbox(self.list_frame, 
                                     width=75,
                                     height=8,
                                     font=('Arial', 10),
                                     selectmode=tk.SINGLE,
                                     bg='white',
                                     selectbackground='#2196F3')
        self.command_list.grid(row=0, column=0, columnspan=2)
        
        # Scrollbar for listbox
        self.list_scrollbar = ttk.Scrollbar(self.list_frame, 
                                          orient=tk.VERTICAL, 
                                          command=self.command_list.yview)
        self.command_list.configure(yscrollcommand=self.list_scrollbar.set)
        self.list_scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        
        # Kontrol butonları
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=3, column=0, pady=10)
        
        self.run_button = ttk.Button(self.button_frame, 
                                   text="▶ Hepsini Çalıştır",
                                   style='Accent.TButton',
                                   command=self.run_commands)
        self.run_button.grid(row=0, column=0, padx=5)
        
        self.run_selected_button = ttk.Button(self.button_frame,
                                            text="▶️ Seçileni Çalıştır",
                                            command=self.run_selected_command)
        self.run_selected_button.grid(row=0, column=1, padx=5)
        
        self.next_button = ttk.Button(self.button_frame,
                                    text="⏭ Tek tek çalıştır",
                                    command=self.run_next_command)
        self.next_button.grid(row=0, column=2, padx=5)
        
        self.clear_button = ttk.Button(self.button_frame, 
                                     text="🗑 Temizle",
                                     command=self.clear_list)
        self.clear_button.grid(row=0, column=3, padx=5)
        
        # Çıktı alanı
        self.output_frame = ttk.LabelFrame(self.main_frame, text="Çıktı", padding="10")
        self.output_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.output_area = scrolledtext.ScrolledText(
            self.output_frame,
            width=65,
            height=10,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#ffffff'
        )
        self.output_area.grid(row=0, column=0)
        
        # Bekleme animasyonu için tag oluştur
        self.output_area.tag_configure("waiting", foreground="yellow")
        
        # Durum çubuğu
        self.status_label = tk.Label(self.main_frame,
                                   text="Hazır",
                                   font=('Arial', 9),
                                   bg='#f0f0f0',
                                   fg='#666666')
        self.status_label.grid(row=5, column=0, pady=(5, 0), sticky=tk.W)
        
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

    def run_commands(self):
        if not self.commands:
            self.status_label.config(text="Çalıştırılacak komut bulunamadı!")
            return

        # UI'ı başlangıç durumuna getir
        self.output_area.delete(1.0, tk.END)
        self.run_button.state(['disabled'])
        self.run_selected_button.state(['disabled'])
        self.next_button.state(['disabled'])
        self.current_command_index = 0
        self.status_label.config(text="Komutlar çalıştırılıyor...")

        def run_single_command(command, index):
            """Tek bir komutu çalıştır"""
            try:
                # Komut başlangıcını göster
                self.root.after(0, lambda: [
                    self.output_area.insert(tk.END, f"\n📌 Komut çalıştırılıyor: {command}\n{'='*50}\n"),
                    self.status_label.config(text=f"Komut çalıştırılıyor... (bekleyin)")
                ])

                # Bekleme satırını ekle
                self.root.after(0, lambda: self.output_area.insert(tk.END, "\nBekleniyor ", "waiting"))
                self.root.after(0, lambda: self.output_area.insert(tk.END, "⋯", ("waiting", "dots")))
                
                # Animasyonlu bekleme göstergesi
                dots = ["⋯", "⋯⋯", "⋯⋯⋯"]
                dot_index = 0
                
                def update_waiting():
                    nonlocal dot_index
                    if not hasattr(self, '_command_finished'):
                        try:
                            # Önce mevcut noktaları bul ve sil
                            try:
                                self.output_area.delete("dots.first", "dots.last")
                            except tk.TclError:
                                pass  # Tag bulunamazsa geç
                            
                            # Yeni noktaları ekle
                            self.root.after(0, lambda: 
                                self.output_area.insert(tk.END, dots[dot_index], ("waiting", "dots"))
                            )
                            
                            dot_index = (dot_index + 1) % len(dots)
                            self.root.after(500, update_waiting)
                        except Exception:
                            pass  # Herhangi bir hata olursa sessizce devam et
                
                # Bekleme animasyonunu başlat
                update_waiting()

                # Komutu çalıştır
                process = subprocess.run(
                    f'cmd /c {command}',
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='cp857',
                    errors='replace'
                )

                # Bekleme animasyonunu temizle
                self._command_finished = True
                def clear_waiting():
                    try:
                        # Önce dots tag'ini temizle
                        try:
                            self.output_area.delete("dots.first", "dots.last")
                        except tk.TclError:
                            pass
                            
                        # Sonra waiting tag'ini temizle
                        try:
                            self.output_area.delete("waiting.first", "waiting.last")
                        except tk.TclError:
                            pass
                            
                        self.status_label.config(text="Komut tamamlandı")
                    except Exception:
                        pass

                self.root.after(0, clear_waiting)

                # Çıktıları göster
                if process.stdout:
                    def show_output():
                        self.output_area.insert(tk.END, f"✅ Çıktı:\n{process.stdout}\n")
                        self.output_area.see(tk.END)  # Sadece yeni çıktı eklendiğinde kaydır
                    self.root.after(0, show_output)

                if process.stderr:
                    def show_error():
                        self.output_area.insert(tk.END, f"⚠️ Uyarı:\n{process.stderr}\n")
                        self.output_area.see(tk.END)  # Sadece yeni çıktı eklendiğinde kaydır
                    self.root.after(0, show_error)

                # İlerlemeyi güncelle
                self.root.after(0, lambda: [
                    setattr(self, 'current_command_index', index + 1),
                    self.update_progress(),
                    self.output_area.see(tk.END)
                ])

                return True

            except Exception as e:
                self.root.after(0, lambda: [
                    self.output_area.insert(tk.END, f"❌ Hata: {str(e)}\n"),
                    self.status_label.config(text="Hata oluştu!")
                ])
                return False

            finally:
                # Bekleme durumunu temizle
                if hasattr(self, '_command_finished'):
                    delattr(self, '_command_finished')

        def execute():
            try:
                for i, cmd in enumerate(self.commands):
                    if self.is_closing:
                        break
                    
                    # Her komut için bekle
                    success = run_single_command(cmd, i)
                    if not success:
                        break
                    
                    # Komutlar arası kısa bekleme
                    self.root.after(100)

            finally:
                # UI'ı sıfırla
                self.root.after(0, lambda: [
                    self.run_button.state(['!disabled']),
                    self.run_selected_button.state(['!disabled']),
                    self.next_button.state(['!disabled']),
                    self.status_label.config(text="Tüm komutlar tamamlandı")
                ])

        # Thread'i başlat
        threading.Thread(target=execute, daemon=True).start()

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
        self.run_button.state(['disabled'])
        self.run_selected_button.state(['disabled'])
        self.next_button.state(['disabled'])
        
        def execute():
            try:
                # Komut başlangıcını göster
                self.root.after(0, lambda: [
                    self.output_area.insert(tk.END, f"\n📌 Komut çalıştırılıyor: {command}\n{'='*50}\n"),
                    self.status_label.config(text=f"Komut çalıştırılıyor... (bekleyin)")
                ])
                
                # Bekleme satırını ekle
                self.root.after(0, lambda: self.output_area.insert(tk.END, "\nBekleniyor ", "waiting"))
                self.root.after(0, lambda: self.output_area.insert(tk.END, "⋯", ("waiting", "dots")))
                
                # Animasyonlu bekleme göstergesi
                dots = ["⋯", "⋯⋯", "⋯⋯⋯"]
                dot_index = 0
                
                def update_waiting():
                    nonlocal dot_index
                    if not hasattr(self, '_command_finished'):
                        try:
                            # Önce mevcut noktaları bul ve sil
                            try:
                                self.output_area.delete("dots.first", "dots.last")
                            except tk.TclError:
                                pass  # Tag bulunamazsa geç
                            
                            # Yeni noktaları ekle
                            self.root.after(0, lambda: 
                                self.output_area.insert(tk.END, dots[dot_index], ("waiting", "dots"))
                            )
                            
                            dot_index = (dot_index + 1) % len(dots)
                            self.root.after(500, update_waiting)
                        except Exception:
                            pass  # Herhangi bir hata olursa sessizce devam et
                
                # Bekleme animasyonunu başlat
                update_waiting()
                
                try:
                    # Komutu çalıştır
                    process = subprocess.run(
                        f'cmd /c {command}',
                        shell=True,
                        capture_output=True,
                        text=True,
                        encoding='cp857',
                        errors='replace'
                    )
                    
                    # Bekleme animasyonunu temizle
                    self._command_finished = True
                    def clear_waiting():
                        try:
                            # Önce dots tag'ini temizle
                            try:
                                self.output_area.delete("dots.first", "dots.last")
                            except tk.TclError:
                                pass
                                
                            # Sonra waiting tag'ini temizle
                            try:
                                self.output_area.delete("waiting.first", "waiting.last")
                            except tk.TclError:
                                pass
                                
                            self.status_label.config(text="Komut tamamlandı")
                        except Exception:
                            pass

                    self.root.after(0, clear_waiting)
                    
                    # Çıktıları göster
                    if process.stdout:
                        def show_output():
                            self.output_area.insert(tk.END, f"✅ Çıktı:\n{process.stdout}\n")
                            self.output_area.see(tk.END)  # Sadece yeni çıktı eklendiğinde kaydır
                        self.root.after(0, show_output)

                    if process.stderr:
                        def show_error():
                            self.output_area.insert(tk.END, f"⚠️ Uyarı:\n{process.stderr}\n")
                            self.output_area.see(tk.END)  # Sadece yeni çıktı eklendiğinde kaydır
                        self.root.after(0, show_error)
                    
                except Exception as e:
                    self.root.after(0, lambda: [
                        self.output_area.insert(tk.END, f"❌ Hata: {str(e)}\n"),
                        self.status_label.config(text="Hata oluştu!")
                    ])
                
            finally:
                # Bekleme durumunu temizle
                if hasattr(self, '_command_finished'):
                    delattr(self, '_command_finished')
                
                # UI'ı güncelle
                def finish():
                    self.run_button.state(['!disabled'])
                    self.run_selected_button.state(['!disabled'])
                    self.next_button.state(['!disabled'])
                    self.current_command_index += 1
                    self.update_progress()
                    self.status_label.config(text=f"Komut tamamlandı: {command}")
                    self.output_area.see(tk.END)
                
                self.root.after(0, finish)
        
        # Thread'i başlat
        threading.Thread(target=execute, daemon=True).start()

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

    def delete_selected(self):
        """Seçili komutu listeden siler"""
        selection = self.command_list.curselection()
        if selection:
            index = selection[0]
            self.command_list.delete(index)
            self.commands.pop(index)
            self.save_commands()
            self.status_label.config(text="Seçili komut silindi")
            self.update_progress()

    def edit_selected(self):
        """Seçili komutu düzenler"""
        selection = self.command_list.curselection()
        if selection:
            index = selection[0]
            old_command = self.commands[index]
            
            # Düzenleme penceresi
            edit_window = tk.Toplevel(self.root)
            edit_window.title("Komutu Düzenle")
            edit_window.geometry("400x100")
            
            edit_frame = ttk.Frame(edit_window, padding="10")
            edit_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            edit_entry = ttk.Entry(edit_frame, width=50)
            edit_entry.insert(0, old_command)
            edit_entry.grid(row=0, column=0, padx=5, pady=5)
            
            def save_edit():
                new_command = edit_entry.get().strip()
                if new_command:
                    self.commands[index] = new_command
                    self.command_list.delete(index)
                    self.command_list.insert(index, new_command)
                    self.save_commands()
                    self.status_label.config(text="Komut düzenlendi")
                edit_window.destroy()
            
            save_button = ttk.Button(edit_frame, text="Kaydet", command=save_edit)
            save_button.grid(row=1, column=0, pady=5)

    def run_selected_command(self):
        """Seçili komutu çalıştırır"""
        selection = self.command_list.curselection()
        if not selection:
            self.status_label.config(text="Lütfen çalıştırılacak bir komut seçin!")
            return
        
        index = selection[0]
        command = self.commands[index]
        
        # UI'ı başlangıç durumuna getir
        self.run_button.state(['disabled'])
        self.run_selected_button.state(['disabled'])
        self.next_button.state(['disabled'])
        
        def execute():
            try:
                # Komut başlangıcını göster
                self.root.after(0, lambda: [
                    self.output_area.insert(tk.END, f"\n📌 Seçili komut çalıştırılıyor: {command}\n{'='*50}\n"),
                    self.status_label.config(text=f"Komut çalıştırılıyor... (bekleyin)")
                ])
                
                # Bekleme satırını ekle
                self.root.after(0, lambda: self.output_area.insert(tk.END, "\nBekleniyor ", "waiting"))
                self.root.after(0, lambda: self.output_area.insert(tk.END, "⋯", ("waiting", "dots")))
                
                # Animasyonlu bekleme göstergesi
                dots = ["⋯", "⋯⋯", "⋯⋯⋯"]
                dot_index = 0
                
                def update_waiting():
                    nonlocal dot_index
                    if not hasattr(self, '_command_finished'):
                        try:
                            # Önce mevcut noktaları bul ve sil
                            try:
                                self.output_area.delete("dots.first", "dots.last")
                            except tk.TclError:
                                pass  # Tag bulunamazsa geç
                            
                            # Yeni noktaları ekle
                            self.root.after(0, lambda: 
                                self.output_area.insert(tk.END, dots[dot_index], ("waiting", "dots"))
                            )
                            
                            dot_index = (dot_index + 1) % len(dots)
                            self.root.after(500, update_waiting)
                        except Exception:
                            pass  # Herhangi bir hata olursa sessizce devam et
                
                # Bekleme animasyonunu başlat
                update_waiting()
                
                try:
                    # Komutu çalıştır
                    process = subprocess.run(
                        f'cmd /c {command}',
                        shell=True,
                        capture_output=True,
                        text=True,
                        encoding='cp857',
                        errors='replace'
                    )
                    
                    # Bekleme animasyonunu temizle
                    self._command_finished = True
                    def clear_waiting():
                        try:
                            # Önce dots tag'ini temizle
                            try:
                                self.output_area.delete("dots.first", "dots.last")
                            except tk.TclError:
                                pass
                                
                            # Sonra waiting tag'ini temizle
                            try:
                                self.output_area.delete("waiting.first", "waiting.last")
                            except tk.TclError:
                                pass
                                
                            self.status_label.config(text="Komut tamamlandı")
                        except Exception:
                            pass

                    self.root.after(0, clear_waiting)
                    
                    # Çıktıları göster
                    if process.stdout:
                        def show_output():
                            self.output_area.insert(tk.END, f"✅ Çıktı:\n{process.stdout}\n")
                            self.output_area.see(tk.END)
                        self.root.after(0, show_output)

                    if process.stderr:
                        def show_error():
                            self.output_area.insert(tk.END, f"⚠️ Uyarı:\n{process.stderr}\n")
                            self.output_area.see(tk.END)
                        self.root.after(0, show_error)
                    
                except Exception as e:
                    self.root.after(0, lambda: [
                        self.output_area.insert(tk.END, f"❌ Hata: {str(e)}\n"),
                        self.status_label.config(text="Hata oluştu!")
                    ])
                
            finally:
                # Bekleme durumunu temizle
                if hasattr(self, '_command_finished'):
                    delattr(self, '_command_finished')
                
                # UI'ı güncelle
                def finish():
                    self.run_button.state(['!disabled'])
                    self.run_selected_button.state(['!disabled'])
                    self.next_button.state(['!disabled'])
                    self.status_label.config(text=f"Seçili komut tamamlandı: {command}")
                    self.output_area.see(tk.END)
                
                self.root.after(0, finish)
        
        # Thread'i başlat
        threading.Thread(target=execute, daemon=True).start()

    def run_command_with_output(self, command):
        """Özel komutlar için çıktı alma yöntemi"""
        try:
            # Önce normal yöntem
            process = subprocess.run(
                f'cmd /c {command}',
                shell=True,
                capture_output=True,
                text=True,
                encoding='cp857',
                errors='replace'
            )
            
            if process.stdout or process.stderr:
                return process.stdout, process.stderr
            
            # Normal yöntem çalışmazsa, alternatif yöntem
            process = subprocess.run(
                f'cmd /c {command}',
                shell=True,
                capture_output=True,
                text=True,
                encoding='cp857',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            return process.stdout, process.stderr
            
        except Exception as e:
            return None, str(e)
    
    def on_closing(self):
        """Uygulama kapanırken temizlik yap"""
        self.is_closing = True  # Thread'lere kapanma sinyali gönder
        self.save_commands()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CommandRunner(root)
    root.mainloop()