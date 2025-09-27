import threading
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import warnings
# Supprimer les RuntimeWarning (dont celui sur le renommage du package)
# Note: pour supprimer l'avertissement à la source, installez la nouvelle lib `ddgs`.
warnings.simplefilter("ignore", RuntimeWarning)

try:
    # package renommé -> essayer ddgs en premier
    from ddgs import DDGS
except Exception:
    try:
        from duckduckgo_search import DDGS
    except Exception:
        sys.stderr.write(
            "Missing dependency: please install 'duckduckgo-search' or 'ddgs' in the active Python environment.\n"
        )
        sys.stderr.write(
            "With the project's venv, run:\n  E:/projets_madum/fortune/.venv/Scripts/python.exe -m pip install duckduckgo-search\n  or\n  E:/projets_madum/fortune/.venv/Scripts/python.exe -m pip install ddgs\n"
        )
        raise

# Essayer de forcer stdout en UTF-8 pour éviter UnicodeEncodeError sur Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    # Python <3.7 ou environnements où reconfigure n'existe pas -> ignorer
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

def search_networth(name, region=None, max_results=10, safesearch="Off"):
    """Effectue la recherche et renvoie une liste d'objets avec champs stringifiés.

    region: None pour laisser la librairie choisir, ou une chaîne comme 'us-en'.
    """
    # Essayer plusieurs variantes de requête pour augmenter les chances d'obtenir des résultats
    queries = [f"{name} net worth", name, f"{name} networth"]
    results = []
    seen = set()
    kwargs = {"safesearch": safesearch, "max_results": max_results}
    if region is not None:
        kwargs["region"] = region

    with DDGS() as ddgs:
        for q in queries:
            try:
                for r in ddgs.text(q, **kwargs):
                    href = r.get("href") or ""
                    title = r.get("title") or ""
                    body = r.get("body") or ""
                    key = (href, title)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append({
                        "href": str(href),
                        "title": str(title),
                        "body": str(body),
                    })
                    if len(results) >= max_results:
                        return results
            except Exception:
                # ignorer les erreurs pour une variante et continuer
                continue

    return results


def extract_net_worth(results):
    """Analyse les titres / bodies pour extraire une estimation de fortune.

    Retourne une chaîne (par ex. "$80 million") ou None.
    """
    import re

    # motifs communs
    patterns = [
        r"\$\s?[0-9]+(?:[\.,][0-9]+)?\s?(?:million|billion|m|bn|milliards|millions|billion|billion)",
        r"[0-9]+(?:[\.,][0-9]+)?\s?(?:million|billion|m|bn|milliards|millions|billion|billion)\s?(?:USD|dollars)?",
        r"[0-9]+(?:[\.,][0-9]+)?\s?[Mm]\b",
        r"£\s?[0-9]+(?:[\.,][0-9]+)?",
        r"€\s?[0-9]+(?:[\.,][0-9]+)?",
    ]

    text = "\n".join((r.get('title','') + '\n' + r.get('body','')) for r in results)
    text = text.replace('\xa0', ' ')
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return None

def on_search():
    name = entry_name.get().strip()
    if not name:
        messagebox.showwarning("Champ vide", "Veuillez entrer un nom.")
        return
    btn_search.config(state=tk.DISABLED)
    txt_results.delete(1.0, tk.END)

    def worker():
        try:
            # Ne pas forcer de region par défaut — laisser la librairie choisir
            results = search_networth(name, region=None, max_results=10)

            def update_ui():
                global current_results
                current_results = results
                if not results:
                    lbl_estimation.config(text="🤷‍♀️ Oups — pas d'estimation trouvée. Essaie un autre nom !", foreground="#b33a3a")
                    lbl_count.config(text="0 sources")
                    btn_more.config(state=tk.DISABLED)
                else:
                    # Extraire estimation de fortune et l'afficher joyeusement
                    est = extract_net_worth(results)
                    if est:
                        # afficher uniquement la valeur trouvée, sans texte additionnel
                        lbl_estimation.config(text=est, foreground="#0a7f3e")
                    else:
                        # ne rien afficher si aucune estimation claire
                        lbl_estimation.config(text="", foreground="#0a7f3e")

                    # compter combien mentionnent explicitement 'net worth' ou 'networth'
                    def mentions_networth(r):
                        t = (r.get('title','') + '\n' + r.get('body','')).lower()
                        return ('net worth' in t) or ('networth' in t)

                    match_count = sum(1 for r in results if mentions_networth(r))
                    lbl_count.config(text=f"{len(results)} sources ({match_count} mentionnent 'net worth')")
                    btn_more.config(state=tk.NORMAL)
                btn_search.config(state=tk.NORMAL)

            root.after(0, update_ui)
        except Exception as e:
            def show_err():
                messagebox.showerror("Erreur", str(e))
                btn_search.config(state=tk.NORMAL)
            root.after(0, show_err)

    threading.Thread(target=worker, daemon=True).start()

