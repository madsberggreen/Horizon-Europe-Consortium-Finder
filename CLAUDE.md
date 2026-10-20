# CLAUDE.md — Horizon Europe Consortium Finder

## Hvad projektet er

En app, der hjælper forskere med at finde og komme ind i et Horizon Europe-konsortium.

Ejer: Mads Lykke Berggreen (GitHub: madsberggreen). Repository: https://github.com/madsberggreen/Horizon-Europe-Consortium-Finder (offentligt).

## Status

Første version deles som Claude-plugin (`plugins/research-funding`, v2.1.0), som kolleger installerer fra dette repository (`.claude-plugin/marketplace.json`). Senere overvejer Mads, om det skal blive en egentlig webapp. En færdig Lovable-byggeplan ligger i Cowork-projektet `OneDrive - ViaUC\Dokumenter\Claude\Projects\Horizon Europe Automated\Lovable-Import`.

Pluginet kommer fra `plugin-src/research-funding` i samme Cowork-projekt, men **dette repository er nu den gældende version**. Ret her, ikke i Cowork-kopien.

## Data — vigtigt

- Forskerdata (CV'er, profiler, rapporter i `researchers/`) er personoplysninger og må aldrig commites. `.gitignore` blokerer `researchers/`, `themes/`, `cordis-data/` og PDF'er.
- CORDIS-data hentes automatisk af `skills/cordis-analysis/scripts/download_cordis.py` fra https://cordis.europa.eu/data/ (ved første brug og når de er over 30 dage gamle). Læg aldrig CORDIS-filer i repositoriet.
- Når version ændres, opdater både `plugins/research-funding/.claude-plugin/plugin.json` og `.claude-plugin/marketplace.json` samt ændringslisten i plugin-README'en.

## Arbejdsregler for dette projekt

- Mads er ikke programmør. Forklar ændringer i almindeligt sprog og fortæl præcist, hvad han skal klikke på eller køre.
- Vælg den enkleste løsning, der virker. En enkelt HTML-fil er bedre end et framework.
- Commit med en kort, forståelig besked efter hver færdig ændring. Push til GitHub først, når ændringen er testet.
- Opdater afsnittet "Status" her, når projektet tager form.
