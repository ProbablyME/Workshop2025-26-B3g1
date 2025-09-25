import tkinter as tk
from tkinter import scrolledtext, messagebox
import serial
import threading
from datetime import datetime
import time
import re
from PIL import Image, ImageTk
import os

class RFIDTransmetteurMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("WAVE Système RFID - Transmetteur")
        self.root.geometry("900x800")
        self.root.configure(bg='#1a1a1a')
        self.root.resizable(False, False)

        # Variables
        self.serial_connection = None
        self.connected = False
        self.cartes_scannees = 0
        self.cartes_autorisees = 0
        self.derniere_carte = "Aucune"
        self.uid_autorise = "C0 A9 72 A3"  # UID configuré dans le code

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
                # Crée un logo par défaut (carré vert)
                img = Image.new('RGB', (120, 120), color='#00ff88')
                self.logo_image = ImageTk.PhotoImage(img)
                print("Logo par défaut créé (logo.png introuvable)")
                return

            img = Image.open(logo_path)
            img = img.resize((120, 120), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
        except Exception as e:
            # En cas d'erreur, crée un logo par défaut
            img = Image.new('RGB', (120, 120), color='#00ff88')
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

        title = tk.Label(title_frame, text="WAVE SYSTÈME RFID",
                        font=('Segoe UI', 28, 'bold'),
                        fg=self.colors['accent'], bg=self.colors['bg'])
        title.pack(anchor='w')

        subtitle = tk.Label(title_frame, text="Contrôle d'accès RFID + Transmission 433MHz",
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

        # Informations RFID
        self.create_rfid_info_section()

        # Message personnalisé
        self.create_message_section()

        # Statut en temps réel
        self.create_status_section()

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
        self.port_entry.insert(0, "COM4")
        self.port_entry.pack(side=tk.LEFT, padx=(10, 20))

        self.connect_btn = tk.Button(input_frame, text="Connecter",
                                   font=('Segoe UI', 12, 'bold'),
                                   bg=self.colors['accent'], fg='black',
                                   relief='flat', padx=20, pady=8,
                                   command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT)

    def create_rfid_info_section(self):
        info_card = tk.Frame(self.root, bg=self.colors['card'])
        info_card.pack(fill=tk.X, padx=30, pady=(0, 20))

        info_content = tk.Frame(info_card, bg=self.colors['card'])
        info_content.pack(padx=25, pady=20)

        tk.Label(info_content, text="CONFIGURATION RFID",
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor='w')

        # UID autorisé
        uid_frame = tk.Frame(info_content, bg=self.colors['card'])
        uid_frame.pack(fill=tk.X, pady=(15, 0))

        tk.Label(uid_frame, text="UID Autorisé:",
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT)

        tk.Label(uid_frame, text=self.uid_autorise,
                font=('Consolas', 12, 'bold'),
                fg=self.colors['success'], bg=self.colors['card']).pack(side=tk.LEFT, padx=(10, 0))

        # Code de transmission
        code_frame = tk.Frame(info_content, bg=self.colors['card'])
        code_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(code_frame, text="Protocole de transmission:",
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT)

        tk.Label(code_frame, text="Messages personnalisés (0xFF...0xFE)",
                font=('Consolas', 12, 'bold'),
                fg=self.colors['blue'], bg=self.colors['card']).pack(side=tk.LEFT, padx=(10, 0))

    def create_message_section(self):
        msg_card = tk.Frame(self.root, bg=self.colors['card'])
        msg_card.pack(fill=tk.X, padx=30, pady=(0, 20))

        msg_content = tk.Frame(msg_card, bg=self.colors['card'])
        msg_content.pack(padx=25, pady=20)

        tk.Label(msg_content, text="MESSAGE PERSONNALISÉ",
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor='w')

        tk.Label(msg_content, text="Message à envoyer quand carte autorisée détectée (max 50 caractères) :",
                font=('Segoe UI', 12),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor='w', pady=(15, 5))

        # Zone de saisie
        input_frame = tk.Frame(msg_content, bg=self.colors['card'])
        input_frame.pack(fill=tk.X, pady=(0, 15))

        self.message_entry = tk.Entry(input_frame,
                                    font=('Segoe UI', 12, 'bold'),
                                    bg=self.colors['bg'], fg=self.colors['accent'],
                                    width=50, relief='flat', bd=5)
        self.message_entry.insert(0, "HELLO")  # Valeur par défaut
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        self.message_entry.bind('<Return>', lambda e: self.send_message_command())

        # Bouton pour définir le message
        self.set_msg_btn = tk.Button(input_frame, text="Définir Message",
                                   font=('Segoe UI', 12, 'bold'),
                                   bg=self.colors['blue'], fg='white',
                                   relief='flat', padx=20, pady=8,
                                   command=self.send_message_command,
                                   state=tk.DISABLED)
        self.set_msg_btn.pack(side=tk.RIGHT)

        # Message actuel affiché
        current_frame = tk.Frame(msg_content, bg=self.colors['bg'], relief='flat', bd=2)
        current_frame.pack(fill=tk.X)

        tk.Label(current_frame, text="Message actuel:",
                font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text_dim'], bg=self.colors['bg']).pack(side=tk.LEFT, padx=(10, 5), pady=10)

        self.current_message_label = tk.Label(current_frame, text="HELLO",
                                            font=('Consolas', 11, 'bold'),
                                            fg=self.colors['success'], bg=self.colors['bg'])
        self.current_message_label.pack(side=tk.LEFT, pady=10)

    def create_status_section(self):
        status_card = tk.Frame(self.root, bg=self.colors['card'])
        status_card.pack(fill=tk.X, padx=30, pady=(0, 20))

        status_content = tk.Frame(status_card, bg=self.colors['card'])
        status_content.pack(padx=25, pady=20)

        header_frame = tk.Frame(status_content, bg=self.colors['card'])
        header_frame.pack(fill=tk.X)

        tk.Label(header_frame, text="STATUT EN TEMPS RÉEL",
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT)

        # VOYANT LUMINEUX PRINCIPAL
        voyant_card = tk.Frame(status_content, bg=self.colors['card'], relief='raised', bd=2)
        voyant_card.pack(fill=tk.X, pady=(15, 0))

        voyant_content = tk.Frame(voyant_card, bg=self.colors['card'])
        voyant_content.pack(padx=25, pady=20)

        tk.Label(voyant_content, text="🚨 VOYANT DE DÉTECTION RFID",
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack()

        # Container pour le voyant
        voyant_container = tk.Frame(voyant_content, bg=self.colors['card'])
        voyant_container.pack(pady=15)

        # GROS VOYANT CIRCULAIRE (100x100)
        self.voyant_canvas = tk.Canvas(voyant_container, width=120, height=120,
                                      bg=self.colors['card'], highlightthickness=0)
        self.voyant_canvas.pack(side=tk.LEFT, padx=20)

        # Cercle externe (cadre)
        self.voyant_outer = self.voyant_canvas.create_oval(10, 10, 110, 110,
                                                          fill='#2a2a2a',
                                                          outline='#666666',
                                                          width=3)

        # Cercle interne (voyant)
        self.voyant_inner = self.voyant_canvas.create_oval(20, 20, 100, 100,
                                                          fill='#404040',
                                                          outline='#606060',
                                                          width=2)

        # Étiquettes du voyant
        voyant_labels = tk.Frame(voyant_container, bg=self.colors['card'])
        voyant_labels.pack(side=tk.LEFT, padx=20)

        tk.Label(voyant_labels, text="ÉTATS:",
                font=('Segoe UI', 14, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor='w')

        tk.Label(voyant_labels, text="🔘 ATTENTE",
                font=('Segoe UI', 12),
                fg='#666666', bg=self.colors['card']).pack(anchor='w', pady=2)

        tk.Label(voyant_labels, text="🟡 DÉTECTION",
                font=('Segoe UI', 12),
                fg='#ffaa00', bg=self.colors['card']).pack(anchor='w', pady=2)

        tk.Label(voyant_labels, text="🟢 AUTORISÉ",
                font=('Segoe UI', 12),
                fg='#00ff66', bg=self.colors['card']).pack(anchor='w', pady=2)

        tk.Label(voyant_labels, text="🔴 REFUSÉ",
                font=('Segoe UI', 12),
                fg='#ff4444', bg=self.colors['card']).pack(anchor='w', pady=2)

        # Statut actuel du voyant
        self.voyant_status = tk.Label(voyant_content, text="🔘 EN ATTENTE",
                                     font=('Segoe UI', 18, 'bold'),
                                     fg='#666666', bg=self.colors['card'])
        self.voyant_status.pack(pady=10)

        # Dernière carte
        carte_frame = tk.Frame(status_content, bg=self.colors['bg'], relief='flat', bd=2)
        carte_frame.pack(fill=tk.X, pady=(15, 0))

        tk.Label(carte_frame, text="Dernière carte scannée:",
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text_dim'], bg=self.colors['bg']).pack(pady=(10, 5))

        self.derniere_carte_label = tk.Label(carte_frame, text=self.derniere_carte,
                                           font=('Consolas', 16, 'bold'),
                                           fg=self.colors['warning'], bg=self.colors['bg'])
        self.derniere_carte_label.pack(pady=(0, 10))

        # Protocole de transmission
        protocol_frame = tk.Frame(status_content, bg=self.colors['card'])
        protocol_frame.pack(fill=tk.X, pady=(15, 0))

        tk.Label(protocol_frame, text="Protocole 433MHz:",
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT)

        self.protocol_status = tk.Label(protocol_frame, text="0xFF→paquets→0xFE",
                                 font=('Consolas', 12, 'bold'),
                                 fg=self.colors['blue'], bg=self.colors['card'])
        self.protocol_status.pack(side=tk.LEFT, padx=(10, 0))

        # Statistiques
        stats_frame = tk.Frame(status_content, bg=self.colors['card'])
        stats_frame.pack(fill=tk.X, pady=(15, 0))

        stats_left = tk.Frame(stats_frame, bg=self.colors['card'])
        stats_left.pack(side=tk.LEFT)

        self.stats_scannees = tk.Label(stats_left, text=f"Cartes scannées: {self.cartes_scannees}",
                                     font=('Segoe UI', 11),
                                     fg=self.colors['text_dim'], bg=self.colors['card'])
        self.stats_scannees.pack(anchor='w')

        stats_right = tk.Frame(stats_frame, bg=self.colors['card'])
        stats_right.pack(side=tk.RIGHT)

        self.stats_autorisees = tk.Label(stats_right, text=f"Autorisées: {self.cartes_autorisees}",
                                       font=('Segoe UI', 11),
                                       fg=self.colors['success'], bg=self.colors['card'])
        self.stats_autorisees.pack(anchor='e')

    def create_console_section(self):
        console_card = tk.Frame(self.root, bg=self.colors['card'])
        console_card.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))

        console_content = tk.Frame(console_card, bg=self.colors['card'])
        console_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        tk.Label(console_content, text="CONSOLE SYSTÈME",
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor='w', pady=(0, 15))

        self.console = scrolledtext.ScrolledText(console_content,
                                               font=('Consolas', 10),
                                               bg='#0d1117', fg=self.colors['accent'],
                                               height=12, relief='flat', bd=0,
                                               state=tk.DISABLED)
        self.console.pack(fill=tk.BOTH, expand=True)

        # Tags pour coloration
        self.console.tag_configure('success', foreground=self.colors['success'], font=('Consolas', 10, 'bold'))
        self.console.tag_configure('error', foreground=self.colors['danger'], font=('Consolas', 10, 'bold'))
        self.console.tag_configure('warning', foreground=self.colors['warning'])
        self.console.tag_configure('info', foreground=self.colors['blue'])
        self.console.tag_configure('uid', foreground=self.colors['accent'], font=('Consolas', 10, 'bold'))

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
                self.status.configure(text="● En ligne - Surveillance RFID", fg=self.colors['success'])
                self.set_msg_btn.configure(state=tk.NORMAL)  # Active le bouton de message

                self.log(f"Connecté au système RFID sur {port}", 'success')

                threading.Thread(target=self.read_serial, daemon=True).start()

            except Exception as e:
                error_msg = str(e)
                if "PermissionError" in error_msg or "Accès refusé" in error_msg:
                    user_msg = f"❌ PORT {port} OCCUPÉ\n\n• Fermez l'Arduino IDE (moniteur série)\n• Ou changez de port COM\n• Ou redémarrez l'ESP8266"
                    self.log(f"Port {port} occupé - Fermez l'Arduino IDE", 'error')
                elif "could not open port" in error_msg:
                    user_msg = f"❌ PORT {port} INTROUVABLE\n\n• Vérifiez que l'ESP8266 est connecté\n• Essayez COM3, COM4, COM7...\n• Redémarrez l'ESP8266"
                    self.log(f"Port {port} introuvable - Vérifiez la connexion", 'error')
                else:
                    user_msg = f"❌ ERREUR DE CONNEXION\n\n{error_msg}\n\n• Vérifiez le port COM\n• Redémarrez l'ESP8266"
                    self.log(f"Erreur connexion: {error_msg}", 'error')

                messagebox.showerror("Erreur de connexion", user_msg)
        else:
            if self.serial_connection:
                self.serial_connection.close()

            self.connected = False
            self.connect_btn.configure(text="Connecter", bg=self.colors['accent'])
            self.status.configure(text="● Hors ligne", fg=self.colors['danger'])
            self.set_msg_btn.configure(state=tk.DISABLED)  # Désactive le bouton de message

            self.log("Déconnecté du système RFID", 'warning')

    def send_message_command(self):
        """Envoie la commande pour définir le message personnalisé"""
        if not self.connected or not self.serial_connection:
            self.log("Non connecté au système", 'error')
            return

        message = self.message_entry.get().strip()
        if not message:
            self.log("Message vide", 'error')
            return

        if len(message) > 50:
            message = message[:50]
            self.log(f"⚠ Message limité à 50 caractères", 'warning')

        try:
            # Envoie la commande MSG: au Arduino
            command = f"MSG:{message}\n"
            self.serial_connection.write(command.encode())
            self.log(f"Nouveau message défini: '{message}'", 'success')

            # Met à jour l'affichage du message actuel
            self.current_message_label.configure(text=message)

            # Flash du bouton
            self.set_msg_btn.configure(bg=self.colors['warning'])
            self.root.after(200, lambda: self.set_msg_btn.configure(bg=self.colors['blue']))

        except Exception as e:
            self.log(f"Erreur d'envoi: {str(e)}", 'error')

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

        # Carte détectée
        if "Carte détectée" in line:
            self.log("🎯 Carte RFID détectée", 'info')
            self.set_voyant_state('detecting')

        # UID scanné
        elif "UID scanné :" in line:
            uid = line.split("UID scanné :")[1].strip()
            self.derniere_carte = uid
            self.derniere_carte_label.configure(text=uid, fg=self.colors['warning'])
            self.cartes_scannees += 1
            self.update_stats()
            self.log(f"UID scanné: {uid}", 'uid')

        # UID autorisé - Nouveau protocole
        elif "DEBUG: UID AUTORISÉ - Envoi de '" in line:
            self.derniere_carte_label.configure(fg=self.colors['success'])
            self.protocol_status.configure(text="📡 Transmission...", fg=self.colors['success'])
            self.cartes_autorisees += 1
            self.update_stats()
            # Voyant vert pour carte autorisée
            self.set_voyant_state('authorized')
            # Extrait le message à envoyer
            match = re.search(r"Envoi de '([^']*)'", line)
            if match:
                message_envoye = match.group(1)
                self.log(f"✅ ACCÈS AUTORISÉ - Envoi de '{message_envoye}'", 'success')
            else:
                self.log("✅ ACCÈS AUTORISÉ - Transmission 433MHz", 'success')

        # UID non autorisé - Nouveau protocole
        elif "DEBUG: UID NON AUTORISÉ - Aucune transmission" in line:
            self.derniere_carte_label.configure(fg=self.colors['danger'])
            self.protocol_status.configure(text="❌ Accès refusé", fg=self.colors['danger'])
            # Voyant rouge pour carte refusée
            self.set_voyant_state('denied')
            self.log("❌ ACCÈS REFUSÉ - Aucune transmission", 'error')

        # Code de début avec longueur
        elif "DEBUG: Envoi code de début:" in line:
            code_match = re.search(r"code de début: (0x[0-9A-F]+)", line)
            if code_match:
                code_debut = code_match.group(1)
                self.log(f"📡 Code début: {code_debut}", 'info')

        # Paquets de données
        elif "DEBUG: Paquet" in line and "- Code:" in line:
            paquet_match = re.search(r"Paquet (\d+)/(\d+) - Code: (0x[0-9A-F]+)", line)
            if paquet_match:
                num_paquet = paquet_match.group(1)
                total_paquets = paquet_match.group(2)
                code_paquet = paquet_match.group(3)
                self.log(f"📦 Paquet {num_paquet}/{total_paquets}: {code_paquet}", 'info')

        # Code de fin
        elif "DEBUG: Envoi code de fin:" in line:
            code_match = re.search(r"code de fin: (0x[0-9A-F]+)", line)
            if code_match:
                code_fin = code_match.group(1)
                self.log(f"🔚 Code fin: {code_fin}", 'info')

        # Transmission terminée
        elif "DEBUG: Transmission terminée avec succès" in line:
            self.log("✅ Transmission 433MHz terminée avec succès", 'success')
            # Reset protocol status après transmission
            self.root.after(3000, lambda: self.protocol_status.configure(text="0xFF→paquets→0xFE", fg=self.colors['blue']))

        # Envoi du message personnalisé (détection initiale)
        elif "DEBUG: Envoi du message personnalisé:" in line:
            match = re.search(r"personnalisé: '([^']*)'.*\((\d+) caractères\)", line)
            if match:
                message_personalise = match.group(1)
                nb_chars = match.group(2)
                self.log(f"🚀 Envoi message: '{message_personalise}' ({nb_chars} chars)", 'success')

        # Communication RFID fermée
        elif "DEBUG: Communication RFID fermée" in line:
            self.log("🔐 Communication RFID fermée", 'normal')

        # Messages INFO pour les nouveaux messages définis
        elif "Nouveau message défini:" in line:
            match = re.search(r"Nouveau message défini: '([^']*)'", line)
            if match:
                nouveau_message = match.group(1)
                self.current_message_label.configure(text=nouveau_message)
                self.log(f"Message mis à jour: '{nouveau_message}'", 'info')

        elif "Message actuel:" in line:
            match = re.search(r"Message actuel: '([^']*)'", line)
            if match:
                message_actuel = match.group(1)
                self.current_message_label.configure(text=message_actuel)
                self.log(f"Message actuel: '{message_actuel}'", 'info')

        # Messages de debug pour l'envoi de messages personnalisés
        elif "Envoi du message personnalisé:" in line:
            match = re.search(r"Envoi du message personnalisé: '([^']*)'", line)
            if match:
                message_personnalise = match.group(1)
                self.log(f"Envoi message personnalisé: '{message_personnalise}'", 'success')

        # Messages de debug généraux
        elif line.startswith("DEBUG:"):
            debug_msg = line[6:].strip()
            if "prêt" in debug_msg.lower() or "configuré" in debug_msg.lower():
                self.log(debug_msg, 'info')
            else:
                self.log(debug_msg, 'normal')

        # Autres messages
        else:
            self.log(line, 'normal')

    def update_stats(self):
        self.stats_scannees.configure(text=f"Cartes scannées: {self.cartes_scannees}")
        self.stats_autorisees.configure(text=f"Autorisées: {self.cartes_autorisees}")

    def log(self, message, msg_type='normal'):
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

    def set_voyant_state(self, state):
        """Change l'état du GROS VOYANT selon l'action"""
        states = {
            'waiting': {
                'color': '#404040',
                'outline': '#606060',
                'status': '🔘 EN ATTENTE',
                'status_color': '#666666'
            },
            'detecting': {
                'color': '#ffaa00',
                'outline': '#ffdd00',
                'status': '🟡 DÉTECTION EN COURS',
                'status_color': '#ffaa00'
            },
            'authorized': {
                'color': '#00ff66',
                'outline': '#00ff88',
                'status': '🟢 ACCÈS AUTORISÉ',
                'status_color': '#00ff66'
            },
            'denied': {
                'color': '#ff4444',
                'outline': '#ff6666',
                'status': '🔴 ACCÈS REFUSÉ',
                'status_color': '#ff4444'
            }
        }

        if state in states:
            s = states[state]

            # Change la couleur du voyant
            self.voyant_canvas.itemconfig(self.voyant_inner,
                                         fill=s['color'],
                                         outline=s['outline'])

            # Change le texte de statut
            self.voyant_status.configure(text=s['status'],
                                        fg=s['status_color'])

            # Effets spéciaux selon l'état
            if state == 'detecting':
                self.pulse_voyant(5)
            elif state == 'authorized':
                self.flash_voyant('success', 3)
            elif state == 'denied':
                self.flash_voyant('error', 3)

            # Retour à l'attente après 4 secondes
            if state != 'waiting':
                self.root.after(4000, lambda: self.set_voyant_state('waiting'))

    def pulse_voyant(self, count):
        """Effet de pulsation du voyant (pour détection)"""
        if count <= 0:
            return

        # Grossit le voyant
        self.root.after(0, lambda: self.voyant_canvas.coords(self.voyant_inner, 15, 15, 105, 105))

        # Remet à la taille normale
        self.root.after(200, lambda: self.voyant_canvas.coords(self.voyant_inner, 20, 20, 100, 100))

        # Continue la pulsation
        if count > 1:
            self.root.after(400, lambda: self.pulse_voyant(count - 1))

    def flash_voyant(self, type_flash, count):
        """Effet de flash du voyant (pour succès/échec)"""
        if count <= 0:
            return

        colors = {
            'success': {'flash': '#ffffff', 'normal': '#00ff66'},
            'error': {'flash': '#ffaaaa', 'normal': '#ff4444'}
        }

        if type_flash in colors:
            flash_color = colors[type_flash]['flash']
            normal_color = colors[type_flash]['normal']

            # Flash blanc/rose
            self.root.after(0, lambda: self.voyant_canvas.itemconfig(
                self.voyant_inner, fill=flash_color))

            # Retour couleur normale
            self.root.after(150, lambda: self.voyant_canvas.itemconfig(
                self.voyant_inner, fill=normal_color))

            # Continue le flash
            if count > 1:
                self.root.after(300, lambda: self.flash_voyant(type_flash, count - 1))

if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDTransmetteurMonitor(root)
    root.mainloop()