root = tk.Tk()
root.title("Recherche Fortune (Net Worth)")
# Ne pas forcer une geometry fixe : laisser la fenêtre s'ajuster au contenu
# Autoriser le redimensionnement par l'utilisateur
root.resizable(True, True)

frame = ttk.Frame(root, padding=6)
frame.pack(fill=tk.X)

# Ligne unique : entry + bouton + estimation + compteur + plus d'infos
hframe = ttk.Frame(frame)
hframe.pack(fill=tk.X, expand=False)

entry_name = ttk.Entry(hframe, width=36)
entry_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,6))
entry_name.bind("<Return>", lambda e: on_search())

btn_search = ttk.Button(hframe, text="Rechercher", command=on_search)
btn_search.pack(side=tk.LEFT, padx=(0,6))

# Label d'estimation (placé entre la zone de recherche et la ligne des sources)
lbl_estimation = ttk.Label(frame, text="", anchor=tk.CENTER, justify=tk.CENTER)
lbl_estimation.config(font=("Segoe UI", 12, "bold"))
lbl_estimation.pack(fill=tk.X, pady=(6,0))

# Nouvelle ligne sous la ligne principale pour le compteur et le bouton 'Plus d'infos'
vframe = ttk.Frame(frame)
vframe.pack(fill=tk.X, pady=(8,0))

# Remettre lbl_count et btn_more dans vframe (on créera des remplacements)
# Supprimer les instances précédentes et recréer dans vframe
lbl_count = ttk.Label(vframe, text="0 sources")
lbl_count.pack(side=tk.LEFT, padx=(0,8), anchor=tk.CENTER)

btn_more = ttk.Button(vframe, text="Plus d'infos", state=tk.DISABLED)
btn_more.pack(side=tk.LEFT)

# Zone de résultats (cachée par défaut) conservée pour debug
# Créer l'objet mais ne pas le pack() pour éviter qu'il force la fenêtre à grandir
txt_results = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=6)
# ne pas pack() par défaut

current_results = []

def open_link(url):
    import webbrowser
    if url:
        webbrowser.open(url)

def show_more():
    top = tk.Toplevel(root)
    top.title("Plus d'infos — sources")
    top.geometry("800x600")
    frm = ttk.Frame(top, padding=10)
    frm.pack(fill=tk.BOTH, expand=True)
    if not current_results:
        ttk.Label(frm, text="Aucune source disponible.").pack()
        return
    for i, r in enumerate(current_results, 1):
        title = r.get('title','')
        href = r.get('href','')
        body = r.get('body','')
        tlower = (title + '\n' + body).lower()
        star = '★ ' if ('net worth' in tlower or 'networth' in tlower) else ''
        lbl = ttk.Label(frm, text=f"[{i}] {star}{title}", wraplength=760)
        lbl.pack(anchor=tk.W, pady=(5,0))
        link = ttk.Button(frm, text=href or 'ouvrir', command=(lambda u=href: open_link(u)))
        link.pack(anchor=tk.W)

btn_more.config(command=show_more)

def _adjust_window_to_contents():
    # Forcer la fenêtre à la taille requise par ses widgets pour éviter un grand vide
    try:
        root.update_idletasks()
        w = root.winfo_reqwidth()
        h = root.winfo_reqheight()
        # appliquer geometry minimale
        root.geometry(f"{w}x{h}")
        root.minsize(w, h)
    except Exception:
        pass

def run_cli_mode():
    # Mode CLI pour tests rapides
    name = ' '.join(sys.argv[sys.argv.index('--cli')+1:]) if '--cli' in sys.argv and len(sys.argv) > sys.argv.index('--cli')+1 else 'john cena'
    print(f"Recherche (CLI) : {name}")
    try:
        res = search_networth(name, region=None, max_results=10)
        est = extract_net_worth(res)
        if est:
            print(f"Estimation trouvée : {est}\n")
        print(f"{len(res)} résultats")
        for i, r in enumerate(res, 1):
            print(f"[{i}] {r.get('title','')} - {r.get('href','')}\n{r.get('body','')}\n")
    except Exception as e:
        print("Erreur:", e)


if __name__ == '__main__':
    if '--cli' in sys.argv:
        run_cli_mode()
    else:
        # ajuster la fenêtre à son contenu pour éviter un grand vide
        _adjust_window_to_contents()
        root.mainloop()
