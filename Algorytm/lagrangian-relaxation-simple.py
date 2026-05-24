import networkx as nx

#=============================================================================
'''
#1. Dane wejściowe - SCENARIUSZ PODSTAWOWY
wezly = [1, 2, 3, 4, 5, 6]
towary = ['A', 'B']

# Struktura sieci - (poczatek, koniec): przepustowosc
luki_dane = {
    (1, 2): 15,
    (2, 3): 10, 
    (3, 4): 15,
    (1, 3): 20, 
    (1, 4): 5, 
    (2, 4): 10,
    (1, 5): 10, 
    (5, 4): 15, 
    (3, 6): 20, 
    (2, 6): 25, 
    (6, 4): 10
}
luki = list(luki_dane.keys())
przepustowosci = luki_dane

# Koszt przesyłu - ('towar', poczatek, koniec): koszt
koszty = {
    ('A', 1, 2): 10, ('A', 2, 3): 5, ('A', 3, 4): 10, ('A', 1, 3): 15,
    ('A', 1, 4): 50, ('A', 2, 4): 20, ('A', 1, 5): 5, ('A', 5, 4): 10,
    ('A', 3, 6): 20, ('A', 2, 6): 25, ('A', 6, 4): 7,
    ('B', 1, 2): 2, ('B', 2, 3): 15, ('B', 3, 4): 5, ('B', 1, 3): 10,
    ('B', 1, 4): 30, ('B', 2, 4): 10, ('B', 1, 5): 3, ('B', 5, 4): 5,
    ('B', 3, 6): 15, ('B', 2, 6): 20, ('B', 6, 4): 5
}

# Wyznaczenie popytow dla algorytmu Dijkstry
popyty = {
    'A': {'zrodlo': 1, 'ujscie': 4, 'ilosc': 10},
    'B': {'zrodlo': 1, 'ujscie': 4, 'ilosc': 5}
}
'''

#1. Dane wejściowe - SCENARIUSZ KONFLIKTU
wezly = [1, 2, 3, 4, 5, 6]
towary = ['A', 'B']

# Struktura sieci - (poczatek, koniec): przepustowosc
luki_dane = {
    (1, 2): 7,      # Drastycznie zmniejszamy przepustowość kluczowego łuku (1, 2) - teraz jest wąskim gardłem
    (2, 3): 10, 
    (3, 4): 15,
    (1, 3): 20, 
    (1, 4): 5, 
    (2, 4): 10,
    (1, 5): 10, 
    (5, 4): 15, 
    (3, 6): 20, 
    (2, 6): 25, 
    (6, 4): 10
}
luki = list(luki_dane.keys())
przepustowosci = luki_dane

# 2. Zmieniamy koszty, aby oba towary "pchały się" na łuk (1, 2)
koszty = {
    # Łuk (1, 2) jest super tani dla obu (priorytet)
    ('A', 1, 2): 1, ('B', 1, 2): 1, 
    
    # Podnosimy koszt (1, 5) dla towaru A - teraz woli iść górą przez (1, 2)
    ('A', 1, 5): 500, # Było 5, teraz jest drożej niż objazdy
    
    # Reszta kosztów pozostaje podobna lub bez zmian
    ('A', 2, 3): 5, ('A', 3, 4): 10, ('A', 1, 3): 500, ('A', 1, 4): 500, ('A', 2, 4): 20, 
    ('A', 5, 4): 10, ('A', 3, 6): 20, ('A', 2, 6): 25, ('A', 6, 4): 7, 
    ('B', 2, 3): 15, ('B', 3, 4): 5, ('B', 1, 3): 500,
    ('B', 1, 4): 500, ('B', 2, 4): 10, ('B', 1, 5): 500, ('B', 5, 4): 5,
    ('B', 3, 6): 15, ('B', 2, 6): 20, ('B', 6, 4): 5
}

# Wyznaczenie popytow dla algorytmu Dijkstry
popyty = {
    'A': {'zrodlo': 1, 'ujscie': 4, 'ilosc': 10},
    'B': {'zrodlo': 1, 'ujscie': 4, 'ilosc': 5}
}
#=============================================================================

#=============================================================================
# 2. INICJALIZACJA STRUKTUR DANYCH I PARAMETRÓW
#=============================================================================
# Tworzymy graf skierowany wykorzystując bibliotekę NetworkX
G = nx.DiGraph()
G.add_edges_from(luki)

