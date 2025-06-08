import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import re
import io
import webbrowser

last_sources_urls = []
last_photo_bytes = None
last_wiki_url = None

def extract_money(text):
    pattern = r'(\$\s?[\d,.]+(?:\s?million|\s?billion)?|\d+[\s.,]?\d*\s?(?:million|mille|milliard|million|millions|millions USD|USD))'
    return re.findall(pattern, text, re.IGNORECASE)

def clean_money(money_str):
    money_str = money_str.replace('$', '').replace('USD', '').replace('€', '').replace(',', '.').strip().lower()
    if 'million' in money_str:
        return float(re.findall(r'[\d.]+', money_str)[0]) * 1_000_000
    if 'milliard' in money_str or 'billion' in money_str:
        return float(re.findall(r'[\d.]+', money_str)[0]) * 1_000_000_000
    numbers = re.findall(r'[\d.]+', money_str)
    if numbers:
        return float(numbers[0])
    return None

def get_net_worth(name):
    global last_sources_urls
    query = f"{name} net worth"
    last_sources_urls = []
    net_worths = []
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, region='wt-wt', safesearch='Off', max_results=7)]
        for res in results:
            try:
                url = res['href']
                html = requests.get(url, timeout=7, headers={'User-Agent':'Mozilla/5.0'}).text
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text(separator=' ', strip=True)
                page_title = soup.title.string if soup.title else ""
                if name.lower() not in page_title.lower() and name.lower() not in text.lower():
                    continue
                montant_trouve = False
                for m in extract_money(text):
                    money = clean_money(m)
                    if money and 10_000 < money < 10_000_000_000:
                        i = text.lower().find(m.lower())
                        if i != -1:
                            snippet = text[max(0, i-80):i+80].lower()
                            if name.lower() in snippet:
                                net_worths.append(money)
                                montant_trouve = True
                if montant_trouve and url not in last_sources_urls:
                    last_sources_urls.append(url)
            except Exception:
                pass
        # Calcul de fiabilité
        nb_sources = len(last_sources_urls)
        if net_worths:
            moyenne = sum(net_worths) / len(net_worths)
            if nb_sources >= 3:
                fiabilite = ("Donnée probablement fiable", "green")
            elif nb_sources == 2:
                fiabilite = ("À prendre avec prudence", "orange")
            else:
                fiabilite = ("Non fiable / source unique", "red")
            return f"{moyenne/1_000_000:.1f} millions USD (moyenne sur {nb_sources} sources distinctes)", fiabilite
        else:
            return "Aucune estimation trouvée.", ("Aucune estimation fiable trouvée", "red")
    except Exception as e:
        return "Erreur réseau ou DuckDuckGo", ("Erreur technique", "red")

def get_wikipedia_data(name):
    url_search = "https://fr.wikipedia.org/w/api.php"
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': name,
        'format': 'json'
    }
    try:
        data = requests.get(url_search, params=params, timeout=8).json()
        results = data.get('query', {}).get('search', [])
        if not results:
            return None, None, None
        page_title = results[0]['title']
        params2 = {
            'action': 'query',
            'format': 'json',
            'prop': 'extracts|pageimages',
            'exintro': True,
            'explaintext': True,
            'titles': page_title,
            'pithumbsize': 180
        }
        data2 = requests.get(url_search, params=params2, timeout=8).json()
        pages = data2.get('query', {}).get('pages', {})
        for page_id, page in pages.items():
            extract = page.get('extract', "")
            img_url = page.get('thumbnail', {}).get('source', None)
            wiki_url = f"https://fr.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
            if extract and len(extract.split()) > 8 and name.split()[0].lower() in extract.lower():
                return extract, wiki_url, img_url
        return None, None, None
    except Exception as e:
        return None, None, None

def lancer_recherche(event=None):
    nom = entry_nom.get()
    if not nom.strip():
        messagebox.showwarning("Champ vide", "Veuillez entrer le nom d'une personnalité.")
        return
    result_label.config(text="Recherche en cours...", foreground="blue")
    fortune_label.config(text="")
    fiab_label.config(text="")
    bio_text.config(state="normal")
    bio_text.delete('1.0', tk.END)
    bio_text.config(state="disabled")
    photo_label.config(image='')
    bouton_wiki.config(state="disabled")
    bouton_rechercher.config(state="disabled")
    bouton_copier.config(state="disabled")
    bouton_sources.config(state="disabled")
    root.update()
    threading.Thread(target=run_full_search, args=(nom,), daemon=True).start()

def run_full_search(nom):
    global last_photo_bytes, last_wiki_url
    last_photo_bytes = None
    fortune, fiabilite = get_net_worth(nom)
    bio, wiki_url, img_url = get_wikipedia_data(nom)

    fortune_label.config(text=f"Fortune estimée : {fortune}", foreground=fiabilite[1])
    fiab_label.config(text=f"Fiabilité : {fiabilite[0]}", foreground=fiabilite[1])
    last_wiki_url = wiki_url
    if wiki_url:
        bouton_wiki.config(state="normal")
    else:
        bouton_wiki.config(state="disabled")
    bio_text.config(state="normal")
    bio_text.delete('1.0', tk.END)
    if bio:
        bio_text.insert(tk.END, bio)
        bio_text.tag_configure("justif", justify="left")
        bio_text.tag_add("justif", "1.0", "end")
    else:
        bio_text.insert(tk.END, "Aucun résumé trouvé.")
    bio_text.config(state="disabled")
    if img_url:
        try:
            img_bytes = requests.get(img_url, timeout=8).content
            last_photo_bytes = img_bytes
            pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            pil_img.thumbnail((120, 120))
            tk_img = ImageTk.PhotoImage(pil_img)
            photo_label.config(image=tk_img)
            photo_label.image = tk_img
        except Exception:
            photo_label.config(image='')
            last_photo_bytes = None
    else:
        photo_label.config(image='')
        last_photo_bytes = None

    result_label.config(text=f"Résultats pour {nom} :")
    bouton_rechercher.config(state="normal")
    bouton_copier.config(state="normal")
    bouton_sources.config(state="normal" if last_sources_urls else "disabled")

