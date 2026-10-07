# Ankkalinnan esimerkkitapaukset

Organisaatio: **Ankkalinna Identity Lab Oy**. Kaikki tiedot ovat kuvitteellisia.
Esimerkeissä käytetään arviointipäivää **7.10.2026**, jotta päivämäärärajojen tulokset pysyvät toistettavina.

## Koko organisaation demo

Käynnistä repon juuresta:

```powershell
python -m access_review.web --snapshot access_review/demo_data/ankkalinna_organization.json
```

Avaa `http://127.0.0.1:8000`. Syötä alla oleva työntekijätunnus ja esihenkilötunnus.
Nykyinen käyttöliittymä avautuu Akun tiedoilla; vaihda tunnukset taulukon mukaan.
Tämä on synteettinen esihenkilösuhteen tarkistus, ei oikea kirjautuminen.

| Työntekijä | Tunnus | Esihenkilötunnus | Tehtävä |
| --- | --- | --- | --- |
| Aku Ankka | `aku.ankka` | `roope.ankka` | HR Specialist |
| Mikki Hiiri | `mikki.hiiri` | `roope.ankka` | Security Analyst |
| Taavi Ankka | `taavi.ankka` | `roope.ankka` | Research Specialist |
| Hansu Hanhi | `hansu.hanhi` | `mummo.ankka` | Seasonal Farm Assistant |
| Iines Ankka | `iines.ankka` | `roope.ankka` | HR Specialist |
| Minni Hiiri | `minni.hiiri` | `roope.ankka` | Application Specialist |
| Hannu Hanhi | `hannu.hanhi` | `roope.ankka` | Sales Specialist |
| Pelle Peloton | `pelle.peloton` | `roope.ankka` | Engineer |
| Leenu Ankka | `leenu.ankka` | `roope.ankka` | Communications Specialist |
| Tupu Ankka | `tupu.ankka` | `roope.ankka` | Trainee |
| Hupu Ankka | `hupu.ankka` | `roope.ankka` | Project Assistant |
| Lupu Ankka | `lupu.ankka` | `roope.ankka` | Project Specialist |

Roope johtaa pääosaa esimerkkitiimeistä. Hansun esihenkilö on Mummo Ankka.
Roope ja Mummo toimivat tässä esihenkilöidentiteetteinä, eivät erillisinä tarkasteltavina työntekijätileinä.

## 22 itsenäistä hyväksymistapausta

Jokaisella tapauksella on oma JSON-snapshot ja käsin määritelty odotettu tulos
tiedostossa `scenarios/cases.json`. Nämä eivät ole saman työntekijän samanaikaisia
tiloja tai todistettua muutoshistoriaa. Koko organisaation demo yhdistää vain yhden
perustilanteen kustakin työntekijästä; ristiriitaiset ja virheelliset variantit ovat erillisiä.

