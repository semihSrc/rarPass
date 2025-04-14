import os
import zipfile
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

class ExtractTRFolders:
    def __init__(self, root):
        self.root = root
        self.root.title("TR Klasör Çıkarıcı")
        self.root.geometry("600x350")
        self.rar_path = ""
        self.passlist_path = ""
        self.winrar_path = self.find_winrar()
        self.cancel_process = False

        # Arayüz bileşenleri
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="🔐 TR Klasör Çıkarıcı", font=("Arial", 16, "bold")).pack(pady=10)

        # Dosya seçme butonları
        tk.Button(self.root, text="📁 RAR/ZIP Dosyası Seç", command=self.select_archive, width=30).pack(pady=5)
        self.label_archive = tk.Label(self.root, text="Dosya seçilmedi", wraplength=500)
        self.label_archive.pack()

        tk.Button(self.root, text="📄 Şifre Listesi Seç (.txt)", command=self.select_passlist, width=30).pack(pady=5)
        self.label_pass = tk.Label(self.root, text="Şifre listesi seçilmedi", wraplength=500)
        self.label_pass.pack()

        # İşlem butonları
        self.start_button = tk.Button(self.root, text="🚀 Çıkartmaya Başla", command=self.start_extraction, bg="#b3ffcc", width=30)
        self.start_button.pack(pady=10)
        
        self.cancel_button = tk.Button(self.root, text="❌ İptal", command=self.cancel_extraction, bg="#ffb3b3", width=30, state=tk.DISABLED)
        self.cancel_button.pack(pady=5)

        # Durum bilgisi
        self.label_progress = tk.Label(self.root, text="", fg="gray")
        self.label_progress.pack()
        
        self.label_result = tk.Label(self.root, text="", fg="blue")
        self.label_result.pack()

    def find_winrar(self):
        """WinRAR'ı otomatik bulmaya çalışır"""
        possible_paths = [
            r"C:\Program Files\WinRAR\WinRAR.exe",
            r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
            os.path.join(os.environ.get("PROGRAMFILES", ""), "WinRAR", "WinRAR.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "WinRAR", "WinRAR.exe")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return "WinRAR.exe"

    def select_archive(self):
        self.rar_path = filedialog.askopenfilename(
            filetypes=[("Arşiv Dosyaları", "*.rar *.zip"), ("RAR dosyası", "*.rar"), ("ZIP dosyası", "*.zip")])
        self.label_archive.config(text=self.rar_path)

    def select_passlist(self):
        self.passlist_path = filedialog.askopenfilename(filetypes=[("Metin Dosyası", "*.txt")])
        self.label_pass.config(text=self.passlist_path)

    def start_extraction(self):
        if not self.rar_path or not self.passlist_path:
            messagebox.showwarning("Uyarı", "Lütfen dosya ve şifre listesi seçin.")
            return

        self.cancel_process = False
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.label_result.config(text="")
        self.label_progress.config(text="Hazırlanıyor...")
        self.root.update()

        self.root.after(100, self.extract_folders)

    def cancel_extraction(self):
        self.cancel_process = True
        self.label_progress.config(text="İşlem iptal ediliyor...")
        self.cancel_button.config(state=tk.DISABLED)

    def extract_folders(self):
        output_dir = os.path.join(os.path.dirname(self.rar_path), "extracted_tr")
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        try:
            with open(self.passlist_path, 'r', encoding='utf-8') as file:
                passwords = [line.strip() for line in file if line.strip()]
        except Exception as e:
            messagebox.showerror("Hata", f"Şifre listesi okunamadı: {e}")
            self.reset_ui()
            return

        total_passwords = len(passwords)
        correct_pwd = None
        folder_found = False

        for index, pwd in enumerate(passwords):
            if self.cancel_process:
                self.label_progress.config(text="İşlem iptal edildi")
                break

            self.label_progress.config(
                text=f"Denenen şifre: {pwd} ({index+1}/{total_passwords})"
            )
            self.root.update()

            if self.rar_path.lower().endswith('.rar'):
                success = self.extract_rar(output_dir, pwd)
            else:
                success = self.extract_zip(output_dir, pwd)

            if success:
                correct_pwd = pwd
                folder_found = True
                break

        if folder_found:
            if correct_pwd == passwords[0]:
                result_text = "Doğru Şifre: Şifresiz (ilk deneme)"
            else:
                result_text = f"Doğru Şifre: {correct_pwd}"
                
            self.label_result.config(text=f"✅ Başarılı! {result_text}")
            messagebox.showinfo("Başarılı", f"TR klasörü çıkarıldı!\n{result_text}")
        else:
            if not self.cancel_process:
                self.label_result.config(text="❌ TR klasörü bulunamadı veya doğru şifre yok")
                messagebox.showinfo("Bilgi", "TR klasörü bulunamadı veya doğru şifre bulunamadı.")

        self.reset_ui()

    def reset_ui(self):
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.cancel_process = False

    def extract_rar(self, output_dir, password):
        try:
            temp_dir = os.path.join(output_dir, f"temp_{password}")
            os.makedirs(temp_dir, exist_ok=True)
            
            result = subprocess.run(
                [self.winrar_path, 'x', f'-p{password}', '-y', '-ibck', self.rar_path, temp_dir],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if not os.listdir(temp_dir):
                shutil.rmtree(temp_dir)
                return False
                
            if self.check_and_move_tr_folders(temp_dir, output_dir):
                shutil.rmtree(temp_dir)
                return True
                
            shutil.rmtree(temp_dir)
            return False
        except Exception as e:
            self.label_progress.config(text=f"Hata oluştu: {str(e)[:100]}...")
            return False

    def extract_zip(self, output_dir, password):
        try:
            temp_dir = os.path.join(output_dir, f"temp_{password}")
            os.makedirs(temp_dir, exist_ok=True)
            
            with zipfile.ZipFile(self.rar_path, 'r') as zip_ref:
                if password:
                    zip_ref.setpassword(password.encode())
                zip_ref.extractall(temp_dir)
                
            if not os.listdir(temp_dir):
                shutil.rmtree(temp_dir)
                return False
                
            if self.check_and_move_tr_folders(temp_dir, output_dir):
                shutil.rmtree(temp_dir)
                return True
                
            shutil.rmtree(temp_dir)
            return False
        except RuntimeError as e:
            if 'Bad password' in str(e):
                return False
            self.label_progress.config(text=f"ZIP hatası: {str(e)[:100]}...")
            return False
        except Exception as e:
            self.label_progress.config(text=f"Hata oluştu: {str(e)[:100]}...")
            return False

    def check_and_move_tr_folders(self, source_dir, target_dir):
        """Sadece adında 'tr' geçen klasörleri taşır"""
        tr_found = False
        
        for root, dirs, files in os.walk(source_dir):
            for dir_name in dirs:
                lower_name = dir_name.lower()
                # 't' ve 'r' harflerinin yan yana olduğunu kontrol et
                if any(lower_name[i] == 't' and lower_name[i+1] == 'r' for i in range(len(lower_name)-1)):
                    src_path = os.path.join(root, dir_name)
                    dest_path = os.path.join(target_dir, dir_name)
                    
                    # Hedef varsa sil
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    
                    shutil.move(src_path, target_dir)
                    self.label_progress.config(text=f"TR klasörü bulundu: {dir_name}")
                    tr_found = True
        
        return tr_found


if __name__ == "__main__":
    root = tk.Tk()
    app = ExtractTRFolders(root)
    root.mainloop()