import tkinter as tk
from tkinter import scrolledtext, messagebox
import serial
import threading
from datetime import datetime
import time
import re
from PIL import Image, ImageTk
import os

class RFIDRecepteurMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("WAVE Système RFID - Récepteur")
        self.root.geometry("900x750")
        self.root.configure(bg='#1a1a1a')
        self.root.resizable(False, False)

        # Variables
        self.serial_connection = None
        self.connected = False
        self.autorisations_recues = 0
        self.codes_non_reconnus = 0
        self.dernier_statut = ""
        self.code_hello = "0x12345678"


        # Couleurs
        self.colors = {
            'bg': '#1a1a1a',
            'card': '#2d2d2d',
            'accent': '#00ff88',
            'text': '#ffffff',
            'text_dim': '#999999',
            'danger': '#ff4444',
            'warning': '#ffaa00',
            'blue': '#4488ff',
            'success': '#00ff66'
        }

        # Logo
        self.load_logo()
        self.setup_ui()

    def load_logo(self):
        """Charge le logo WAVE"""
        try:
            # Essaie de charger le logo depuis le répertoire du script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(script_dir, "logo.png")

            # Si le fichier n'existe pas, essaie depuis le répertoire courant
            if not os.path.exists(logo_path):
                logo_path = "logo.png"

            # Si toujours pas trouvé, crée un logo par défaut
            if not os.path.exists(logo_path):
                # Crée un logo par défaut (carré bleu)
                img = Image.new('RGB', (120, 120), color='#4488ff')
                self.logo_image = ImageTk.PhotoImage(img)
                print("Logo par défaut créé (logo.png introuvable)")
                return

            img = Image.open(logo_path)
            img = img.resize((120, 120), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
        except Exception as e:
            # En cas d'erreur, crée un logo par défaut
            img = Image.new('RGB', (120, 120), color='#4488ff')
            self.logo_image = ImageTk.PhotoImage(img)
            print(f"Erreur chargement logo: {e} - Logo par défaut utilisé")

    def setup_ui(self):
        # Header avec logo
        header = tk.Frame(self.root, bg=self.colors['bg'])
        header.pack(fill=tk.X, padx=30, pady=30)

        # Logo à gauche
        logo_label = tk.Label(header, image=self.logo_image, bg=self.colors['bg'])
        logo_label.pack(side=tk.LEFT)

        # Titre à droite du logo
        title_frame = tk.Frame(header, bg=self.colors['bg'])
        title_frame.pack(side=tk.LEFT, padx=(30, 0), fill=tk.Y)

        title = tk.Label(title_frame, text="WAVE CONTRÔLE D'ACCÈS",
                        font=('Segoe UI', 28, 'bold'),
                        fg=self.colors['blue'], bg=self.colors['bg'])
        title.pack(anchor='w')

        subtitle = tk.Label(title_frame, text="Surveillance des autorisations 433MHz",
                          font=('Segoe UI', 14),
                          fg=self.colors['text_dim'], bg=self.colors['bg'])
        subtitle.pack(anchor='w', pady=(5, 0))

        # Status
        self.status = tk.Label(title_frame, text="● Hors ligne",
                             font=('Segoe UI', 12, 'bold'),
                             fg=self.colors['danger'], bg=self.colors['bg'])
        self.status.pack(anchor='w', pady=(10, 0))

        # Connexion
        self.create_connection_section()

        # Configuration récepteur
        self.create_config_section()

        # Statut d'accès principal
        self.create_access_status_section()

        # Console
        self.create_console_section()

    def create_connection_section(self):
        conn_card = tk.Frame(self.root, bg=self.colors['card'])
        conn_card.pack(fill=tk.X, padx=30, pady=(0, 20))

        conn_content = tk.Frame(conn_card, bg=self.colors['card'])
        conn_content.pack(padx=25, pady=20)

        tk.Label(conn_content, text="CONNEXION SÉRIE",
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor='w')

        input_frame = tk.Frame(conn_content, bg=self.colors['card'])
        input_frame.pack(fill=tk.X, pady=(15, 0))

        tk.Label(input_frame, text="Port COM:",
                font=('Segoe UI', 12),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT)

        self.port_entry = tk.Entry(input_frame,
                                 font=('Segoe UI', 12),
                                 bg=self.colors['bg'], fg=self.colors['text'],
                                 width=8, relief='flat', bd=5)
        self.port_entry.insert(0, "COM8")
        self.port_entry.pack(side=tk.LEFT, padx=(10, 20))

        self.connect_btn = tk.Button(input_frame, text="Connecter",
                                   font=('Segoe UI', 12, 'bold'),
                                   bg=self.colors['blue'], fg='white',
                                   relief='flat', padx=20, pady=8,
                                   command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT)

        # Stats à droite
        stats_frame = tk.Frame(input_frame, bg=self.colors['card'])
        stats_frame.pack(side=tk.RIGHT)

        self.stats_label = tk.Label(stats_frame, text=f"Autorisations: {self.autorisations_recues} • Non reconnus: {self.codes_non_reconnus}",
                                   font=('Segoe UI', 10),
                                   fg=self.colors['text_dim'], bg=self.colors['card'])
        self.stats_label.pack()

    def create_config_section(self):
        config_card = tk.Frame(self.root, bg=self.colors['card'])
        config_card.pack(fill=tk.X, padx=30, pady=(0, 20))

        config_content = tk.Frame(config_card, bg=self.colors['card'])
        config_content.pack(padx=25, pady=20)

        tk.Label(config_content, text="CONFIGURATION RÉCEPTEUR",
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor='w')

        # Code attendu
        code_frame = tk.Frame(config_content, bg=self.colors['card'])
        code_frame.pack(fill=tk.X, pady=(15, 0))

        tk.Label(code_frame, text="Code d'autorisation attendu:",
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT)

        tk.Label(code_frame, text="Messages personnalisés (0xFF...0xFE)",
                font=('Consolas', 12, 'bold'),
                fg=self.colors['success'], bg=self.colors['card']).pack(side=tk.LEFT, padx=(10, 0))

        # Paramètres
        params_frame = tk.Frame(config_content, bg=self.colors['card'])
        params_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(params_frame, text="Protocole: 0xFF+longueur → paquets de données → 0xFE (fin)",
                font=('Segoe UI', 11),
                fg=self.colors['text_dim'], bg=self.colors['card']).pack(side=tk.LEFT)

    def create_access_status_section(self):
        status_card = tk.Frame(self.root, bg=self.colors['card'])
        status_card.pack(fill=tk.X, padx=30, pady=(0, 20))

        status_content = tk.Frame(status_card, bg=self.colors['card'])
        status_content.pack(padx=25, pady=20)

        tk.Label(status_content, text="STATUT D'ACCÈS",
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor='w')

        # Zone de statut principal
        status_display = tk.Frame(status_content, bg=self.colors['bg'], relief='flat', bd=2)
        status_display.pack(fill=tk.X, pady=(15, 0))

        self.access_status_label = tk.Label(status_display, text="",
                                          font=('Segoe UI', 22, 'bold'),
                                          fg=self.colors['text_dim'], bg=self.colors['bg'],
                                          pady=30)
        self.access_status_label.pack()

        # Informations détaillées
        info_frame = tk.Frame(status_content, bg=self.colors['card'])
        info_frame.pack(fill=tk.X, pady=(15, 0))

        self.derniere_reception = tk.Label(info_frame, text="",
                                         font=('Segoe UI', 11, 'italic'),
                                         fg=self.colors['text_dim'], bg=self.colors['card'])
        self.derniere_reception.pack(side=tk.LEFT)

        self.type_signal = tk.Label(info_frame, text="",
                                   font=('Segoe UI', 11, 'bold'),
                                   fg=self.colors['blue'], bg=self.colors['card'])
        self.type_signal.pack(side=tk.RIGHT)

    def create_console_section(self):
        console_card = tk.Frame(self.root, bg=self.colors['card'])
        console_card.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))

        console_content = tk.Frame(console_card, bg=self.colors['card'])
        console_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        header_frame = tk.Frame(console_content, bg=self.colors['card'])
        header_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(header_frame, text="CONSOLE DE SURVEILLANCE",
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT)

        clear_btn = tk.Button(header_frame, text="Effacer",
                            font=('Segoe UI', 10),
                            bg=self.colors['warning'], fg='black',
                            relief='flat', padx=15, pady=5,
                            command=self.clear_console)
        clear_btn.pack(side=tk.RIGHT)

        self.console = scrolledtext.ScrolledText(console_content,
                                               font=('Consolas', 10),
                                               bg='#0d1117', fg=self.colors['text'],
                                               height=10, relief='flat', bd=0,
                                               state=tk.DISABLED)
        self.console.pack(fill=tk.BOTH, expand=True)

        # Tags pour coloration
        self.console.tag_configure('success', foreground=self.colors['success'], font=('Consolas', 10, 'bold'))
        self.console.tag_configure('error', foreground=self.colors['danger'], font=('Consolas', 10, 'bold'))
        self.console.tag_configure('warning', foreground=self.colors['warning'])
        self.console.tag_configure('info', foreground=self.colors['blue'])
        self.console.tag_configure('signal', foreground=self.colors['accent'], font=('Consolas', 10, 'bold'))

    def toggle_connection(self):
        if not self.connected:
            port = self.port_entry.get()
            try:
                self.serial_connection = serial.Serial(
                    port=port,
                    baudrate=115200,
                    timeout=0.1
                )

                self.connected = True
                self.connect_btn.configure(text="Déconnecter", bg=self.colors['danger'])
                self.status.configure(text="● En ligne - Surveillance d'accès", fg=self.colors['success'])

                self.log(f"Surveillance d'accès activée sur {port}", 'success')

                threading.Thread(target=self.read_serial, daemon=True).start()

            except Exception as e:
                error_msg = str(e)
                if "PermissionError" in error_msg or "Accès refusé" in error_msg:
                    user_msg = f"PORT {port} OCCUPÉ\n\n• Fermez l'Arduino IDE (moniteur série)\n• Ou changez de port COM\n• Ou redémarrez l'ESP8266"
                    self.log(f"Port {port} occupé - Fermez l'Arduino IDE", 'error')
                elif "could not open port" in error_msg:
                    user_msg = f"PORT {port} INTROUVABLE\n\n• Vérifiez que l'ESP8266 est connecté\n• Essayez COM3, COM4, COM7...\n• Redémarrez l'ESP8266"
                    self.log(f"Port {port} introuvable - Vérifiez la connexion", 'error')
                else:
                    user_msg = f"ERREUR DE CONNEXION\n\n{error_msg}\n\n• Vérifiez le port COM\n• Redémarrez l'ESP8266"
                    self.log(f"Erreur connexion: {error_msg}", 'error')

                messagebox.showerror("Erreur de connexion", user_msg)
        else:
            if self.serial_connection:
                self.serial_connection.close()

            self.connected = False
            self.connect_btn.configure(text="Connecter", bg=self.colors['blue'])
            self.status.configure(text="● Hors ligne", fg=self.colors['danger'])

            self.log("Surveillance d'accès désactivée", 'warning')

    def read_serial(self):
        while self.connected and self.serial_connection:
            try:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.root.after(0, lambda l=line: self.process_line(l))
                else:
                    time.sleep(0.01)
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Erreur lecture: {str(e)}", 'error'))
                break

    def process_line(self, line):
        if not line:
            return

        current_time = datetime.now()

        # Signal détecté
        if "Signal détecté" in line:
            self.log("Signal 433MHz détecté", 'signal')

        # Code brut reçu
        elif "Code brut reçu :" in line:
            code = line.split("Code brut reçu :")[1].strip()
            self.log(f"Code reçu: {code}", 'info')

        # Détails du signal
        elif "Longueur :" in line:
            longueur = line.split("Longueur :")[1].strip()
            self.log(f"Longueur: {longueur}", 'info')

        elif "Protocole :" in line:
            protocole = line.split("Protocole :")[1].strip()
            self.log(f"Protocole: {protocole}", 'info')

        # Code valide détecté
        elif "Code valide détecté" in line:
            self.log("Code valide (32 bits)", 'success')

        # Message personnalisé reçu avec émojis ✅
        elif "✅ MESSAGE PERSONNALISÉ REÇU:" in line:
            # Extrait le message entre les guillemets simples
            match = re.search(r"✅ MESSAGE PERSONNALISÉ REÇU: '([^']*)'", line)
            if match:
                message_recu = match.group(1)
                if message_recu:  # Seulement si le message n'est pas vide
                    self.display_access_status(f"✅ {message_recu}", "MESSAGE REÇU", current_time, True)
                    self.autorisations_recues += 1
                    self.update_stats()
                    self.log(f"✅ MESSAGE REÇU: '{message_recu}'", 'success')
                else:
                    # Message vide détecté
                    self.display_access_status("⚠️ MESSAGE VIDE", "ERREUR RÉCEPTION", current_time, False)
                    self.codes_non_reconnus += 1
                    self.update_stats()
                    self.log("⚠️ Message vide reçu - Problème de décodage", 'error')

        # Début de message avec nouveau format
        elif "DEBUG: Début de message - Longueur attendue:" in line:
            longueur = line.split("Longueur attendue:")[1].strip()
            self.log(f"📡 Début réception - {longueur} caractères attendus", 'info')

        # Paquets de message avec debug amélioré
        elif "DEBUG: Paquet" in line and "reçu:" in line:
            paquet_match = re.search(r"DEBUG: Paquet (\d+) reçu: (0x[0-9A-F]+)", line)
            if paquet_match:
                num_paquet = paquet_match.group(1)
                code_hex = paquet_match.group(2)
                self.log(f"📦 Paquet {num_paquet}: {code_hex}", 'info')

        # Buffer actuel avec progression
        elif "Buffer actuel:" in line:
            match = re.search(r"Buffer actuel: '([^']*)' \((\d+)/(\d+) chars\)", line)
            if match:
                buffer_actuel = match.group(1)
                current_len = match.group(2)
                total_len = match.group(3)
                if buffer_actuel:  # Ne log que si non vide
                    progress = f"({current_len}/{total_len})"
                    self.log(f"🔄 Assemblage: '{buffer_actuel}' {progress}", 'info')

        # Carte autorisée détectée
        elif "✅ CARTE AUTORISÉE DÉTECTÉE" in line:
            self.log("✅ Accès accordé - Carte RFID autorisée", 'success')

        # Signal hors séquence (nouveau format debug)
        elif "DEBUG: Signal hors séquence:" in line:
            code_match = re.search(r"Signal hors séquence: (0x[0-9A-F]+)", line)
            if code_match:
                code_hex = code_match.group(1)
                self.display_access_status(f"⚠️ {code_hex[:8]}", "HORS SÉQUENCE", current_time, False)
                self.codes_non_reconnus += 1
                self.update_stats()
                self.log(f"⚠️ Signal hors séquence: {code_hex}", 'warning')

        # Buffer réinitialisé
        elif "DEBUG: Buffer réinitialisé" in line:
            self.log("🔄 Buffer de réception réinitialisé", 'info')




        # Signal rejeté
        elif "Signal rejeté" in line:
            self.log("Signal rejeté (bruit/format invalide)", 'error')

        # Bruit détecté
        elif "Code = 0" in line:
            self.log("Bruit radio détecté", 'warning')

        # Longueur incorrecte
        elif "Longueur incorrecte" in line:
            details = line.split("Longueur incorrecte :")[1].strip() if ":" in line else ""
            self.log(f"Format incorrect: {details}", 'warning')

        # Messages de debug
        elif line.startswith("DEBUG:"):
            debug_msg = line[6:].strip()
            if "prêt" in debug_msg.lower():
                self.log(debug_msg, 'info')
            else:
                self.log(debug_msg, 'normal')

        # Autres messages
        else:
            self.log(line, 'normal')

    def display_access_status(self, message, type_signal, timestamp, is_authorized):
        """Affiche le statut d'accès principal"""
        self.dernier_statut = message
        self.access_status_label.configure(text=message)

        if is_authorized:
            self.access_status_label.configure(fg=self.colors['success'])
        else:
            self.access_status_label.configure(fg=self.colors['warning'])

        self.derniere_reception.configure(text=f"Reçu à {timestamp.strftime('%H:%M:%S')}")
        self.type_signal.configure(text=type_signal)

        # Animation flash
        self.animate_access_status(is_authorized)

        # Efface l'affichage après 5 secondes
        self.root.after(5000, self.clear_status_display)

    def clear_status_display(self):
        """Efface l'affichage du statut"""
        self.access_status_label.configure(text="")
        self.derniere_reception.configure(text="")
        self.type_signal.configure(text="")

    def animate_access_status(self, is_authorized):
        """Animation du statut d'accès"""
        original_bg = self.access_status_label.master.cget('bg')
        flash_color = self.colors['success'] if is_authorized else self.colors['warning']

        # Flash
        colors = [flash_color, original_bg, flash_color, original_bg]
        for i, color in enumerate(colors):
            self.root.after(i * 200, lambda c=color: self.access_status_label.master.configure(bg=c))

    def update_stats(self):
        """Met à jour les statistiques"""
        self.stats_label.configure(
            text=f"Autorisations: {self.autorisations_recues} • Non reconnus: {self.codes_non_reconnus}")

    def log(self, message, msg_type='normal'):
        """Ajoute un message à la console"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.console.configure(state=tk.NORMAL)
        time_text = f"[{timestamp}] "
        self.console.insert(tk.END, time_text, 'time')
        self.console.insert(tk.END, f"{message}\n", msg_type)
        self.console.see(tk.END)
        self.console.configure(state=tk.DISABLED)

        # Tags
        self.console.tag_configure('time', foreground=self.colors['text_dim'])
        self.console.tag_configure('normal', foreground=self.colors['text'])

        # Limite le nombre de lignes
        lines = self.console.get(1.0, tk.END).split('\n')
        if len(lines) > 100:
            self.console.configure(state=tk.NORMAL)
            self.console.delete(1.0, "2.0")
            self.console.configure(state=tk.DISABLED)

    def clear_console(self):
        """Efface la console"""
        self.console.configure(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.configure(state=tk.DISABLED)

        self.access_status_label.configure(text="En attente...", fg=self.colors['warning'])
        self.derniere_reception.configure(text="Aucune réception")
        self.type_signal.configure(text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDRecepteurMonitor(root)
    root.mainloop()