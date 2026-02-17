import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# -------------------- DATABÁZE --------------------

conn = sqlite3.connect("sklad.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS produkty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nazev TEXT NOT NULL,
    cena REAL NOT NULL,
    mnozstvi INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS objednavky (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datum TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS polozky_objednavky (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    objednavka_id INTEGER,
    produkt_id INTEGER,
    ks INTEGER
)
""")

conn.commit()

aktualni_objednavka_id = None

# -------------------- PRODUKTY --------------------

def pridat_produkt():
    nazev = entry_nazev.get()
    cena = entry_cena.get()
    mnozstvi = entry_mnozstvi.get()

    if not nazev or not cena or not mnozstvi:
        messagebox.showerror("Chyba", "Vyplň všechna pole!")
        return

    try:
        cena = float(cena)
        mnozstvi = int(mnozstvi)
    except:
        messagebox.showerror("Chyba", "Cena musí být číslo a množství celé číslo!")
        return

    cursor.execute("INSERT INTO produkty (nazev, cena, mnozstvi) VALUES (?, ?, ?)",
                   (nazev, cena, mnozstvi))
    conn.commit()
    zobraz_produkty()

def zobraz_produkty():
    for row in tree_produkty.get_children():
        tree_produkty.delete(row)

    cursor.execute("SELECT * FROM produkty")
    for row in cursor.fetchall():
        tree_produkty.insert("", "end", values=row)

# -------------------- OBJEDNÁVKY --------------------

def vytvorit_objednavku():
    global aktualni_objednavka_id

    datum = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO objednavky (datum) VALUES (?)", (datum,))
    conn.commit()

    aktualni_objednavka_id = cursor.lastrowid
    label_objednavka.config(text=f"Aktuální objednávka ID: {aktualni_objednavka_id}")

    vymaz_polozky()
    messagebox.showinfo("Info", "Objednávka vytvořena")

def pridat_do_objednavky():
    global aktualni_objednavka_id

    if aktualni_objednavka_id is None:
        messagebox.showerror("Chyba", "Nejprve vytvoř objednávku!")
        return

    produkt_id = entry_produkt_id.get()
    ks = entry_ks.get()

    if not produkt_id or not ks:
        messagebox.showerror("Chyba", "Vyplň pole!")
        return

    try:
        produkt_id = int(produkt_id)
        ks = int(ks)
    except:
        messagebox.showerror("Chyba", "ID i ks musí být číslo!")
        return

    cursor.execute("SELECT nazev, mnozstvi FROM produkty WHERE id = ?", (produkt_id,))
    produkt = cursor.fetchone()

    if produkt is None:
        messagebox.showerror("Chyba", "Produkt neexistuje!")
        return

    nazev, sklad = produkt

    if sklad < ks:
        messagebox.showerror("Chyba", "Nedostatek na skladě!")
        return

    cursor.execute("""
        INSERT INTO polozky_objednavky (objednavka_id, produkt_id, ks)
        VALUES (?, ?, ?)
    """, (aktualni_objednavka_id, produkt_id, ks))

    cursor.execute("""
        UPDATE produkty SET mnozstvi = mnozstvi - ?
        WHERE id = ?
    """, (ks, produkt_id))

    conn.commit()

    zobraz_produkty()
    zobraz_polozky()
    messagebox.showinfo("Info", "Přidáno do objednávky")

def zobraz_polozky():
    for row in tree_polozky.get_children():
        tree_polozky.delete(row)

    cursor.execute("""
        SELECT p.nazev, po.ks
        FROM polozky_objednavky po
        JOIN produkty p ON po.produkt_id = p.id
        WHERE po.objednavka_id = ?
    """, (aktualni_objednavka_id,))

    for row in cursor.fetchall():
        tree_polozky.insert("", "end", values=row)

def vymaz_polozky():
    for row in tree_polozky.get_children():
        tree_polozky.delete(row)

# -------------------- EXPORT --------------------

def export_objednavky():
    if aktualni_objednavka_id is None:
        messagebox.showerror("Chyba", "Žádná aktivní objednávka")
        return

    cursor.execute("""
        SELECT p.nazev, po.ks
        FROM polozky_objednavky po
        JOIN produkty p ON po.produkt_id = p.id
        WHERE po.objednavka_id = ?
    """, (aktualni_objednavka_id,))

    data = cursor.fetchall()

    with open(f"objednavka_{aktualni_objednavka_id}.txt", "w", encoding="utf-8") as f:
        f.write(f"Objednávka ID: {aktualni_objednavka_id}\n")
        f.write("================================\n")
        for row in data:
            f.write(f"{row[0]} - {row[1]} ks\n")

    messagebox.showinfo("Info", "Export hotov!")

# -------------------- GUI --------------------

root = tk.Tk()
root.title("Skladový systém")

# ----- PRODUKTY -----
frame1 = tk.Frame(root)
frame1.pack(pady=10)

tk.Label(frame1, text="Název").grid(row=0, column=0)
entry_nazev = tk.Entry(frame1)
entry_nazev.grid(row=0, column=1)

tk.Label(frame1, text="Cena").grid(row=1, column=0)
entry_cena = tk.Entry(frame1)
entry_cena.grid(row=1, column=1)

tk.Label(frame1, text="Množství").grid(row=2, column=0)
entry_mnozstvi = tk.Entry(frame1)
entry_mnozstvi.grid(row=2, column=1)

tk.Button(frame1, text="Přidat produkt", command=pridat_produkt)\
    .grid(row=3, columnspan=2, pady=5)

tree_produkty = ttk.Treeview(root, columns=("ID", "Nazev", "Cena", "Mnozstvi"), show="headings")
tree_produkty.heading("ID", text="ID")
tree_produkty.heading("Nazev", text="Název")
tree_produkty.heading("Cena", text="Cena")
tree_produkty.heading("Mnozstvi", text="Množství")
tree_produkty.pack()

zobraz_produkty()

# ----- OBJEDNÁVKY -----
frame2 = tk.Frame(root)
frame2.pack(pady=15)

label_objednavka = tk.Label(frame2, text="Aktuální objednávka ID: žádná")
label_objednavka.grid(row=0, columnspan=2)

tk.Button(frame2, text="Vytvořit objednávku", command=vytvorit_objednavku)\
    .grid(row=1, columnspan=2, pady=5)

tk.Label(frame2, text="ID produktu").grid(row=2, column=0)
entry_produkt_id = tk.Entry(frame2)
entry_produkt_id.grid(row=2, column=1)

tk.Label(frame2, text="Ks").grid(row=3, column=0)
entry_ks = tk.Entry(frame2)
entry_ks.grid(row=3, column=1)

tk.Button(frame2, text="Přidat do objednávky", command=pridat_do_objednavky)\
    .grid(row=4, columnspan=2, pady=5)

tree_polozky = ttk.Treeview(root, columns=("Nazev", "Ks"), show="headings")
tree_polozky.heading("Nazev", text="Produkt")
tree_polozky.heading("Ks", text="Ks")
tree_polozky.pack(pady=5)

tk.Button(root, text="Export aktuální objednávky", command=export_objednavky)\
    .pack(pady=10)

root.mainloop()