def copier_resultat():
    txt = result_label.cget("text") + "\n" + fortune_label.cget("text") + "\n"
    txt += fiab_label.cget("text") + "\n"
    txt += bio_text.get('1.0', tk.END).strip()
    if last_wiki_url:
        txt += "\nLien Wikipédia : " + last_wiki_url
    root.clipboard_clear()
    root.clipboard_append(txt)
    messagebox.showinfo("Copié !", "Résumé copié dans le presse-papier.")

def ouvrir_wiki():
    if last_wiki_url:
        webbrowser.open_new(last_wiki_url)

def show_sources():
    if not last_sources_urls:
        messagebox.showinfo("Sources", "Aucune source disponible.")
        return
    src_window = tk.Toplevel(root)
    src_window.title("Sources utilisées pour la fortune")
    src_window.geometry("520x300")
    src_window.resizable(False, False)
    label = ttk.Label(src_window, text="Sources (cliquez pour ouvrir) :", font=('Segoe UI', 11))
    label.pack(pady=10)
    listbox = tk.Listbox(src_window, font=('Segoe UI', 10), cursor="hand2", width=70)
    listbox.pack(fill="both", expand=True, padx=20, pady=5)
    for url in last_sources_urls:
        listbox.insert(tk.END, url)
    def open_url(event):
        idx = listbox.curselection()
        if idx:
            webbrowser.open_new(listbox.get(idx[0]))
    listbox.bind("<Double-Button-1>", open_url)
    close_btn = ttk.Button(src_window, text="Fermer", command=src_window.destroy)
    close_btn.pack(pady=8)

def show_large_photo(event=None):
    global last_photo_bytes
    if not last_photo_bytes:
        return
    try:
        pil_img = Image.open(io.BytesIO(last_photo_bytes)).convert("RGBA")
        w, h = pil_img.size
        max_w, max_h = min(w, 420), min(h, 420)
        pil_img.thumbnail((max_w, max_h))
        large_win = tk.Toplevel(root)
        large_win.title("Photo agrandie")
        large_win.geometry(f"{pil_img.width+20}x{pil_img.height+20}")
        large_win.resizable(True, True)
        img_large = ImageTk.PhotoImage(pil_img)
        img_label = ttk.Label(large_win, image=img_large)
        img_label.image = img_large
        img_label.pack(padx=10, pady=10)
        large_win.focus_force()
    except Exception:
        messagebox.showinfo("Agrandissement impossible", "Impossible d'afficher l'image en grand.")

root = tk.Tk()
root.title("Estimation Fortune & Bio Personnalités - MegaGPT")

w, h = 500, 560
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
x, y = (sw - w) // 2, (sh - h) // 2
root.geometry(f"{w}x{h}+{x}+{y}")
root.resizable(False, False)

frame = ttk.Frame(root, padding=16)
frame.pack(expand=True, fill="both")

label = ttk.Label(frame, text="Nom de la personnalité :", font=('Segoe UI', 12))
label.pack(pady=(0, 5))

entry_nom = ttk.Entry(frame, font=('Segoe UI', 12))
entry_nom.pack(fill="x", padx=5, pady=(0, 10))
entry_nom.focus_set()
entry_nom.bind('<Return>', lancer_recherche)

bouton_rechercher = ttk.Button(frame, text="Rechercher", command=lancer_recherche)
bouton_rechercher.pack(pady=(0, 10))

result_label = ttk.Label(frame, text="", font=('Segoe UI', 11), anchor="center")
result_label.pack(pady=(2, 3), fill="x")

fortune_label = ttk.Label(frame, text="", font=('Segoe UI', 11), wraplength=420, anchor="center")
fortune_label.pack(pady=(2, 1), fill="x")

fiab_label = ttk.Label(frame, text="", font=('Segoe UI', 10, "italic"))
fiab_label.pack(pady=(0,3), fill="x")

bio_photo_frame = ttk.Frame(frame)
bio_photo_frame.pack(pady=(10, 0), fill="x")

photo_label = ttk.Label(bio_photo_frame)
photo_label.pack(side="left", padx=(0, 15))
photo_label.bind("<Button-1>", show_large_photo)

bio_text_frame = ttk.Frame(bio_photo_frame)
bio_text_frame.pack(side="left", fill="both", expand=True)

bio_text = tk.Text(bio_text_frame, font=('Segoe UI', 10), wrap="word", height=8, width=44)
bio_text.pack(side="left", fill="both", expand=True)
bio_text.config(state="disabled", relief="flat", bg="white")

scrollbar = ttk.Scrollbar(bio_text_frame, orient="vertical", command=bio_text.yview)
scrollbar.pack(side="right", fill="y")
bio_text['yscrollcommand'] = scrollbar.set

buttons_frame = ttk.Frame(frame)
buttons_frame.pack(pady=(20, 0), fill="x")

bouton_wiki = ttk.Button(buttons_frame, text="Voir Wikipédia", command=ouvrir_wiki, state="disabled")
bouton_wiki.pack(side="left", padx=8)

bouton_sources = ttk.Button(buttons_frame, text="Voir les sources", command=show_sources, state="disabled")
bouton_sources.pack(side="left", padx=8)

bouton_copier = ttk.Button(buttons_frame, text="Copier le résultat", command=copier_resultat, state="disabled")
bouton_copier.pack(side="right", padx=8)

root.mainloop()
