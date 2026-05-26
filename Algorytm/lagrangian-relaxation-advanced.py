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
# [ZMIANA WOBEC WERSJI PODSTAWOWEJ]: Zwiększono liczbę iteracji z 50 na 100, aby dać heurystyce więcej czasu na poszukiwania.
maks_iteracji = 100

# [ZMIANA WOBEC WERSJI PODSTAWOWEJ]: Zamiast 'najmniejsze_przekroczenie' szukamy rozwiązania, które ma najmniejszy koszt, ALE jest w 100% legalne fizycznie.
najlepszy_koszt_dopuszczalny = float('inf')
najlepsze_przeplywy_aktywnie = {t: {(i, j): 0 for (i, j) in luki} for t in towary}

# [ZMIANA WOBEC WERSJI PODSTAWOWEJ]: Nowa struktura. Baza wiedzy o ścieżkach do heurystyki. Zapisujemy tu każdą unikalną trasę odkrytą przez Dijkstrę.
odkryte_sciezki = {t: [] for t in towary}

#=============================================================================
# 3. GŁÓWNA PĘTLA ALGORYTMU (RELAKSACJA LAGRANGE'A)
#=============================================================================
for q in range(1, maks_iteracji + 1):
    
    # Obliczamy rozmiar kroku (theta). 
    # [ZMIANA WOBEC WERSJI PODSTAWOWEJ]: Zmieniono z szybko malejącego (1.0/q) na wolniej malejący krok (100 / q). Pozwala to na drastyczne podbicie kar powyżej poziomu kosztów 500.
    theta_q = 100 / q
    
    sciezki_iteracji = {}
    przeplyw_luki_iteracji = {(i, j): 0 for (i, j) in luki}
    
    # -------------------------------------------------------------------------
    # KROK A: ROZWIĄZYWANIE PODPROBLEMÓW (Najkrótsze ścieżki)
    # -------------------------------------------------------------------------
    for t in towary:
        # przygotowanie wag w grafie
        for (i, j) in luki:
            koszt_bazowy = koszty.get((t, i, j), float('inf'))
            G[i][j]['weight'] = max(0.0, koszt_bazowy + w_mnozniki[(i, j)])
            
        zrodlo = popyty[t]['zrodlo']
        ujscie = popyty[t]['ujscie']
        ilosc = popyty[t]['ilosc']
        
        # wywolanie algorytmu dijkstry z biblioteki networkx
        trasa_wezly = nx.shortest_path(G, source=zrodlo, target=ujscie, weight='weight')
        
        # lista wezlow na liste krawędzi
        trasa = [(trasa_wezly[m], trasa_wezly[m+1]) for m in range(len(trasa_wezly)-1)]
        sciezki_iteracji[t] = trasa
        
        # zapisanie nowej sciezki do bazy
        if trasa not in odkryte_sciezki[t]:
            odkryte_sciezki[t].append(trasa)
        
        # przepuszczenie towaru po trasie
        for luk in trasa:
            przeplyw_luki_iteracji[luk] += ilosc

    # -------------------------------------------------------------------------
    # KROK B: HEURYSTYKA NAPRAWCZA (Dopasowanie do ograniczeń pojemności)
    # [ZMIANA WOBEC WERSJI PODSTAWOWEJ]: Cały ten blok jest nowy. Zamiast akceptować rozwiązanie z naruszeniami, próbujemy ręcznie "upchać" towar na odkrytych dotąd ścieżkach, jednostka po jednostce.
    # -------------------------------------------------------------------------
    biezacy_przeplyw_luki = {(i, j): 0 for (i, j) in luki}
    lokalny_przeplyw_szczegolowy = {t: {(i, j): 0 for (i, j) in luki} for t in towary}
    popyt_zaspokojony = {t: 0 for t in towary}
    koszt_fizyczny_iteracji = 0
    
    for t in towary:
        sciezki_z_kosztem = []
        for trasa_z_bazy in odkryte_sciezki[t]:
            c_bazowy = sum(koszty[(t, trasa_z_bazy[m][0], trasa_z_bazy[m][1])] for m in range(len(trasa_z_bazy)))
            sciezki_z_kosztem.append((c_bazowy, trasa_z_bazy))
            
        sciezki_z_kosztem.sort(key=lambda x: x[0]) 
        
        wolny_popyt = popyty[t]['ilosc']
        
        for c_bazowy, trasa_z_bazy in sciezki_z_kosztem:
            if wolny_popyt == 0:
                break
                
            mozliwa_alokacja = wolny_popyt
            for luk in trasa_z_bazy:
                # sprawdzanie czy na luku jest miejsce
                dostepne_miejsce = przepustowosci[luk] - biezacy_przeplyw_luki[luk]
                if dostepne_miejsce < mozliwa_alokacja:
                    mozliwa_alokacja = dostepne_miejsce
            
            if mozliwa_alokacja > 0:
                # jesli jest miejsce, alokujemy towar na tej trasie
                for luk in trasa_z_bazy:
                    biezacy_przeplyw_luki[luk] += mozliwa_alokacja
                    lokalny_przeplyw_szczegolowy[t][luk] += mozliwa_alokacja
                
                koszt_fizyczny_iteracji += c_bazowy * mozliwa_alokacja
                popyt_zaspokojony[t] += mozliwa_alokacja
                wolny_popyt -= mozliwa_alokacja
                
    # zapis jesli nie przekracza przepustowosci i jest lepsze od dotychczasowego
    if all(popyt_zaspokojony[t] == popyty[t]['ilosc'] for t in towary):
        if koszt_fizyczny_iteracji < najlepszy_koszt_dopuszczalny:
            najlepszy_koszt_dopuszczalny = koszt_fizyczny_iteracji
            najlepsze_przeplywy_aktywnie = {t: {l: lokalny_przeplyw_szczegolowy[t][l] for l in luki} for t in towary}

    # -------------------------------------------------------------------------
    # KROK C: AKTUALIZACJA MNOŻNIKÓW (Karanie przeciążonych łuków)
    # -------------------------------------------------------------------------
    for (i, j) in luki:
        subgradient = przeplyw_luki_iteracji[(i, j)] - przepustowosci[(i, j)]
        w_mnozniki[(i, j)] = max(0.0, w_mnozniki[(i, j)] + theta_q * subgradient)

#=============================================================================
# 4. WYPISANIE WYNIKÓW 
#=============================================================================
# [ZMIANA WOBEC WERSJI PODSTAWOWEJ]: Ponieważ heurystyka (Krok B) od razu podliczyła legalny koszt rozdzielonego ruchu, tu po prostu go wypisujemy. Wersja podstawowa musiała tu na nowo przeliczać koszt z uwzględnieniem jednego, niezależnego zapotrzebowania.
print(f"Koszt całkowity: {najlepszy_koszt_dopuszczalny:.1f}")

print("\n--- Wybrane trasy (przepływy niezerowe) ---")
for t in towary:
    print(f"\nTowar {t}:")
    przeplyw_znaleziony = False
    for (i, j) in luki:
        val = najlepsze_przeplywy_aktywnie[t][(i, j)]
        if val > 0:
            print(f"  Łuk ({i} -> {j}): wysłano {int(val)} jednostek")
            przeplyw_znaleziony = True
    
    if not przeplyw_znaleziony:
        print("  Brak przepływu dla tego towaru.")