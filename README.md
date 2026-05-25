# Registro GitHub Italia

Registro pubblico delle organizzazioni italiane presenti su GitHub.

L'obiettivo e' mantenere un indice semplice, verificabile e riusabile da persone, script e pagine statiche.

## Consultazione

Il sito statico e' pubblicato con GitHub Pages usando `docs/` come site root.

- Home: `docs/index.html`
- Open Data: `docs/open-data/index.html`
- Trending: `docs/trending/index.html`
- Dati pubblici per il sito: `docs/data/`

In locale:

```bash
make serve
```

Il server espone direttamente la cartella `docs/`.

## Dati

- `data/organizations.json`: formato canonico dell'ultima fotografia.
- `data/organizations.csv`: esportazione tabellare dell'ultima fotografia.
- `data/trending.json`: classifica trending corrente.
- `data/trending.csv`: esportazione tabellare della classifica.
- `data/YYYY/MM/DD/`: snapshot storici giornalieri.
- `docs/data/`: copia pubblicabile via GitHub Pages.

## Campi

- `login`: nome dell'account su GitHub.
- `name`: nome pubblico mostrato da GitHub.
- `github_url`: URL dell'account.
- `account_type`: `Organization` o `User`.
- `website`: sito ufficiale collegato.
- `location`: localita' dichiarata su GitHub.
- `sector`: classificazione sintetica, ad esempio `PA`, `PMI`, `Ricerca`, `Civic tech`, `N/D`.
- `verified`: `true` se GitHub mostra l'organizzazione come verificata.
- `description`: descrizione breve.
- `followers`: numero follower.
- `public_repos`: numero repository pubbliche.
- `total_stargazers`: somma delle stelle su tutte le repository pubbliche.
- `source_url`: fonte usata per la verifica.
- `last_checked`: data di ultimo controllo in formato `YYYY-MM-DD`.

## Criteri di inclusione

Sono incluse organizzazioni GitHub che rappresentano enti, aziende, fondazioni, comunita' o progetti italiani, oppure organizzazioni con sede o attivita' pubblica rilevante in Italia.

Per motivi storici alcuni soggetti usano account GitHub di tipo utente invece di una pagina organizzazione. Questi account vengono inclusi se elencati in `data/watchusers.txt` e sono distinguibili con `account_type: User`.

Ogni record deve avere almeno:

- login GitHub;
- URL GitHub;
- nome leggibile;
- settore;
- fonte verificabile.

## Watchlist e ignorelist

`data/watchorgs.txt` contiene organizzazioni da processare sempre, anche quando non rientrano nella query GitHub.

`data/watchusers.txt` contiene account utente che rappresentano organizzazioni storiche. Vengono processati con gli endpoint `/users/{login}` e `/users/{login}/repos`.

`data/ignoreorgs.txt` contiene login da escludere sempre dai dati e dalle classifiche. La ignorelist ha precedenza sulla query, su `watchorgs.txt`, su `watchusers.txt` e sugli snapshot precedenti.

I file accettano un login per riga, righe vuote, commenti con `#` e URL GitHub completi.

## Autopopolamento

Il registro puo' essere aggiornato automaticamente con:

```bash
make populate
```

Il target usa `scripts/populate.py`, interroga GitHub Search API con la query predefinita:

```text
location:Italy type:org followers:>50
```

Variabili utili:

```bash
make populate QUERY='location:Italy type:org followers:>100' MAX_ORGS=200
make populate SNAPSHOT_DATE=2026-05-25
make populate WATCH_ORGS_FILE=data/watchorgs.txt WATCH_USERS_FILE=data/watchusers.txt
```

Se presenti, `GITHUB_TOKEN` o `GH_TOKEN` vengono usati per aumentare i limiti API.

Ogni esecuzione crea una fotografia in:

```text
data/YYYY/MM/DD/
```

con:

- `organizations.json`
- `organizations.csv`
- `metadata.json`

I file `data/organizations.*` e `docs/data/organizations.*` rappresentano sempre l'ultima fotografia disponibile.

## Trending

La classifica viene generata con:

```bash
make trending
```

Il risultato viene scritto in `data/trending.json`, `data/trending.csv`, `docs/data/trending.json`, `docs/data/trending.csv` e nello snapshot giornaliero `data/YYYY/MM/DD/`.

Lo score combina crescita stimata a 30 giorni di follower, repository e stelle totali.

Le baseline a 30 giorni usano interpolazione lineare tra le letture disponibili. Se non esiste una lettura piu vecchia della finestra richiesta, il valore piu vecchio disponibile viene considerato costante andando indietro nel tempo.

## Automazione GitHub Actions

- `.github/workflows/populate.yml`: esegue `make populate` ogni notte, committa e pusha solo se i dati cambiano.
- `.github/workflows/tranding.yml`: esegue `make trending` ogni notte, committa e pusha solo se la classifica cambia.

## Aggiornare manualmente

1. Aggiornare watchlist, ignorelist o dati sorgente.
2. Eseguire `make populate`.
3. Eseguire `make trending`.
4. Verificare il sito con `make serve`.
5. Committare dati, snapshot e pagine aggiornate.

## Segnala una organizzazione

Vuoi aggiungere la tua organizzazione a questo dataset? Apri una issue nel repository indicando:

- login GitHub dell'organizzazione o account utente storico;
- nome pubblico dell'organizzazione;
- sito ufficiale, se disponibile;
- settore suggerito;
- motivo per cui dovrebbe essere inclusa nel registro.

Apri una nuova segnalazione da qui: https://github.com/alterloop/github/issues/new

## Repository

Struttura principale:

- `docs/`: sito GitHub Pages.
- `docs/data/`: dataset pubblicati dal sito.
- `data/`: dataset canonici, snapshot e file di controllo.
- `scripts/populate.py`: raccolta e arricchimento dati da GitHub.
- `scripts/trending.py`: calcolo classifica trending.
- `Makefile`: comandi locali.
- `.github/workflows/`: automazioni schedulate.

## Licenza

Il progetto e' distribuito con licenza MIT. Vedi `LICENSE`.

I dati derivano da informazioni pubbliche esposte da GitHub e dai profili collegati. Prima di riutilizzarli in contesti critici, verificare sempre la fonte indicata in `source_url`.

## Note

Il registro non e' un elenco ufficiale di organizzazioni italiane su GitHub. E' un dataset aperto e mantenuto in modo incrementale.

Le metriche GitHub possono cambiare nel tempo e dipendono dai limiti e dalla disponibilita' delle API GitHub al momento dello snapshot.
