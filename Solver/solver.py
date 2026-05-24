import pulp

'''
#1. Dane wejściowe
# NIE ZMIENIAC DANYCH - JUZ DALEM GRAF DO SPRAWOZDANIA
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

# Bilans węzłów: >0 podaż (źródło), <0 popyt (ujście), 0 tranzyt
bilanse = {
    'A': {1: 10, 2: 0, 3: 0, 4: -10, 5: 0, 6: 0},
    'B': {1: 5, 2: 0, 3: 0, 4: -5, 5: 0, 6: 0}
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

# Bilans węzłów: >0 podaż (źródło), <0 popyt (ujście), 0 tranzyt
bilanse = {
    'A': {1: 10, 2: 0, 3: 0, 4: -10, 5: 0, 6: 0},
    'B': {1: 5, 2: 0, 3: 0, 4: -5, 5: 0, 6: 0}
}


'''2. Inicjalizacja modelu'''
#LpMinimize - chcemy minimalizować koszt
problem = pulp.LpProblem("Wieloskladnikowy_Przeplyw", pulp.LpMinimize)

'''3. Zmienne decyzyjne'''
# x[towar, i, j] - ile jednostek danego towaru płynie konkretnym łukiem
# cat=pulp.LpInteger sprawia, że zmienne są całkowite (Etap 1: Indivisible goods)
x = pulp.LpVariable.dicts("przeplyw", 
                         ((t, i, j) for t in towary for (i, j) in luki), 
                         lowBound=0, 
                         cat=pulp.LpInteger)

'''4. Funkcja celu'''
# Sumujemy (koszt * ilość) dla wszystkich towarów i wszystkich łuków
problem += pulp.lpSum(koszty[t, i, j] * x[t, i, j] for t in towary for (i, j) in luki)

'''5. Ograniczenia przepustowosci'''
# Suma wszystkich towarów na danym łuku nie może przekroczyć jego limitu
for (i, j) in luki:
    problem += pulp.lpSum(x[t, i, j] for t in towary) <= przepustowosci[i, j], f"Limit_luk_{i}_{j}"

'''6. Ograniczenia bilansu'''
# Dla każdego towaru i każdego węzła: wypływ - wpływ = bilans
for t in towary:
    for n in wezly:
        wyplyw = pulp.lpSum(x[t, i, j] for (i, j) in luki if i == n)
        wplyw = pulp.lpSum(x[t, i, j] for (i, j) in luki if j == n)
        problem += (wyplyw - wplyw == bilanse[t][n]), f"Bilans_{t}_wezel_{n}"

'''7. Rozwiazanie problemu'''
problem.solve(pulp.PULP_CBC_CMD(msg=0))

'''8. Wyniki'''
print(f"Koszt całkowity: {pulp.value(problem.objective)}")

print("\n--- Wybrane trasy (przepływy niezerowe) ---")
# Interujemy po wszystkich towarach i łukach
for t in towary:
    print(f"\nTowar {t}:")
    przeplyw_znaleziony = False
    for (i, j) in luki:
        # Pobieramy wartość zmiennej x dla danego towaru i łuku
        val = pulp.value(x[t, i, j])
        if val > 0:
            print(f"  Łuk ({i} -> {j}): wysłano {int(val)} jednostek")
            przeplyw_znaleziony = True
    
    if not przeplyw_znaleziony:
        print("  Brak przepływu dla tego towaru.")