| Tapaus / tiedosto | Tarkoitus | Odotettu tulos |
| --- | --- | --- |
| [mikki-privileged](mikki-privileged.json) | Mikki: perusteltukin ylläpito-oikeus tarkistetaan | 2 oikeutta, 1 tarkistettavaa, 0 ehdotusta; tilin tila `active`. |
| [taavi-new-starter](taavi-new-starter.json) | Taavi: uuden työntekijän dokumentoitu roolipohja | 0 oikeutta, 0 tarkistettavaa, 1 ehdotusta; tilin tila `active`. |
| [hansu-seasonal](hansu-seasonal.json) | Hansu: kausityön tunnus vanhenee seitsemässä päivässä | 1 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `expiring_soon`. |
| [iines-contract-extension](iines-contract-extension.json) | Iines: jatkettu sopimus mutta vanha tunnuksen päättymispäivä | 1 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `expiring_soon`. |
| [minni-inherited](minni-inherited.json) | Minni: peritty jäsenyys näkyy perittynä | 1 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `active`. |
| [hannu-legacy-finance](hannu-legacy-finance.json) | Hannu: myyntiin siirtyneen vanha talousoikeus | 1 oikeutta, 1 tarkistettavaa, 1 ehdotusta; tilin tila `active`. |
| [pelle-undocumented](pelle-undocumented.json) | Pelle: kokeiluryhmän käyttötarkoitus puuttuu | 1 oikeutta, 1 tarkistettavaa, 0 ehdotusta; tilin tila `active`. |
| [leenu-mail-and-distribution](leenu-mail-and-distribution.json) | Leenu: jaettu postilaatikko ja jakeluryhmä | 2 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `active`. |
| [tupu-organization-wide](tupu-organization-wide.json) | Tupu: organisaation yhteinen oikeus erottuu | 1 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `active`. |
| [hupu-expired](hupu-expired.json) | Hupu: päättynyt työsuhde ja vanhentunut tunnus | 1 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `expired`. |
| [lupu-dormant](lupu-dormant.json) | Lupu: lähdetiedossa käyttämättömäksi merkitty oikeus | 1 oikeutta, 1 tarkistettavaa, 0 ehdotusta; tilin tila `active`. |
| [mikki-manager-conflict](mikki-manager-conflict.json) | Mikki: AD ja Entra kertovat eri esihenkilön | Pääsy estetään, raporttia ei palauteta. |
| [taavi-manager-missing](taavi-manager-missing.json) | Taavi: Entran esihenkilötieto puuttuu | Pääsy estetään, raporttia ei palauteta. |
| [hansu-wrong-manager](hansu-wrong-manager.json) | Hansu: Roope ei ole Mummon työntekijän esihenkilö | Pääsy estetään, raporttia ei palauteta. |
| [minni-self-review](minni-self-review.json) | Minni: omien oikeuksien esihenkilötarkistus estetään | Pääsy estetään, raporttia ei palauteta. |
| [taavi-no-expiry](taavi-no-expiry.json) | Taavi: päättymispäivää ei ole asetettu | 0 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `no_expiry_configured`. |
| [hansu-expiry-today](hansu-expiry-today.json) | Hansu: päättymisen raja-arvo today | 0 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `expiring_soon`. |
| [hansu-expiry-90-days](hansu-expiry-90-days.json) | Hansu: päättymisen raja-arvo 90-days | 0 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `expiring_soon`. |
| [hansu-expiry-91-days](hansu-expiry-91-days.json) | Hansu: päättymisen raja-arvo 91-days | 0 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `active`. |
| [pelle-source-name-collision](pelle-source-name-collision.json) | Pelle: sama nimi AD:ssa ei tarkoita Entra-oikeutta | 1 oikeutta, 0 tarkistettavaa, 1 ehdotusta; tilin tila `active`. |
| [taavi-already-member](taavi-already-member.json) | Taavi: olemassa olevaa oikeutta ei ehdoteta uudestaan | 1 oikeutta, 0 tarkistettavaa, 0 ehdotusta; tilin tila `active`. |
| [mikki-duplicate-identity](mikki-duplicate-identity.json) | Mikki: monistunut käyttäjätunnus keskeyttää analyysin | Analyysi keskeytyy virheeseen. |

## Yksittäisen tilanteen avaaminen

Esimerkiksi Hansun kausityö:

```powershell
python -m access_review.web --snapshot scenarios/hansu-seasonal.json
```

Työntekijä: `hansu.hanhi`. Esihenkilö: `mummo.ankka`. Päivä: `2026-10-07`.
Roope-tunnuksella tämän työntekijän tarkastelu kuuluu estää.

Komentoriviltä sama tilanne:

```powershell
python -m access_review scenarios/hansu-seasonal.json --user hansu.hanhi --manager mummo.ankka --as-of 2026-10-07
```

## Mitä testataan ja mitä ei

- Työntekijän omat jäsenyydet eivät sekoitu muiden työntekijöiden jäsenyyksiin.
- Suora ja peritty jäsenyys erotellaan; perittyä oikeutta ei tässä poisteta.
- Sama ryhmänimi AD:ssa ja Entrassa ei tarkoita samaa oikeutta.
- Päättymisen rajat: tänään, seitsemän päivän, 90 päivän ja 91 päivän päästä sekä jo päättynyt tili.
- Sopimuksen jatko tunnistetaan, kun sopimuksen päättymispäivä on tunnuksen päivää myöhempi.
- Privileged- ja dormant-merkinnät ovat lähdedatan väitteitä; demo ei tutki lokitietoja niiden todentamiseksi.
- Postilaatikot ja jakeluryhmät näkyvät resurssityyppeinä. Full Access-, Send As- ja Send on Behalf -erottelua ei vielä mallinneta.
- Tilin vanhentuminen ei vielä ole koko lähtöprosessin tarkastus: istuntoja, lisenssejä tai käytön estoa ei käsitellä.
- Osastonvaihdon ristiriita on tarkistuspyyntö, ei automaattinen todiste tarpeettomasta oikeudesta.
- Keräysaika, lähteiden täydellisyys, hyväksytyt poikkeukset ja todelliset integraatiot ovat jatkokehitystä.

## Testit ja AI-arviointi

```powershell
python -m unittest discover -s tests -v
python -m access_review.evaluate
```

22 tapausta testataan erikseen. Lisäksi yhdistelmädatasta tarkistetaan kaikkien 12
työntekijän oikeuksien erillisyys ja Hansun esihenkilörajaus.
Viisi aiempaa AI-järjestyksen arviointitapausta säilyvät kansiossa `evaluation/`.
Nämä 22 uutta tapausta testaavat toiminnallisuutta; niitä ei esitetä mitattuna AI-laatuna.

**Validointi:** 61 testiä läpäisty. Oikean mallin arviointi ja selainulkoasun tarkistus ovat edelleen avoinna.
