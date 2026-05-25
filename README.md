# Registro GitHub Italia

Registro pubblico delle organizzazioni italiane presenti su GitHub.

L'obiettivo e' mantenere un indice semplice, verificabile e riusabile da persone, script e pagine statiche.

## Dati

- `data/organizations.json`: formato canonico.
- `data/organizations.csv`: esportazione tabellare.
- `docs/index.html`: interfaccia statica per consultare il registro.

## Campi

- `login`: nome dell'organizzazione su GitHub.
- `name`: nome pubblico mostrato da GitHub.
- `github_url`: URL dell'organizzazione.
- `website`: sito ufficiale collegato.
- `location`: localita' dichiarata su GitHub.
- `sector`: classificazione sintetica.
- `verified`: `true` se GitHub mostra l'organizzazione come verificata.
- `description`: descrizione breve.
- `source_url`: fonte usata per la verifica.
- `last_checked`: data di ultimo controllo in formato `YYYY-MM-DD`.
- `total_stargazers`: somma delle stelle su tutte le repository pubbliche dell'organizzazione.

## Criteri di inclusione

Sono incluse organizzazioni GitHub che rappresentano enti, aziende, fondazioni, comunita' o progetti italiani, oppure organizzazioni con sede o attivita' pubblica rilevante in Italia.

Ogni record deve avere almeno:

- login GitHub;
- URL GitHub;
- nome leggibile;
- settore;
- fonte verificabile.

## Aggiornare il registro

1. Aggiungere o modificare il record in `data/organizations.json`.
2. Riflettere la stessa modifica in `data/organizations.csv`.
3. Aggiornare `last_checked`.
4. Verificare che la pagina in `docs/index.html` mostri correttamente i dati.

## Autopopolamento

Il registro puo' essere aggiornato automaticamente con:

```bash
make populate
```

Il target usa `scripts/populate.py`, interroga GitHub Search API con la query predefinita:

```text
location:Italy type:org followers:>231
```

Variabili utili:

```bash
make populate QUERY='location:Italy type:org followers:>100' MAX_ORGS=200
make populate SNAPSHOT_DATE=2026-05-25
```

Se presenti, `GITHUB_TOKEN` o `GH_TOKEN` vengono usati per aumentare i limiti API.

### Organizzazioni ignorate

`data/ignoreorgs.txt` contiene i login GitHub da escludere sempre dai dati e dalle classifiche. La ignorelist ha precedenza sulla watchlist, sulla query GitHub e sugli snapshot precedenti.

### Organizzazioni sempre monitorate

`data/watchorgs.txt` contiene i login GitHub delle organizzazioni da processare sempre, anche quando non rientrano nella query di popolamento. Il file accetta una organizzazione per riga, righe vuote, commenti con `#` e URL GitHub completi.

Questo file e' parte del contratto dati del progetto: anche gli script futuri di scoring o trending devono leggerlo per includere sempre le organizzazioni monitorate manualmente.

Per usare una watchlist diversa:

```bash
make populate WATCH_ORGS_FILE=data/watchorgs.txt
```

Ogni esecuzione crea una fotografia in:

```text
data/YYYY/MM/DD/
```

con:

- `organizations.json`
- `organizations.csv`
- `metadata.json`

I file `data/organizations.json` e `data/organizations.csv` rappresentano sempre l'ultima fotografia disponibile. Questo permette di calcolare trend confrontando snapshot di date diverse, ad esempio follower, repository pubblici e variazioni di profilo.

## Automazione GitHub Actions

Il workflow `.github/workflows/populate.yml` esegue `make populate` ogni notte, committa le modifiche in `data/` solo se lo snapshot cambia e pusha sul branch corrente.

## Trending

La classifica viene generata con:

```bash
make trending
```

Il risultato viene scritto in `data/trending.json`, `data/trending.csv` e nello snapshot giornaliero `data/YYYY/MM/DD/`. Lo score combina crescita stimata a 30 giorni di follower, repository e stelle totali, piu base audience, base repository e verifica.

Le baseline a 30 giorni usano interpolazione lineare tra le letture disponibili. Se non esiste una lettura piu vecchia della finestra richiesta, il valore piu vecchio disponibile viene considerato costante andando indietro nel tempo.

Il workflow `.github/workflows/tranding.yml` aggiorna la classifica ogni notte e committa solo se cambia.