# Inicjalizacja mnożników Lagrange'a (kary za przeciążenia łuków) na 0.
w_mnozniki = {(i, j): 0.0 for (i, j) in luki}

# Parametry optymalizacji
maks_iteracji = 50
najlepsze_rozwiazanie = None
najmniejsze_przekroczenie = float('inf')

#=============================================================================
# 3. GŁÓWNA PĘTLA ALGORYTMU (RELAKSACJA LAGRANGE'A)
#=============================================================================
for q in range(1, maks_iteracji + 1):
    
    # Obliczamy rozmiar kroku (theta). Szybko malejący krok.
    theta_q = 1.0 / q 
    
    sciezki_iteracji = {}
    przeplyw_luki_iteracji = {(i, j): 0 for (i, j) in luki}
    
    # -------------------------------------------------------------------------
    # KROK A: ROZWIĄZYWANIE PODPROBLEMÓW (Najkrótsze ścieżki)
    # -------------------------------------------------------------------------
    for t in towary:
        # Przygotowanie wag w grafie NetworkX: Koszt = bazowy + kara
        for (i, j) in luki:
            koszt_bazowy = koszty.get((t, i, j), float('inf'))
            G[i][j]['weight'] = max(0.0, koszt_bazowy + w_mnozniki[(i, j)])
            
        zrodlo = popyty[t]['zrodlo']
        ujscie = popyty[t]['ujscie']
        ilosc = popyty[t]['ilosc']
        
        # Wywołanie algorytmu Dijkstry z biblioteki NetworkX (zwraca węzły)
        trasa_wezly = nx.shortest_path(G, source=zrodlo, target=ujscie, weight='weight')
        
        # Konwersja listy węzłów na listę krawędzi (łuków)
        trasa = [(trasa_wezly[m], trasa_wezly[m+1]) for m in range(len(trasa_wezly)-1)]
        sciezki_iteracji[t] = trasa
        
        # Symulujemy puszczenie całego ruchu tą jedną ścieżką
        for luk in trasa:
            przeplyw_luki_iteracji[luk] += ilosc

    # -------------------------------------------------------------------------
    # KROK B: HEURYSTYKA NAPRAWCZA 
    # (Brak w wersji podstawowej - puszczamy ruch bez rozdzielania i oceniamy)
    # -------------------------------------------------------------------------
    suma_przekroczen = sum(max(0, przeplyw_luki_iteracji[luk] - przepustowosci[luk]) for luk in luki)
    
    if suma_przekroczen < najmniejsze_przekroczenie:
        najmniejsze_przekroczenie = suma_przekroczen
        najlepsze_rozwiazanie = (sciezki_iteracji.copy(), przeplyw_luki_iteracji.copy())
        
    if suma_przekroczen == 0:
        print(f"Znaleziono optymalne dopuszczalne rozwiązanie w iteracji {q}.")
        break

    # -------------------------------------------------------------------------
    # KROK C: AKTUALIZACJA MNOŻNIKÓW (Karanie przeciążonych łuków)
    # -------------------------------------------------------------------------
    for (i, j) in luki:
        subgradient = przeplyw_luki_iteracji[(i, j)] - przepustowosci[(i, j)]
        w_mnozniki[(i, j)] = max(0.0, w_mnozniki[(i, j)] + theta_q * subgradient)

#=============================================================================
# 4. WYPISANIE WYNIKÓW 
#=============================================================================
trasy_wynik, przeplywy_wynik = najlepsze_rozwiazanie

calkowity_koszt = 0
for t in towary:
    ilosc = popyty[t]['ilosc']
    for luk in trasy_wynik[t]:
        calkowity_koszt += koszty[(t, luk[0], luk[1])] * ilosc

print(f"Koszt całkowity: {calkowity_koszt}")

print("\n--- Wybrane trasy (przepływy niezerowe) ---")
for t in towary:
    print(f"\nTowar {t}:")
    przeplyw_znaleziony = False
    
    ilosc = popyty[t]['ilosc']
    aktywne_luki = trasy_wynik[t] 
    
    for (i, j) in luki:
        if (i, j) in aktywne_luki:
            print(f"  Łuk ({i} -> {j}): wysłano {ilosc} jednostek")
            przeplyw_znaleziony = True
            
    if not przeplyw_znaleziony:
        print("  Brak przepływu dla tego towaru.")