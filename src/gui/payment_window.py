import os
import webbrowser
import urllib.parse
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from datetime import datetime
from src.license_manager import LicenseManager


class PaymentWindow(ctk.CTkToplevel):
    def __init__(self, parent, license_manager: LicenseManager, callback=None):
        super().__init__(parent)
        self.title("Passer à la version Premium")
        self.geometry("600x650")
        self.resizable(False, False)
        self.parent = parent

        # --- AMÉLIORATION DE PERFORMANCE ---
        # 1. Cacher la fenêtre temporairement pour éviter le "flash" blanc
        # pendant que les widgets sont en cours de création.
        self.withdraw()

        self.license_manager = license_manager
        self.callback = callback

        # --- Centraliser le numéro de téléphone ---
        self.CONTACT_PHONE = "+257 62 305 671"
        self.WHATSAPP_NUMBER = "243827788173" # Sans le '+' pour les liens wa.me

        self.create_widgets()

        # --- AMÉLIORATION DE PERFORMANCE ---
        # 2. Forcer le traitement de toutes les tâches de dessin et de géométrie
        # avant d'afficher la fenêtre.
        self.update_idletasks()

        # 3. Rendre la fenêtre modale et l'afficher maintenant qu'elle est prête.
        self.transient(parent)
        self.deiconify() # Affiche la fenêtre
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Titre
        title_label = ctk.CTkLabel(self, text="Choisissez votre plan Premium", font=("Helvetica", 24, "bold"))
        title_label.pack(pady=(20, 10))

        # Description
        desc_text = "Débloquez toutes les fonctionnalités premium et profitez d'une expérience sans limites."
        desc_label = ctk.CTkLabel(self, text=desc_text, font=("Helvetica", 14))
        desc_label.pack(pady=(0, 20))

        # Plans
        plans_frame = ctk.CTkScrollableFrame(self, label_text="Choisissez votre plan")
        plans_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Plan mensuel
        monthly_frame = self.create_plan_frame(
            plans_frame,
            "Mensuel",
            "2 800 FBU",
            ["Téléchargements illimités", "Qualité HD (1080p+)", "Audio 320kbps", "Support prioritaire"],
            "monthly"
        )
        monthly_frame.pack(pady=10, padx=10, fill="x")

        # Plan annuel
        yearly_frame = self.create_plan_frame(
            plans_frame,
            "Annuel",
            "15 800 FBU",
            ["Téléchargements illimités", "Qualité HD (1080p+)", "Audio 320kbps", "Support prioritaire", "Économisez 33%"],
            "yearly",
            is_recommended=True
        )
        yearly_frame.pack(pady=10, padx=10, fill="x")

        # Plan à vie
        lifetime_frame = self.create_plan_frame(
            plans_frame,
            "À vie",
            "39 900 FBU",
            ["Téléchargements illimités", "Qualité HD (1080p+)", "Audio 320kbps", "Support prioritaire", "Paiement unique"],
            "lifetime"
        )
        lifetime_frame.pack(pady=10, padx=10, fill="x")

        # Activation de licence
        license_frame = ctk.CTkFrame(self)
        license_frame.pack(pady=20, padx=20, fill="x")

        license_label = ctk.CTkLabel(license_frame, text="Vous avez un code d'activation ?", font=("Helvetica", 14, "bold"))
        license_label.pack(pady=(10, 5), padx=10, anchor="w")

        license_entry_frame = ctk.CTkFrame(license_frame, fg_color="transparent")
        license_entry_frame.pack(pady=5, padx=10, fill="x")

        self.license_entry = ctk.CTkEntry(license_entry_frame, width=400, placeholder_text="Entrez votre clé de licence")
        self.license_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        activate_button = ctk.CTkButton(license_entry_frame, text="Activer", command=self.activate_license)
        activate_button.pack(side="right")

        # Informations de paiement sécurisé
        security_frame = ctk.CTkFrame(self)
        security_frame.pack(pady=10, padx=20, fill="x")

        security_text = "🔒 Paiement sécurisé | Support local au Burundi | Satisfait ou remboursé sous 30 jours"
        security_label = ctk.CTkLabel(security_frame, text=security_text, font=("Helvetica", 12))
        security_label.pack(pady=10)

        # Informations de contact
        contact_frame = ctk.CTkFrame(self)
        contact_frame.pack(pady=5, padx=20, fill="x")

        contact_text = f"📞 Besoin d'aide? Contactez-nous au {self.CONTACT_PHONE} ou par email à vitalzagabe156@gmail.com"
        contact_label = ctk.CTkLabel(contact_frame, text=contact_text, font=("Helvetica", 12))
        contact_label.pack(pady=10)

    def create_plan_frame(self, parent, title, price, features, plan_type, is_recommended=False):
        # Couleurs adaptatives selon le thème actuel
        mode = ctk.get_appearance_mode()
        if is_recommended:
            bg_color = "#1e293b" if mode == "Dark" else "#dbeafe"
        else:
            bg_color = "#0f172a" if mode == "Dark" else "#f1f5f9"

        frame = ctk.CTkFrame(parent, fg_color=bg_color)

        # Badge recommandé
        if is_recommended:
            badge_frame = ctk.CTkFrame(frame, fg_color="#fbbf24", corner_radius=5)
            badge_frame.pack(pady=(10, 0), padx=10, anchor="ne")
            badge_label = ctk.CTkLabel(badge_frame, text="RECOMMANDÉ", font=("Helvetica", 10, "bold"), text_color="#000")
            badge_label.pack(pady=2, padx=5)

        # Titre et prix
        title_label = ctk.CTkLabel(frame, text=title, font=("Helvetica", 18, "bold"))
        title_label.pack(pady=(15, 5), padx=15)

        price_label = ctk.CTkLabel(frame, text=price, font=("Helvetica", 24, "bold"), text_color="#60a5fa")
        price_label.pack(pady=(0, 10))

        # Fonctionnalités
        for feature in features:
            feature_frame = ctk.CTkFrame(frame, fg_color="transparent")
            feature_frame.pack(pady=2, padx=15, fill="x")

            check_label = ctk.CTkLabel(feature_frame, text="✓", font=("Helvetica", 14, "bold"), text_color="#4ade80")
            check_label.pack(side="left", padx=(0, 5))

            feature_label = ctk.CTkLabel(feature_frame, text=feature, font=("Helvetica", 12))
            feature_label.pack(side="left", fill="x")

        # Bouton d'achat
        button_text = "Acheter maintenant"
        button_color = "#2563eb" if is_recommended else "#1d4ed8"
        hover_color = "#1d4ed8" if is_recommended else "#1e40af"

        purchase_button = ctk.CTkButton(
            frame,
            text=button_text,
            command=lambda: self.process_payment(plan_type),
            fg_color=button_color,
            hover_color=hover_color,
            height=35
        )
        purchase_button.pack(pady=15, padx=15)

        return frame

    def process_payment(self, plan_type):
        # Afficher les options de paiement disponibles au Burundi
        payment_options = [
            "Mobile Money (Lumicash)",
            "Mobile Money (Ecocash)",
            "Carte bancaire",
            "Virement bancaire"
        ]

        payment_window = ctk.CTkToplevel(self)
        payment_window.title("Choisir un mode de paiement")
        payment_window.geometry("400x350")
        payment_window.resizable(False, False)
        payment_window.transient(self)
        payment_window.grab_set()

        # Titre
        title_label = ctk.CTkLabel(payment_window, text="Choisissez votre mode de paiement", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(20, 15))

        # Prix selon le plan
        price_text = {
            "monthly": "2 800 FBU",
            "yearly": "15 800 FBU",
            "lifetime": "39 900 FBU"
        }

        price_label = ctk.CTkLabel(payment_window, text=f"Montant à payer: {price_text.get(plan_type)}", font=("Helvetica", 14))
        price_label.pack(pady=(0, 20))

        # Options de paiement
        payment_var = tk.StringVar(value=payment_options[0])

        for option in payment_options:
            radio_button = ctk.CTkRadioButton(payment_window, text=option, variable=payment_var, value=option)
            radio_button.pack(pady=5, padx=20, anchor="w")

        # Boutons
        button_frame = ctk.CTkFrame(payment_window, fg_color="transparent")
        button_frame.pack(pady=20, fill="x")

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=payment_window.destroy,
            fg_color="#64748b",
            hover_color="#475569"
        )
        cancel_button.pack(side="left", padx=20)

        pay_button = ctk.CTkButton(
            button_frame,
            text="Procéder au paiement",
            command=lambda: self.handle_payment_selection(payment_window, payment_var.get(), plan_type)
        )
        pay_button.pack(side="right", padx=20)

    def handle_payment_selection(self, payment_window, payment_method, plan_type):
        payment_window.destroy()

        # Prix selon le plan
        price_text = {
            "monthly": "2 800 FBU",
            "yearly": "15 800 FBU",
            "lifetime": "39 900 FBU"
        }
        price = price_text.get(plan_type)

        # Afficher le formulaire de paiement selon la méthode choisie
        if "Lumicash" in payment_method:
            instructions = f"1. Composez *163#\n2. Sélectionnez 'Transfert d'argent'\n3. Envoyez l'argent au numéro {self.CONTACT_PHONE}\n4. Montant à payer: {price}\n5. Prenez une capture d'écran du message de confirmation"
            self._create_payment_form_window(plan_type, price, "Lumicash", instructions)
        elif "Ecocash" in payment_method:
            instructions = f"Pour payer avec Ecocash:\n\n1. Composez *151#\n2. Sélectionnez 'Payer'\n3. Envoyez l'argent au numéro {self.CONTACT_PHONE}\n4. Entrez le montant: {price}\n5. Confirmez avec votre code PIN\n6. Prenez une capture d'écran du message de confirmation"

            response = messagebox.askyesno(
                f"Instructions de paiement - {payment_method}",
                f"{instructions}\n\nUne fois le paiement effectué, vous devrez remplir un formulaire avec vos informations et la capture d'écran.\n\nSouhaitez-vous continuer?"
            )

            if response:
                ecocash_instructions = f"1. Composez *151#\n2. Sélectionnez 'Payer'\n3. Envoyez l'argent au numéro {self.CONTACT_PHONE}\n4. Montant à payer: {price}\n5. Prenez une capture d'écran du message de confirmation"
                self._create_payment_form_window(plan_type, price, "Ecocash", ecocash_instructions)
        elif "Carte bancaire" in payment_method:
            instructions = (
                f"Pour payer par carte bancaire:\n\n"
                f"1. Contactez-nous au {self.CONTACT_PHONE} ou par WhatsApp\n"
                f"2. Indiquez votre ID Utilisateur et le plan choisi\n"
                f"3. Montant à payer: {price}\n"
                f"4. Vous recevrez votre clé de licence après confirmation du paiement"
            )
            response = messagebox.askyesno(
                f"Instructions de paiement - {payment_method}",
                f"{instructions}\n\nSouhaitez-vous nous contacter par WhatsApp maintenant?"
            )
            if response:
                msg = urllib.parse.quote(
                    f"Bonjour, je souhaite acheter le plan {plan_type} ({price}).\n"
                    f"Mon ID Utilisateur: {self.license_manager.user_id}"
                )
                webbrowser.open(f'https://wa.me/{self.WHATSAPP_NUMBER}?text={msg}')
        else:  # Virement bancaire
            instructions = f"Pour payer par virement bancaire:\n\nBanque: Banque de la République du Burundi\nCompte: 123456789\nBénéficiaire: TelVid\nRéférence: Votre adresse email\n\nMontant: {price}"

            response = messagebox.askyesno(
                f"Instructions de paiement - {payment_method}",
                f"{instructions}\n\nUne fois le paiement effectué, envoyez le reçu de paiement à vitalzagabe156@gmail.com\n\nSouhaitez-vous continuer?"
            )

            if response:
                # Ouvrir le client email par défaut
                webbrowser.open('mailto:vitalzagabe156@gmail.com?subject=Paiement%20TelVid&body=Bonjour,%0A%0AJe%20viens%20d\'effectuer%20un%20paiement%20pour%20TelVid.%0A%0APlan:%20' + plan_type + '%0AMontant:%20' + price.replace(' ', '%20') + '%0A%0AMerci%20de%20m\'envoyer%20ma%20clé%20de%20licence.%0A%0ACordialement,')
                messagebox.showinfo("Email", "Veuillez envoyer le reçu de paiement par email avec vos informations. Vous recevrez votre clé de licence dès que le paiement sera vérifié.")

    def _create_payment_form_window(self, plan_type, price, payment_method, instructions_text):
        """Crée une fenêtre de formulaire générique pour les paiements manuels."""
        form_window = ctk.CTkToplevel(self)
        form_window.title(f"Paiement par {payment_method}")
        form_window.geometry("600x700")
        form_window.resizable(False, False)
        form_window.transient(self)
        form_window.grab_set()

        # Titre
        title_label = ctk.CTkLabel(form_window, text=f"Paiement par {payment_method}", font=("Helvetica", 20, "bold"))
        title_label.pack(pady=(20, 10))

        # Instructions
        instructions_frame = ctk.CTkFrame(form_window)
        instructions_frame.pack(pady=10, padx=20, fill="x")

        instructions_label = ctk.CTkLabel(instructions_frame, text=instructions_text, font=("Helvetica", 14), justify="left")
        instructions_label.pack(pady=10, padx=10)

        # Formulaire
        form_frame = ctk.CTkScrollableFrame(form_window, label_text="Veuillez remplir vos informations")
        form_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # ID Utilisateur (non modifiable)
        user_id_label = ctk.CTkLabel(form_frame, text="Votre ID Utilisateur (à ne pas modifier) :", font=("Helvetica", 14, "bold"))
        user_id_label.pack(pady=(10, 0), padx=10, anchor="w")
        user_id_entry = ctk.CTkEntry(form_frame, width=400)
        user_id_entry.pack(pady=(0, 10), padx=10, fill="x")
        user_id_entry.insert(0, self.license_manager.user_id)
        user_id_entry.configure(state="readonly")

        # Nom
        name_label = ctk.CTkLabel(form_frame, text="Nom:", font=("Helvetica", 14))
        name_label.pack(pady=(10, 0), padx=10, anchor="w")
        name_entry = ctk.CTkEntry(form_frame, width=400)
        name_entry.pack(pady=(0, 10), padx=10, fill="x")

        # Prénom
        surname_label = ctk.CTkLabel(form_frame, text="Prénom:", font=("Helvetica", 14))
        surname_label.pack(pady=(10, 0), padx=10, anchor="w")
        surname_entry = ctk.CTkEntry(form_frame, width=400)
        surname_entry.pack(pady=(0, 10), padx=10, fill="x")

        # Email
        email_label = ctk.CTkLabel(form_frame, text="Adresse email:", font=("Helvetica", 14))
        email_label.pack(pady=(10, 0), padx=10, anchor="w")
        email_entry = ctk.CTkEntry(form_frame, width=400)
        email_entry.pack(pady=(0, 10), padx=10, fill="x")

        # Numéro de téléphone
        phone_label = ctk.CTkLabel(form_frame, text="Numéro de téléphone (utilisé pour le paiement):", font=("Helvetica", 14))
        phone_label.pack(pady=(10, 0), padx=10, anchor="w")
        phone_entry = ctk.CTkEntry(form_frame, width=400)
        phone_entry.pack(pady=(0, 10), padx=10, fill="x")

        # Montant payé
        amount_label = ctk.CTkLabel(form_frame, text="Montant payé:", font=("Helvetica", 14))
        amount_label.pack(pady=(10, 0), padx=10, anchor="w")
        amount_entry = ctk.CTkEntry(form_frame, width=400)
        amount_entry.pack(pady=(0, 10), padx=10, fill="x")
        amount_entry.insert(0, price)  # Pré-remplir avec le prix du plan

        # Capture d'écran
        screenshot_label = ctk.CTkLabel(form_frame, text="Capture d'écran du paiement:", font=("Helvetica", 14))
        screenshot_label.pack(pady=(10, 0), padx=10, anchor="w")

        screenshot_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        screenshot_frame.pack(pady=(0, 10), padx=10, fill="x")

        screenshot_path_var = tk.StringVar()
        screenshot_entry = ctk.CTkEntry(screenshot_frame, width=300, textvariable=screenshot_path_var)
        screenshot_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        def browse_screenshot():
            file_path = filedialog.askopenfilename(
                title="Sélectionner la capture d'écran",
                filetypes=[("Images", "*.png *.jpg *.jpeg")]
            )
            if file_path:
                screenshot_path_var.set(file_path)

        browse_button = ctk.CTkButton(screenshot_frame, text="Parcourir", command=browse_screenshot)
        browse_button.pack(side="right")

        # Boutons d'action
        buttons_frame = ctk.CTkFrame(form_window, fg_color="transparent")
        buttons_frame.pack(pady=20, padx=20, fill="x")

        # Bouton de réclamation
        def open_whatsapp():
            # Ouvrir WhatsApp avec le numéro spécifié
            webbrowser.open(f'https://wa.me/{self.WHATSAPP_NUMBER}')

        claim_button = ctk.CTkButton(
            buttons_frame,
            text="Réclamation",
            command=open_whatsapp,
            fg_color="#64748b",
            hover_color="#475569"
        )
        claim_button.pack(side="left", padx=10)

        # Bouton d'annulation
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=form_window.destroy,
            fg_color="#64748b",
            hover_color="#475569"
        )
        cancel_button.pack(side="left", padx=10)

        # Bouton de validation
        def submit_form():
            # Vérifier que tous les champs sont remplis
            if not name_entry.get() or not surname_entry.get() or not email_entry.get() or not phone_entry.get() or not amount_entry.get() or not screenshot_path_var.get():
                messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
                return

            # Récupérer toutes les valeurs AVANT de détruire les fenêtres pour éviter l'erreur "invalid command name"
            name = name_entry.get()
            surname = surname_entry.get()
            email = email_entry.get()
            phone = phone_entry.get()
            amount = amount_entry.get()
            screenshot_path = screenshot_path_var.get()
            user_id = user_id_entry.get() # Récupérer l'ID utilisateur

            try:
                # Proposer le choix à l'utilisateur pour l'envoi de la confirmation
                choice_window = ctk.CTkToplevel(form_window)
                choice_window.title("Choisir la méthode d'envoi")
                choice_window.geometry("450x180")
                choice_window.transient(form_window)
                choice_window.grab_set()

                ctk.CTkLabel(choice_window, text="Comment souhaitez-vous nous envoyer la confirmation de paiement ?", font=("Helvetica", 14)).pack(pady=20)

                email_body = f"Bonjour,\n\nJe viens d'effectuer un paiement pour TelVid.\n\nID Utilisateur: {user_id}\nNom: {name}\nPrénom: {surname}\nEmail: {email}\nTéléphone: {phone}\nPlan: {plan_type}\nMontant: {amount}\nMéthode de paiement: {payment_method}\n\nMerci de m'envoyer ma clé de licence.\n\nCordialement,\n{name} {surname}"

                def send_by_email():
                    choice_window.destroy()
                    form_window.destroy()
                    subject = urllib.parse.quote(f"Paiement TelVid - {payment_method} - Capture d'écran")
                    body = urllib.parse.quote(email_body)
                    to = "vitalzagabe156@gmail.com"
                    webbrowser.open(f'mailto:{to}?subject={subject}&body={body}')
                    messagebox.showinfo("Email", "Votre client email est ouvert. Veuillez joindre manuellement la capture d'écran avant d'envoyer.")

                def send_by_whatsapp():
                    choice_window.destroy()
                    form_window.destroy()
                    whatsapp_body = f"Confirmation de paiement TelVid:\n- ID Utilisateur: {user_id}\n- Nom: {name} {surname}\n- Email: {email}\n- Tél: {phone}\n- Plan: {plan_type}\n- Montant: {amount}\n- Méthode: {payment_method}"
                    encoded_text = urllib.parse.quote(whatsapp_body)
                    webbrowser.open(f'https://wa.me/{self.WHATSAPP_NUMBER}?text={encoded_text}')
                    messagebox.showinfo("WhatsApp", "WhatsApp est ouvert. Veuillez envoyer le message et joindre manuellement la capture d'écran.")

                choice_button_frame = ctk.CTkFrame(choice_window, fg_color="transparent")
                choice_button_frame.pack(pady=20, fill="x", expand=True)

                ctk.CTkButton(choice_button_frame, text="Envoyer par Email", command=send_by_email).pack(side="left", expand=True, padx=10)
                ctk.CTkButton(choice_button_frame, text="Envoyer par WhatsApp", command=send_by_whatsapp).pack(side="right", expand=True, padx=10)

            except Exception as e:
                messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")

        submit_button = ctk.CTkButton(
            buttons_frame,
            text="Valider",
            command=submit_form
        )
        submit_button.pack(side="right", padx=10)

    def close_license_window(self, window):
        window.destroy()

    def activate_license(self):
        license_key = self.license_entry.get().strip()
        if not license_key:
            messagebox.showerror("Erreur", "Veuillez entrer une clé de licence valide")
            return

        success, message = self.license_manager.activate_license(license_key)

        if success:
            messagebox.showinfo("Activation réussie", message)
            self.on_close(success=True)
        else:
            messagebox.showerror("Erreur d'activation", message)

    def on_close(self, success=False):
        self.grab_release()
        self.destroy()
        if self.callback and success:
            self.callback()