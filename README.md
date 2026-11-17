# Plant Chamber Web App

## "Upgrades, People, Upgrades"
![upgrades](./readme_files/Upgrades,_People,_Upgrades.jpg)

### ./services/rpi_service.py

Zastąpiłem `/bump` endpointem `/health`, ponieważ chciałbym wprowadzić by ten plik automatycznie uruchamiał się na malinie po tym jak otrzyma zasilanie. W tym celu napiszę jeszcze skrypt, by w przypadku, gdzie malina posiadała by starszą wersje dostanie jej update i ponownie się uruchomi. Wersja będzie ustawiana bezpośrednio w pliku `rpi_service.py`

Gdzieś wyczytałem, że malina może sobie przełączać porty, więc dałem by próbował się połączyć po 3 najbardziej możliwych. Jeśli u nas to nie wystepuje, usunę tę część.

Dodatkowo, może się zdażyć, że na raz będzie kilka zapytań do maliny, a potem do arduino, więc żeby się nie zadławił wstawiłem ograniczenie, by się dane nie mieszały i nie traciły. Kolejne dodatkowo, bo chyba to dziś z Danielem zauważyliśmy (17.11.26), że światełko białe nałożyło się z ?czerwonym?, więc dla pewności, że po wykonaniu zdjęcia nawet jeśli coś się wywali po drodzę, to białe światło i tak się wyłączy.

### ./data

Zmieniłem nazwe bazy danych ponieważ zawiera stare dane i tabele, której się juz nie wykorzystuję. Żeby nie usuwać archiwalnych danych, niech se będzie i nowa utworzy się przy uruchomieniu.

### ./app/database/connection.py ; app/database/models.py 

Rozdzieliłem poprzednie `database.py` na dwa pliczki. Myślę, że będzie lepiej dla oczu jeśli bedzie taka podziałka.

### ./app/logic/raspberry_pi/raspberry.py

Zmieniłem by co 30 sekund (?) wywoływał `/health`, czyli będzie wiadomo czy malina nadaje i czy arduino jest podłączone. Jest to wykonane dla instancji, więc potem na Dashboardzie zrobie sekcje, gdzie będą ich statusy.

Oznaczyłem, że `if __name__ == "__main__"` jest tylko i wyłącznie dla testów.

Poukładałem importy według wytycznych PEP 8 (mam taką nadzieje, ze niczego nie spieprzyłem)

### ./app/logic/chamber/chamber.py

Poukładałem importy tak jak wyżej. W `from_config_params()` w ChamberConfig zmieniłem zwracanie configu, ze względu na inne zmiany. Dodałem `rpi_address` do `set()` w ChamberConfig. Po pousuwaniu paru komponentów AI wskazało bym dodał `__enter__` i `__exit__`, ponoć inaczej się wysypie. Przetestuje.

### ./app/logic/shared.py

Poukładane importy!

### ./app/frontend

Poza przekopiowaniem za dużo tam nie zrobiłem, jeszcze...

### ./app/config.py

Zawiera konfiguracje biblioteki `logging`, stałe ścieżki oraz wartości typu `CONSTANT`

### ./app/main.py

Jeszcze nie skończony, ale będzie wystarczyło wpisać `python app/main.py` by uruchomić całą aplikacje.

### PyArrow

Sorki Daniel, na razie nie miałem chwili żeby przy tym bardziej pokombinować. Chciałem skupić się na postawieniu systemu na czymkolwiek co działa. Linux chwile poczeka

### .gitignore

Zauważyłem, że plik świeci pustkami, więc skleiłem standardową zawartości (template) dla języka Python ze [strony GitHub'a](https://github.com/github/gitignore/blob/main/Python.gitignore)
