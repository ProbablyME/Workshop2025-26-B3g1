import tkinter as tk
from tkinter import messagebox, ttk
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
        self.root.title("République · Système RFID – Récepteur")
        self.root.geometry("1200x800")
        self.root.configure(bg='#e6f3ff')
        self.root.resizable(True, True)
        
        # Permettre le plein écran avec F11
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        self.fullscreen = False

        # Variables
        self.serial_connection = None
        self.connected = False
        self.autorisations_recues = 0
        self.codes_non_reconnus = 0
        self.dernier_statut = ""
        self.code_hello = "0x12345678"
        self.messages_non_lus = []  # Liste des messages non lus
        self.selected_message_id = None
        self.sound_enabled = True  # État du son (par défaut activé)


        # Couleurs
        self.colors = {
            'bg': '#f5f5f7',  # Fond Apple clair
            'card': '#ffffff',  # Cartes blanches
            'accent': '#007aff',  # Bleu Apple
            'text': '#1d1d1f',  # Texte principal Apple
            'text_dim': '#86868b',  # Texte secondaire Apple
            'danger': '#ff3b30',  # Rouge Apple
            'warning': '#ff9500',  # Orange Apple
            'blue': '#007aff',  # Bleu Apple
            'success': '#34c759',  # Vert Apple
            'border': '#d2d2d7',  # Bordures Apple
            'header': '#ffffff',  # En-tête blanc Apple
            'main_section': '#ffffff',  # Section principale blanche
            'secondary_section': '#f5f5f7',  # Section secondaire gris clair
            'shadow': '#00000020',  # Ombre subtile
            'title_bar': '#007aff',  # Barre de titre bleue Apple
            'hover': '#f5f5f7',  # Couleur de survol Apple
            'military_green': '#4a5d23',  # Vert militaire
            'steel_gray': '#4a5568'  # Gris acier
        }

        # Logo
        self.load_logo()
        self.setup_ui()

    def load_logo(self):
        """Charge le logo WAVE-CONNECT agrandi"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Essaie plusieurs noms de logos
            logo_files = ["WAVE-CONNECT.png", "logo.png", "WAVE.png"]
            logo_found = False

            for logo_name in logo_files:
                logo_path = os.path.join(script_dir, logo_name)
                if os.path.exists(logo_path):
                    img_wave = Image.open(logo_path)
                    # Préserve le ratio en limitant à 120x80 max
                    img_wave.thumbnail((120, 80), Image.Resampling.LANCZOS)
                    self.wave_image = ImageTk.PhotoImage(img_wave)
                    logo_found = True
                    print(f"Logo chargé: {logo_name}")
                    break

            if not logo_found:
                # Logo par défaut agrandi
                img_wave = Image.new('RGB', (120, 80), color='#007aff')
                self.wave_image = ImageTk.PhotoImage(img_wave)
                print("Logo par défaut utilisé (fichier image non trouvé)")
                
        except Exception as e:
            # Logo par défaut en cas d'erreur
            img_wave = Image.new('RGB', (120, 80), color='#007aff')
            self.wave_image = ImageTk.PhotoImage(img_wave)
            print(f"Erreur chargement logo: {e} - Logo par défaut utilisé")

    def toggle_fullscreen(self, event=None):
        """Bascule entre plein écran et fenêtre normale"""
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        return "break"

    def exit_fullscreen(self, event=None):
        """Sort du plein écran"""
        if self.fullscreen:
            self.fullscreen = False
            self.root.attributes('-fullscreen', False)
        return "break"

    def setup_ui(self):
        # Styles officiels
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('Card.TFrame', background=self.colors['card'])
        style.configure('Header.TFrame', background=self.colors['blue'])
        style.configure('Header.TLabel', background=self.colors['blue'], foreground='#ffffff', font=('Segoe UI', 14))
        style.configure('HeaderTitle.TLabel', background=self.colors['blue'], foreground='#ffffff', font=('Segoe UI', 22, 'bold'))
        style.configure('Muted.TLabel', background=self.colors['card'], foreground=self.colors['text_dim'])
        style.configure('Strong.TLabel', background=self.colors['card'], foreground=self.colors['text'], font=('Segoe UI', 11, 'bold'))
        style.configure('Treeview', background='#ffffff', fieldbackground='#ffffff', foreground=self.colors['text'], rowheight=32, bordercolor=self.colors['border'], borderwidth=1, font=('SF Pro Text', 11))
        style.configure('Treeview.Heading', background=self.colors['accent'], foreground='white', font=('SF Pro Display', 12, 'bold'), relief='flat')
        style.map('Treeview', background=[('selected', '#e3f2fd')])
        style.map('Treeview.Heading', background=[('active', self.colors['accent'])])

        # En-tête épuré style Apple avec logo agrandi
        header = tk.Frame(self.root, bg=self.colors['header'], height=140)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg=self.colors['header'])
        header_inner.pack(fill=tk.BOTH, expand=True, padx=50, pady=30)

        # Section gauche - Logo WAVE-CONNECT agrandi et titre
        left_header = tk.Frame(header_inner, bg=self.colors['header'])
        left_header.pack(side=tk.LEFT, fill=tk.Y)

        # Logo WAVE-CONNECT agrandi
        wave_logo = tk.Label(left_header, image=self.wave_image, 
                            bg=self.colors['header'])
        wave_logo.pack(anchor='w', pady=(0, 15))

        # Titre WAVE-CONNECT
        title_label = tk.Label(left_header, text="WAVE-CONNECT", 
                              font=('SF Pro Display', 28, 'bold'), 
                              fg=self.colors['text'], bg=self.colors['header'])
        title_label.pack(anchor='w')

        # Section droite - Horloge uniquement
        right_header = tk.Frame(header_inner, bg=self.colors['header'])
        right_header.pack(side=tk.RIGHT, fill=tk.Y)

        # Horloge système épurée
        self.clock_label = tk.Label(right_header, text="", 
                                   font=('SF Mono', 16), 
                                   fg=self.colors['text_dim'], bg=self.colors['header'])
        self.clock_label.pack(anchor='e')
        self.update_clock()

        # Zone principale épurée style Apple
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Section principale gauche - Style Apple épuré
        main_section = tk.Frame(main_container, bg=self.colors['main_section'], 
                               relief='flat', bd=0)
        main_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))

        # Barre de titre épurée
        main_title_bar = tk.Frame(main_section, bg=self.colors['title_bar'], height=45)
        main_title_bar.pack(fill=tk.X)
        main_title_bar.pack_propagate(False)

        title_content = tk.Frame(main_title_bar, bg=self.colors['title_bar'])
        title_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=12)

        tk.Label(title_content, text="Messages reçus", 
                font=('SF Pro Display', 16, 'bold'), 
                fg='white', bg=self.colors['title_bar']).pack(side=tk.LEFT)

        # Section secondaire droite - Style Apple épuré
        secondary_section = tk.Frame(main_container, bg=self.colors['secondary_section'], 
                                    width=300, relief='flat', bd=0)
        secondary_section.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        secondary_section.pack_propagate(False)

        # Contrôles épurés style Apple
        controls_frame = tk.Frame(secondary_section, bg=self.colors['secondary_section'])
        controls_frame.pack(fill=tk.X, padx=25, pady=25)

        # Titre épuré
        title_frame = tk.Frame(controls_frame, bg=self.colors['secondary_section'])
        title_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(title_frame, text="Contrôles", 
                font=('SF Pro Display', 18, 'bold'), 
                fg=self.colors['text'], bg=self.colors['secondary_section']).pack(anchor='w')

        # Statut de connexion épuré
        status_frame = tk.Frame(controls_frame, bg=self.colors['secondary_section'])
        status_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(status_frame, text="Statut", 
                font=('SF Pro Display', 14, 'bold'), 
                fg=self.colors['text'], bg=self.colors['secondary_section']).pack(anchor='w')
        
        self.status = tk.Label(status_frame, text="Hors ligne", 
                              font=('SF Pro Text', 12), 
                              fg=self.colors['danger'], bg=self.colors['secondary_section'])
        self.status.pack(anchor='w', pady=(8, 0))

        # Connexion série épurée
        conn_frame = tk.Frame(controls_frame, bg=self.colors['secondary_section'])
        conn_frame.pack(fill=tk.X, pady=(0, 25))

        tk.Label(conn_frame, text="Connexion", 
                font=('SF Pro Display', 14, 'bold'), 
                fg=self.colors['text'], bg=self.colors['secondary_section']).pack(anchor='w')
        
        port_frame = tk.Frame(conn_frame, bg=self.colors['secondary_section'])
        port_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(port_frame, text="Port COM", 
                font=('SF Pro Text', 11), 
                fg=self.colors['text_dim'], bg=self.colors['secondary_section']).pack(anchor='w')
        
        self.port_entry = tk.Entry(port_frame, font=('SF Mono', 12), 
                                  bg='#ffffff', fg=self.colors['text'], 
                                  width=10, relief='flat', bd=1,
                                  highlightthickness=2, highlightcolor=self.colors['accent'])
        self.port_entry.insert(0, "COM8")
        self.port_entry.pack(anchor='w', pady=(8, 0))
        
        self.connect_btn = tk.Button(port_frame, text="Connecter", 
                                    font=('SF Pro Text', 12, 'bold'), 
                                    bg=self.colors['accent'], fg='white', 
                                    relief='flat', bd=0, padx=20, pady=10, 
                                    command=self.toggle_connection,
                                    cursor='hand2')
        self.connect_btn.pack(anchor='w', pady=(12, 0))

        # Statistiques épurées
        stats_frame = tk.Frame(controls_frame, bg=self.colors['secondary_section'])
        stats_frame.pack(fill=tk.X, pady=(25, 0))

        tk.Label(stats_frame, text="Statistiques",
                font=('SF Pro Display', 14, 'bold'),
                fg=self.colors['text'], bg=self.colors['secondary_section']).pack(anchor='w')

        self.stats_label = tk.Label(stats_frame,
                                   text=f"Messages reçus: {self.autorisations_recues}\nAlertes actives: 0\nNon reconnus: {self.codes_non_reconnus}",
                                   font=('SF Pro Text', 11),
                                   fg=self.colors['text_dim'],
                                   bg=self.colors['secondary_section'],
                                   justify='left')
        self.stats_label.pack(anchor='w', pady=(8, 0))

        # Section Actions
        actions_frame = tk.Frame(controls_frame, bg=self.colors['secondary_section'])
        actions_frame.pack(fill=tk.X, pady=(25, 0))

        tk.Label(actions_frame, text="Actions",
                font=('SF Pro Display', 14, 'bold'),
                fg=self.colors['text'], bg=self.colors['secondary_section']).pack(anchor='w')

        # Bouton STOP ALERTE principal
        self.stop_alert_btn = tk.Button(actions_frame, text="🔴 STOP ALERTE",
                                       font=('SF Pro Text', 12, 'bold'),
                                       bg=self.colors['danger'], fg='white',
                                       relief='flat', bd=0, padx=25, pady=12,
                                       command=self.mark_message_read,
                                       cursor='hand2', state=tk.DISABLED,
                                       width=20)
        self.stop_alert_btn.pack(anchor='w', pady=(10, 0))

        # Bouton SON ON/OFF
        self.sound_btn = tk.Button(actions_frame, text="🔊 SON ON",
                                  font=('SF Pro Text', 11, 'bold'),
                                  bg=self.colors['success'], fg='white',
                                  relief='flat', bd=0, padx=25, pady=10,
                                  command=self.toggle_sound,
                                  cursor='hand2', state=tk.DISABLED,
                                  width=20)
        self.sound_btn.pack(anchor='w', pady=(10, 0))

        # Console de debug supprimée

        # Carte principale: Journal des messages
        self.create_journal_section()




    def create_journal_section(self):
        # Le journal sera intégré dans la section principale
        # Trouve la section principale créée dans setup_ui
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame) and widget.cget('bg') == self.colors['bg']:
                main_container = widget
                break
        else:
            return

        # Trouve la section principale grise
        for widget in main_container.winfo_children():
            if isinstance(widget, tk.Frame) and widget.cget('bg') == self.colors['main_section']:
                main_section = widget
                break
        else:
            return

        # Bouton effacer dans la barre de titre
        clear_btn = tk.Button(main_section.winfo_children()[0], text="Effacer",
                             font=('SF Pro Text', 11), bg=self.colors['danger'], fg='white',
                             relief='flat', bd=0, padx=15, pady=8,
                             command=self.clear_console,
                             cursor='hand2')
        clear_btn.pack(side=tk.RIGHT, padx=25, pady=10)

        # Tableau épuré dans la section principale
        columns = ('statut', 'heure', 'message')
        self.journal = ttk.Treeview(main_section, columns=columns, show='headings', height=16)
        self.journal.heading('statut', text='🔔')
        self.journal.heading('heure', text='Heure')
        self.journal.heading('message', text='Message')
        self.journal.column('statut', width=50, anchor='center')
        self.journal.column('heure', width=100, anchor='center')
        self.journal.column('message', width=550, anchor='w')
        self.journal.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))

        # Binding pour la sélection
        self.journal.bind('<<TreeviewSelect>>', self.on_message_select)

        # Barre de défilement verticale épurée
        vsb = ttk.Scrollbar(self.journal.master, orient='vertical', command=self.journal.yview)
        self.journal.configure(yscrollcommand=vsb.set)
        vsb.place(in_=self.journal, relx=1.0, rely=0, relheight=1.0, anchor='ne')

        # Info de pied épurée
        footer = tk.Label(main_section, text="🚨 Alerte active • ✅ Alerte arrêtée • Sélectionnez un message et cliquez \"STOP ALERTE\" pour éteindre la LED clignotante",
                         font=('SF Pro Text', 10), fg=self.colors['text_dim'],
                         bg=self.colors['main_section'])
        footer.pack(anchor='w', padx=25, pady=(0, 20))

    def update_clock(self):
        try:
            now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            self.clock_label.configure(text=now)
        except Exception:
            pass
        finally:
            self.root.after(1000, self.update_clock)

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

                # Activer le bouton son quand connecté
                self.sound_btn.configure(state=tk.NORMAL)

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

            # Désactiver le bouton son quand déconnecté
            self.sound_btn.configure(state=tk.DISABLED)

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
                    # Ajoute uniquement le texte du message au journal
                    self.journal_message(message_recu)
                    self.autorisations_recues += 1
                    self.update_stats()
                    self.log(f"✅ MESSAGE REÇU: '{message_recu}'", 'success')
                else:
                    # Message vide détecté
                    self.display_access_status("⚠️ MESSAGE VIDE", "ERREUR RÉCEPTION", current_time, False)
                    self.codes_non_reconnus += 1
                    self.update_stats()
                    self.log("⚠️ Message vide reçu - Problème de décodage", 'error')

        # Alerte arrêtée par l'ESP
        elif "✅ ALERTE ARRÊTÉE - LED ÉTEINTE" in line:
            self.log("✅ ESP confirme: Alerte arrêtée - LED éteinte", 'success')

        # Message lu par l'ESP
        elif "📄 Message lu:" in line:
            # Extrait le message lu
            message_match = re.search(r"📄 Message lu: '([^']*)'", line)
            if message_match:
                message_lu = message_match.group(1)
                self.log(f"📖 Message lu confirmé: '{message_lu}'", 'success')
            else:
                self.log("📖 Message marqué comme lu", 'success')

        # Nouvelle alerte activée
        elif "🚨 NOUVELLE ALERTE ACTIVÉE - LED CLIGNOTANTE" in line:
            self.log("🚨 Nouvelle alerte activée sur l'ESP - LED clignote", 'warning')

        # Commande reçue par l'ESP
        elif "📝 Commande reçue:" in line:
            cmd_match = re.search(r"📝 Commande reçue: '([^']*)'", line)
            if cmd_match:
                commande = cmd_match.group(1)
                self.log(f"📝 ESP a reçu la commande: '{commande}'", 'info')

        # Son activé par l'ESP
        elif "🔊 SON ACTIVÉ" in line:
            self.sound_enabled = True
            self.update_sound_button()
            self.log("🔊 ESP confirme: Son activé", 'success')

        # Son désactivé par l'ESP
        elif "🔇 SON DÉSACTIVÉ" in line:
            self.sound_enabled = False
            self.update_sound_button()
            self.log("🔇 ESP confirme: Son désactivé", 'info')

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
        # Le statut est maintenant affiché dans le journal des messages
        # Plus besoin d'affichage séparé

    def journal_message(self, message_text):
        """Ajoute uniquement le message reçu dans le journal avec l'heure système"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            # Ajouter avec statut "alerte active"
            item_id = self.journal.insert('', tk.END, values=('🚨', timestamp, message_text))
            self.messages_non_lus.append(item_id)

            # Configurer l'emoji pour les messages en alerte
            self.journal.set(item_id, 'statut', '🚨')  # Alerte active

            if len(self.journal.get_children()) > 500:
                first = self.journal.get_children()[0]
                # Retirer de la liste des non lus si supprimé
                if first in self.messages_non_lus:
                    self.messages_non_lus.remove(first)
                self.journal.delete(first)

            last = self.journal.get_children()
            if last:
                self.journal.see(last[-1])
        except Exception:
            pass


    def update_stats(self):
        """Met à jour les statistiques"""
        alertes_actives = len(self.messages_non_lus)
        self.stats_label.configure(
            text=f"Messages reçus: {self.autorisations_recues}\nAlertes actives: {alertes_actives}\nNon reconnus: {self.codes_non_reconnus}")

    def log(self, message, msg_type='normal'):
        """Log interne (console UI supprimée)"""
        # Aucune sortie UI; peut être redirigé vers print si nécessaire
        return

    def on_message_select(self, event):
        """Gère la sélection d'un message"""
        try:
            selection = self.journal.selection()
            if selection:
                self.selected_message_id = selection[0]
                # Vérifier si le message est non lu (alerte active)
                if self.selected_message_id in self.messages_non_lus:
                    self.stop_alert_btn.configure(state=tk.NORMAL, bg=self.colors['danger'],
                                                 text="🔴 STOP ALERTE")
                else:
                    self.stop_alert_btn.configure(state=tk.DISABLED, bg=self.colors['text_dim'],
                                                 text="✅ ALERTE ARRÊTÉE")
            else:
                self.selected_message_id = None
                self.stop_alert_btn.configure(state=tk.DISABLED, bg=self.colors['text_dim'],
                                            text="🔴 STOP ALERTE")
        except Exception:
            pass

    def mark_message_read(self):
        """Marque le message sélectionné comme lu et envoie la commande stopalert à l'ESP"""
        if not self.selected_message_id or self.selected_message_id not in self.messages_non_lus:
            return

        try:
            # Envoyer la commande stopalert à l'ESP
            if self.connected and self.serial_connection:
                self.serial_connection.write(b"stopalert\n")
                self.log("Commande 'stopalert' envoyée à l'ESP", 'info')

            # Marquer le message comme lu visuellement
            self.journal.set(self.selected_message_id, 'statut', '✅')  # Alerte arrêtée

            # Retirer de la liste des non lus
            if self.selected_message_id in self.messages_non_lus:
                self.messages_non_lus.remove(self.selected_message_id)

            # Mettre à jour les statistiques
            self.update_stats()

            # Changer l'état du bouton
            self.stop_alert_btn.configure(state=tk.DISABLED, bg=self.colors['text_dim'],
                                        text="✅ ALERTE ARRÊTÉE")

            # Récupérer le texte du message pour affichage
            message_values = self.journal.item(self.selected_message_id)['values']
            if len(message_values) >= 3:
                message_text = message_values[2]
                self.log(f"🔴 Arrêt de l'alerte demandé pour: '{message_text}'", 'info')

        except Exception as e:
            self.log(f"Erreur lors de l'arrêt de l'alerte: {str(e)}", 'error')

    def toggle_sound(self):
        """Active/désactive le son des alertes sur l'ESP"""
        if not self.connected or not self.serial_connection:
            self.log("Erreur: Non connecté à l'ESP", 'error')
            return

        try:
            if self.sound_enabled:
                # Bouton affichait SON ON -> envoyer soundoff et passer à OFF
                self.serial_connection.write(b"soundoff\n")
                self.log("Commande 'soundoff' envoyée à l'ESP", 'info')
                self.sound_enabled = False
                self.update_sound_button()
            else:
                # Bouton affichait SON OFF -> envoyer soundon et passer à ON
                self.serial_connection.write(b"soundon\n")
                self.log("Commande 'soundon' envoyée à l'ESP", 'info')
                self.sound_enabled = True
                self.update_sound_button()

        except Exception as e:
            self.log(f"Erreur lors du toggle du son: {str(e)}", 'error')

    def update_sound_button(self):
        """Met à jour l'affichage du bouton son selon l'état actuel"""
        try:
            if self.sound_enabled:
                self.sound_btn.configure(text="🔊 SON ON", bg=self.colors['success'])
            else:
                self.sound_btn.configure(text="🔇 SON OFF", bg=self.colors['warning'])
        except Exception:
            pass

    def clear_console(self):
        """Efface la console"""
        # Efface le journal
        try:
            for iid in self.journal.get_children():
                self.journal.delete(iid)
            # Vider la liste des messages non lus
            self.messages_non_lus.clear()
            self.selected_message_id = None
            self.stop_alert_btn.configure(state=tk.DISABLED, bg=self.colors['text_dim'],
                                        text="🔴 STOP ALERTE")
            # Réinitialiser le bouton son aussi
            self.sound_btn.configure(state=tk.DISABLED)
            # Mettre à jour les stats
            self.update_stats()
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDRecepteurMonitor(root)
    root.mainloop()