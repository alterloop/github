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
