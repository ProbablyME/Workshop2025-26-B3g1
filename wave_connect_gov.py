import tkinter as tk
from tkinter import scrolledtext, messagebox, font
import serial
import threading
from datetime import datetime
import time
from PIL import Image, ImageTk
import os

class WaveConnectGov:
    def __init__(self, root):
        self.root = root
        self.root.title("WAVE Connect - Système d'Alerte Gouvernemental")
        self.root.geometry("750x700")
        self.root.configure(bg='#f8f9fa')
        self.root.resizable(True, True)
        self.root.minsize(650, 600)

        # Variables
        self.message_alerte = ""
        self.serial_connection = None
        self.connected = False

        # Couleurs gouvernementales
        self.colors = {
            'bg': '#f8f9fa',
            'card': '#ffffff',
            'primary': '#1e40af',      # Bleu gouvernemental
            'secondary': '#374151',    # Gris foncé
            'text': '#111827',
            'text_light': '#6b7280',
            'success': '#059669',
            'danger': '#dc2626',
            'warning': '#d97706',
            'border': '#e5e7eb'
        }

        # Logo
        self.load_logo()

        # Configuration pour le scrolling
        self.setup_scrollable_container()

    def load_logo(self):
        """Charge le logo officiel"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(script_dir, "logo.png")

            if not os.path.exists(logo_path):
                logo_path = "logo.png"

            if not os.path.exists(logo_path):
                # Logo par défaut gouvernemental
                img = Image.new('RGB', (120, 120), color='#1e40af')
                self.logo_image = ImageTk.PhotoImage(img)
                return

            img = Image.open(logo_path)
            # Préserve le ratio: limite à 80x80 max
            img.thumbnail((80, 80), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
        except Exception as e:
            img = Image.new('RGB', (120, 120), color='#1e40af')
            self.logo_image = ImageTk.PhotoImage(img)

    def setup_scrollable_container(self):
        """Configure un container scrollable pour toute l'interface"""
        # Canvas principal avec scrollbars
        self.main_canvas = tk.Canvas(self.root, bg=self.colors['bg'], highlightthickness=0)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar verticale
        v_scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.main_canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Scrollbar horizontale
        h_scrollbar = tk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.main_canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, before=v_scrollbar)

        # Configuration du canvas
        self.main_canvas.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Frame conteneur pour tout le contenu
        self.scrollable_frame = tk.Frame(self.main_canvas, bg=self.colors['bg'])

        # Créer une fenêtre dans le canvas
        self.canvas_window = self.main_canvas.create_window(0, 0, anchor="nw", window=self.scrollable_frame)

        # Bind pour mettre à jour la scrollregion quand le contenu change
        self.scrollable_frame.bind('<Configure>', self.on_frame_configure)

        # Bind pour ajuster la largeur du frame au canvas
        self.main_canvas.bind('<Configure>', self.on_canvas_configure)

        # Bind la molette de souris pour le scroll vertical
        self.bind_mouse_scroll()

        # Maintenant configurer l'UI dans le frame scrollable
        self.setup_main_ui()

    def on_frame_configure(self, event=None):
        """Met à jour la scrollregion du canvas quand le frame change de taille"""
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Ajuste la largeur du frame intérieur pour correspondre au canvas"""
        canvas_width = event.width
        self.main_canvas.itemconfig(self.canvas_window, width=canvas_width)

    def bind_mouse_scroll(self):
        """Bind la molette de souris pour le défilement"""
        # Windows et Linux
        self.main_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        # Linux alternatif
        self.main_canvas.bind_all("<Button-4>", self.on_mousewheel)
        self.main_canvas.bind_all("<Button-5>", self.on_mousewheel)

    def on_mousewheel(self, event):
        """Gère le défilement avec la molette de souris"""
        # Windows
        if event.delta:
            self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # Linux
        elif event.num == 4:
            self.main_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.main_canvas.yview_scroll(1, "units")

    def setup_main_ui(self):
        """Interface principale de saisie"""
        # Header officiel (plus compact) - maintenant dans le frame scrollable
        header_frame = tk.Frame(self.scrollable_frame, bg=self.colors['primary'], height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Conteneur pour logo et titre
        header_content = tk.Frame(header_frame, bg=self.colors['primary'])
        header_content.pack(expand=True, fill='both', padx=15, pady=5)

        # Logo
        logo_label = tk.Label(header_content, image=self.logo_image, bg=self.colors['primary'])
        logo_label.pack(side=tk.LEFT)

        # Titre officiel
        title_frame = tk.Frame(header_content, bg=self.colors['primary'])
        title_frame.pack(side=tk.LEFT, padx=(20, 0), fill=tk.Y)

        title_label = tk.Label(title_frame, text="WAVE Connect",
                              font=('Segoe UI', 24, 'bold'),
                              fg='white', bg=self.colors['primary'])
        title_label.pack(anchor='w')

        subtitle_label = tk.Label(title_frame, text="Système Gouvernemental d'Alerte à la Population",
                                 font=('Segoe UI', 10),
                                 fg='#bfdbfe', bg=self.colors['primary'])
        subtitle_label.pack(anchor='w', pady=(2, 0))

        # Contenu principal
        main_content = tk.Frame(self.scrollable_frame, bg=self.colors['bg'])
        main_content.pack(expand=True, fill='both', padx=20, pady=15)

        # Section d'information (compacte)
        info_card = tk.Frame(main_content, bg=self.colors['card'], relief='solid', bd=1)
        info_card.pack(fill=tk.X, pady=(0, 15))

        info_content = tk.Frame(info_card, bg=self.colors['card'])
        info_content.pack(padx=20, pady=15)

        tk.Label(info_content, text="🚨 DIFFUSION D'ALERTE D'URGENCE - 433MHz",
                font=('Segoe UI', 14, 'bold'),
                fg=self.colors['primary'], bg=self.colors['card']).pack()

        tk.Label(info_content, text="1. Connecter • 2. Saisir message • 3. Envoyer • 4. Autoriser",
                font=('Segoe UI', 10),
                fg=self.colors['text'], bg=self.colors['card']).pack(pady=(5, 0))

        # Section de connexion COM
        com_card = tk.Frame(main_content, bg=self.colors['card'], relief='solid', bd=1)
        com_card.pack(fill=tk.X, pady=(0, 15))

        com_content = tk.Frame(com_card, bg=self.colors['card'])
        com_content.pack(padx=20, pady=15)

        tk.Label(com_content, text="🔌 CONNEXION SYSTÈME",
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['secondary'], bg=self.colors['card']).pack(anchor='w')

        # Sélection port COM
        com_frame = tk.Frame(com_content, bg=self.colors['card'])
        com_frame.pack(fill=tk.X, pady=(8, 0))

        tk.Label(com_frame, text="Port COM :",
                font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT)

        self.port_var = tk.StringVar(value="COM4")
        self.port_entry = tk.Entry(com_frame, textvariable=self.port_var,
                                  font=('Segoe UI', 11),
                                  bg='white', fg=self.colors['text'],
                                  width=8, relief='solid', bd=1)
        self.port_entry.pack(side=tk.LEFT, padx=(10, 15))

        self.connect_btn = tk.Button(com_frame, text="📡 CONNECTER",
                                    font=('Segoe UI', 11, 'bold'),
                                    bg=self.colors['success'], fg='white',
                                    relief='flat', padx=20, pady=8,
                                    command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT)

        # Statut de connexion
        self.connection_status = tk.Label(com_frame, text="⚪ NON CONNECTÉ",
                                         font=('Segoe UI', 11, 'bold'),
                                         fg=self.colors['text_light'], bg=self.colors['card'])
        self.connection_status.pack(side=tk.LEFT, padx=(15, 0))

        # Section de saisie
        input_card = tk.Frame(main_content, bg=self.colors['card'], relief='solid', bd=1)
        input_card.pack(fill=tk.BOTH, expand=True)

        input_content = tk.Frame(input_card, bg=self.colors['card'])
        input_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        tk.Label(input_content, text="📢 MESSAGE D'ALERTE À LA POPULATION",
                font=('Segoe UI', 14, 'bold'),
                fg=self.colors['secondary'], bg=self.colors['card']).pack(anchor='w')

        tk.Label(input_content, text="Rédigez votre message d'urgence (maximum 50 caractères) :",
                font=('Segoe UI', 10),
                fg=self.colors['text_light'], bg=self.colors['card']).pack(anchor='w', pady=(5, 10))

        # Zone de texte
        text_frame = tk.Frame(input_content, bg=self.colors['card'])
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.message_text = scrolledtext.ScrolledText(text_frame,
                                                    font=('Segoe UI', 11),
                                                    bg='#ffffff', fg=self.colors['text'],
                                                    height=6, relief='solid', bd=1,
                                                    wrap=tk.WORD)
        self.message_text.pack(fill=tk.BOTH, expand=True)

        # Compteur de caractères
        self.char_counter = tk.Label(input_content, text="0 / 50 caractères",
                                    font=('Segoe UI', 9),
                                    fg=self.colors['text_light'], bg=self.colors['card'])
        self.char_counter.pack(anchor='e', pady=(5, 10))

        # Binding pour le compteur
        self.message_text.bind('<KeyRelease>', self.update_char_count)

        # Section boutons
        button_section = tk.Frame(input_content, bg=self.colors['card'])
        button_section.pack(fill=tk.X, pady=(5, 0))

        # Label de statut de carte (au-dessus du bouton de test)
        self.card_status_label = tk.Label(button_section, text="",
                                         font=('Segoe UI', 14, 'bold'),
                                         bg=self.colors['card'])
        self.card_status_label.pack(pady=(0, 10))

        # Bouton de test de connexion
        self.send_message_btn = tk.Button(button_section, text="📡 TESTER CONNEXION",
                                         font=('Segoe UI', 11, 'bold'),
                                         bg=self.colors['warning'], fg='white',
                                         relief='flat', padx=25, pady=8,
                                         command=self.send_message_to_system,
                                         state=tk.DISABLED)
        self.send_message_btn.pack(pady=(0, 10))

        # Bouton d'établissement du message
        self.demander_btn = tk.Button(button_section, text="📢 ÉTABLIR MESSAGE ET ATTENDRE CARTE",
                                     font=('Segoe UI', 12, 'bold'),
                                     bg=self.colors['primary'], fg='white',
                                     relief='raised', padx=30, pady=15,
                                     command=self.demander_autorisation,
                                     state=tk.DISABLED)
        self.demander_btn.pack()


        # Statut du message
        self.message_status = tk.Label(button_section, text="⚪ AUCUN MESSAGE ÉTABLI",
                                      font=('Segoe UI', 10, 'bold'),
                                      fg=self.colors['text_light'], bg=self.colors['card'])
        self.message_status.pack(pady=(8, 0))

        # Footer officiel
        footer = tk.Frame(self.scrollable_frame, bg=self.colors['border'], height=1)
        footer.pack(fill=tk.X)

        footer_text = tk.Label(self.scrollable_frame, text="Classification: USAGE OFFICIEL • Autorisation requise",
                              font=('Segoe UI', 9),
                              fg=self.colors['text_light'], bg=self.colors['bg'])
        footer_text.pack(pady=10)

    def update_char_count(self, event=None):
        """Met à jour le compteur de caractères"""
        content = self.message_text.get(1.0, tk.END).strip()
        char_count = len(content)

        self.char_counter.configure(text=f"{char_count} / 50 caractères")

        if char_count > 50:
            self.char_counter.configure(fg=self.colors['danger'])
        elif char_count > 180:
            self.char_counter.configure(fg=self.colors['warning'])
        else:
            self.char_counter.configure(fg=self.colors['text_light'])

    def toggle_connection(self):
        """Connecter/déconnecter du système"""
        if not self.connected:
            port = self.port_var.get()
            try:
                self.serial_connection = serial.Serial(
                    port=port,
                    baudrate=11550,
                    timeout=0.1
                )
                self.connected = True
                self.connection_status.configure(text="🟢 CONNECTÉ", fg=self.colors['success'])
                self.connect_btn.configure(text="🔌 DÉCONNECTER", bg=self.colors['danger'])
                self.send_message_btn.configure(state=tk.NORMAL)

                # Démarre la lecture série
                threading.Thread(target=self.read_serial, daemon=True).start()

            except Exception as e:
                self.connection_status.configure(text="🔴 ÉCHEC CONNEXION", fg=self.colors['danger'])
                messagebox.showerror("Erreur de Connexion",
                                   f"Impossible de se connecter au port {port}\n\n"
                                   f"Vérifiez :\n"
                                   f"• ESP8266 connecté et allumé\n"
                                   f"• Port COM correct (COM3, COM4, etc.)\n"
                                   f"• Aucune autre application n'utilise le port\n\n"
                                   f"Erreur: {str(e)}")
        else:
            if self.serial_connection:
                self.serial_connection.close()
            self.connected = False
            self.connection_status.configure(text="⚪ NON CONNECTÉ", fg=self.colors['text_light'])
            self.connect_btn.configure(text="📡 CONNECTER", bg=self.colors['success'])
            self.send_message_btn.configure(state=tk.DISABLED)
            self.demander_btn.configure(state=tk.DISABLED)

    def send_message_to_system(self):
        """Envoie un message de test"""
        if not self.connected or not self.serial_connection:
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord au système.")
            return

        try:
            # Envoie un ping test pour vérifier la connexion
            self.serial_connection.write(b"PING\n")
            self.message_status.configure(text="🟢 TEST RÉUSSI - PRÊT À ENVOYER", fg=self.colors['success'])
            self.demander_btn.configure(state=tk.NORMAL, bg=self.colors['primary'])

            # Affiche le test réussi dans le label de statut au lieu d'une popup
            self.card_status_label.configure(text="✅ CONNEXION VÉRIFIÉE", fg=self.colors['success'])
            self.root.after(3000, lambda: self.card_status_label.configure(text=""))

        except Exception as e:
            self.card_status_label.configure(text="❌ ERREUR DE CONNEXION", fg=self.colors['danger'])
            self.root.after(3000, lambda: self.card_status_label.configure(text=""))

    def demander_autorisation(self):
        """Établit le message et attend la carte pour envoi automatique"""
        message = self.message_text.get(1.0, tk.END).strip()

        if not message:
            self.card_status_label.configure(text="⚠️ MESSAGE REQUIS", fg=self.colors['warning'])
            self.root.after(3000, lambda: self.card_status_label.configure(text=""))
            return

        if len(message) > 50:
            self.card_status_label.configure(text="⚠️ MESSAGE TROP LONG (MAX 50)", fg=self.colors['danger'])
            self.root.after(3000, lambda: self.card_status_label.configure(text=""))
            return

        if not self.connected or not self.serial_connection:
            self.card_status_label.configure(text="⚠️ NON CONNECTÉ", fg=self.colors['warning'])
            self.root.after(3000, lambda: self.card_status_label.configure(text=""))
            return

        # Envoie le message au système ESP8266
        try:
            command = f"MSG:{message}\n"
            self.serial_connection.write(command.encode())

            self.message_alerte = message

            # Affiche l'état dans le label
            self.card_status_label.configure(text="📡 MESSAGE ÉTABLI - PASSEZ VOTRE CARTE",
                                            fg=self.colors['primary'])

            # Change le texte mais garde le bouton actif pour annuler si besoin
            self.demander_btn.configure(text="🔄 ATTENTE CARTE - CLIQUER POUR ANNULER",
                                       bg=self.colors['warning'], state=tk.NORMAL,
                                       command=self.reset_message)
            self.message_status.configure(text="📡 EN ATTENTE DE CARTE", fg=self.colors['warning'])

        except Exception as e:
            self.card_status_label.configure(text="❌ ERREUR D'ENVOI", fg=self.colors['danger'])
            self.root.after(3000, lambda: self.card_status_label.configure(text=""))

    def read_serial(self):
        """Lit les messages série en continu"""
        while self.connected and self.serial_connection:
            try:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.root.after(0, lambda l=line: self.process_line(l))
                else:
                    time.sleep(0.01)
            except Exception as e:
                break

    def process_line(self, line):
        """Traite les messages reçus du système"""
        print(f"[WAVE] {line}")  # Debug dans la console

        # Message établi avec succès
        if "Nouveau message défini:" in line:
            print("Message défini avec succès")

        # Carte RFID détectée
        elif "Carte détectée" in line:
            print("🎯 Carte RFID détectée")

        # UID autorisé - Transmission OK
        elif "DEBUG: UID AUTORISÉ" in line:
            self.root.after(0, self.show_success)

        # UID non autorisé
        elif "DEBUG: UID NON AUTORISÉ" in line:
            self.root.after(0, self.show_error)

        # Transmission terminée avec succès
        elif "DEBUG: Transmission terminée avec succès" in line:
            print("✅ Transmission 433MHz réussie")

    def show_success(self):
        """Affiche le succès d'autorisation"""
        # Affiche le message de succès dans le label
        self.card_status_label.configure(text="✅ CARTE VALIDÉE - MESSAGE ENVOYÉ",
                                        fg=self.colors['success'])

        # Réactive les boutons pour permettre un nouvel envoi
        self.demander_btn.configure(text="📢 ÉTABLIR MESSAGE ET ATTENDRE CARTE",
                                   bg=self.colors['primary'], state=tk.NORMAL,
                                   command=self.demander_autorisation)
        self.message_status.configure(text="✅ DERNIER ENVOI RÉUSSI", fg=self.colors['success'])

        # L'ESP gère lui-même son état, pas besoin de reset

        # Efface le message après 5 secondes
        self.root.after(5000, lambda: self.card_status_label.configure(text=""))

    def reset_message(self):
        """Annule le message en attente et réinitialise l'interface"""
        # Réinitialise l'interface
        self.demander_btn.configure(text="📢 ÉTABLIR MESSAGE ET ATTENDRE CARTE",
                                   bg=self.colors['primary'], state=tk.NORMAL,
                                   command=self.demander_autorisation)
        self.message_status.configure(text="⚪ MESSAGE ANNULÉ", fg=self.colors['text_light'])

        # Affiche l'annulation dans le label
        self.card_status_label.configure(text="⚪ MESSAGE ANNULÉ", fg=self.colors['text_light'])
        self.root.after(3000, lambda: self.card_status_label.configure(text=""))

    def show_error(self):
        """Affiche l'erreur d'autorisation"""
        # Affiche le message d'erreur dans le label
        self.card_status_label.configure(text="❌ CARTE REFUSÉE",
                                        fg=self.colors['danger'])

        # Garde le message actif en attente d'une carte valide
        self.demander_btn.configure(text="🔒 RÉESSAYEZ AVEC UNE CARTE VALIDE",
                                   bg=self.colors['danger'], state=tk.NORMAL,
                                   command=self.reset_message)
        self.message_status.configure(text="❌ CARTE REFUSÉE - MESSAGE TOUJOURS ACTIF", fg=self.colors['danger'])

        # Efface le message après 5 secondes
        self.root.after(5000, lambda: self.card_status_label.configure(text=""))

    # Supprimé - plus besoin d'interface de validation séparée

    # Supprimé - plus besoin d'animation

    # Supprimé - le monitoring se fait maintenant côté ESP8266

    # Supprimé - plus besoin de monitoring depuis l'interface

    # Supprimé - plus besoin de traitement des lignes

    # Supprimé - plus besoin d'affichage de résultat

    # Supprimé - plus besoin de boutons de simulation

    # Supprimé - plus besoin de fermeture de validation

    # Supprimé - plus besoin d'annulation de validation

if __name__ == "__main__":
    root = tk.Tk()
    app = WaveConnectGov(root)
    root.mainloop()