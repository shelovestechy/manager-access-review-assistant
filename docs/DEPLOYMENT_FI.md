# Käyttöönotto käytännössä: sovellus, Copilot-agentti ja oikeudet

**Tila:** suunnitelma, ei toteutettu tuotantointegraatio.  
**Dokumentaation tarkistuspäivä:** 7.10.2026.  
**Esimerkkiorganisaatio:** Ankkalinna Identity Lab Oy.

## 1. Mikä tämä olisi yrityksessä?

Assistant olisi **kirjautumista edellyttävä, vain tietoja lukeva käyttöoikeuksien tarkastelupalvelu**. Roope Ankka voisi avata Akun raportin, nähdä mistä tiedot tulevat ja valmistella ICT:lle pyynnön. Oikeuksia ei muuteta eikä tikettiä lähetetä automaattisesti.

Nykyinen Python-sovellus on paikallinen demo. Siinä esihenkilön tunnus kirjoitetaan itse ja tiedot tulevat JSON-esimerkeistä. Tämä havainnollistaa tarkistussääntöä, mutta ei todista käyttäjän henkilöllisyyttä.

| Vaihtoehto | Käyttöliittymä | Mitä sen lisäksi tarvitaan? |
| --- | --- | --- |
| Oma verkkosovellus | Raportti, valintaruudut ja pyyntöluonnos selaimessa | Entra-kirjautuminen, suojattu API ja tietolähteiden lukuliitännät |
| Teamsiin tuotu verkkosovellus | Sama raporttinäkymä Teams-välilehdellä | Teamsin tunnistautumisen toteutus ja sama suojattu taustapalvelu |
| Copilot Studio -agentti | Roope kysyy keskustelussa: ”Näytä Akun tarkastettavat oikeudet” | Käyttäjäkohtaisesti tunnistautuva työkalu/custom connector, suojattu API ja samat tietolähteet |
| Power Apps -käyttöliittymä | Low-code-raportti ja lomake | Käyttäjäkohtainen API-yhteys sekä sama tarkistus- ja keräyslogiikka |

**Ehdotettu etenemistapa:** ensin kirjautuva verkkosovellus ja rajattu lukuliitäntä. Copilot Studio voidaan liittää myöhemmin samaan APIin. Näin raportti on käyttökelpoinen myös ilman kielimallia.

Agentti olisi palvelun keskustelupinta. Pelkkä agentin ohjeteksti, tiedostojen lisääminen tietopankkiin tai kehotus ”näytä vain omat alaiset” ei toteuta käyttöoikeusrajausta.

## 2. Esimerkkikulku: Roope tarkastelee Akua

1. Roope kirjautuu organisaation Entra ID -tunnuksella. Yrityksen kirjautumiskäytännöt, kuten MFA ja Conditional Access, koskevat palvelua.
2. Taustapalvelu tunnistaa Roopen vahvistetusta käyttäjäistunnosta/API-tokenista. Lomakkeella tai agentin parametrissa annettua manager-tunnusta ei käytetä henkilöllisyyden todisteena.
3. Palvelu tarkistaa tenantin, sallitun käyttäjän/sovellusroolin ja Akun esihenkilösuhteen. Hybridipilotissa esihenkilön täytyy täsmätä **sekä AD:ssa että Entrassa**, kuten nykyisessä demossa.
4. Vasta hyväksytyn tarkistuksen jälkeen palvelu hakee Akun rajatun oikeusraportin.
5. Raporttiin liitetään lähde, keräysaika ja tiedon kattavuus. Puuttuva Exchange-tieto näkyy puuttuvana, ei väitteenä ”ei postilaatikko-oikeuksia”.
6. Sääntömoottori laskee huomiot. Mahdollinen AI saa vain hyväksytyn raportin tarpeellisen osan.
7. Roope valitsee ehdotetut muutokset. Pyyntöluonnoksen tekeminen tarkistaa oikeuden uudelleen. Roope toimittaa luonnoksen hyväksyttyä kanavaa pitkin ICT:lle.

Entra-objektin ja AD-käyttäjän yhdistämiseen tarvitaan luotettava, organisaation synkronointiin sopiva tunnistekartoitus. Pelkkä sama näyttönimi tai sähköpostiteksti ei riitä. Pilviorganisaatiossa ilman AD:ta dual-source-sääntöä pitäisi muuttaa tietoisesti ja testata erikseen.

## 3. Kolme erilaista oikeutta

| Taso | Kenelle annetaan? | Merkitys |
| --- | --- | --- |
| Palvelun käyttöoikeus | Roopelle ja pilotin muille esihenkilöille | Oikeus avata sovellus/agentti; voidaan rajata sovellusroolilla tai pilotin käyttäjäryhmällä |
| Tietolähteen lukuoikeus | Graph-liitännälle tai erilliselle AD/Exchange-kerääjälle | Tekninen oikeus hakea tietoja |
| Raportin katseluoikeus | Tarkistetaan jokaisella pyynnöllä | Roope saa nähdä vain hyväksytyn esihenkilösuhteen mukaiset raportit |

**API-oikeus ei automaattisesti rajaa tietoa omiin alaisiin.** Esimerkiksi `User.Read.All` on laaja lukuoikeus. Taustapalvelun pitää tehdä oma raporttikohtainen rajaus myös delegoidussa mallissa.

Roopelle ei tarvitse antaa Global Administrator- tai Exchange Administrator -roolia palvelun käyttämistä varten.

## 4. Microsoft Graph: ensimmäisen lukupilotin oikeudet

Alla on ehdotus **kirjautuneen käyttäjän puolesta toimivalle delegoidulle Graph-liitännälle**. Oikeudet myönnetään sovellukselle; niiden hyväksyntä tehdään organisaation ylläpidossa. Tämä on suunnittelupohja, ei kaikille tenanteille valmis oikeuspaketti.

| Tarve | Esimerkkikutsu | Oikeus ja rajaus |
| --- | --- | --- |
| Akun esihenkilö | `GET /users/{aku-id}/manager` | Delegoitu `User.Read.All`. Microsoftin tämänhetkinen manager-endpointin taulukko ei tue application-oikeuksia. |
| Akun suorat ryhmäjäsenyydet | `GET /users/{aku-id}/memberOf` | Delegoitu `User.Read.All`. Kerättävä erikseen, jotta suorat ja välilliset jäsenyydet voidaan erottaa. |
| Akun suorat ja välilliset jäsenyydet | `GET /users/{aku-id}/transitiveMemberOf` | Toisen käyttäjän jäsenyyksien lukuun dokumentoitu `User.Read.All`. Vastaus voi sisältää myös muita directoryObject-tyyppejä. |
| Ryhmien nimet ja tarvittavat perustiedot | `GET /groups/{group-id}?$select=id,displayName,description` | Esimerkiksi read-only `GroupMember.Read.All` on dokumentoitu tuettu oikeus. Tarkista, riittääkö kapeampi lukuscope valittuihin kenttiin. |
| Piilotetut jäsenyydet | Vain erikseen hyväksytyn tarpeen perusteella | `Member.Read.Hidden` voi olla tarpeen. Ei mukaan oletusarvoisesti. |

`User.Read.All` vaatii admin consentin. Muutkin valitut oikeudet ja tenantin consent-käytännöt tarkistetaan ennen pilotointia. Ryhmäobjektien lukeminen voi ilman sopivaa oikeutta palauttaa vain tunnisteen ja tyypin; puuttuvia kenttiä ei saa tulkita täydelliseksi tiedoksi.

Ensimmäisen pilotin suunnittelussa voidaan arvioida **delegoitua `User.Read.All` + tarvittavaa ryhmätietojen lukuscopea**, ei hakemiston kirjoitusoikeuksia. `Directory.Read.All` ei ole oletusratkaisu jokaiseen puuttuvaan kenttään.

Backend voi käyttää **On-Behalf-Of (OBO)** -mallia kutsuakseen Graphia Roopen puolesta. UI/connector hankkii tokenin backendin APIlle; backend hankkii oman Graph-tokeninsa. Graphille tarkoitettua tokenia ei hyväksytä backendin omaksi API-tokeniksi. Käytä tuettua tunnistautumiskirjastoa ja varmista signature, issuer, audience, voimassaolo, tenant, käyttäjä sekä vaadittu scope/rooli.

Graphin ryhmäjäsenyys ei ole täydellinen kuva kaikista Teams-, SharePoint-, sovellus- tai tiedostokohtaisista oikeuksista. Yksityiset/jaetut kanavat, sivustojen yksilölliset oikeudet ja PIM:n eligible-roolit tarvitsevat erillisen suunnittelun. Näitä ei luvata ensimmäiseen pilottiin.

## 5. Paikallinen AD: oma read-only-kerääjä

Microsoft Graph ei lue paikallisen AD DS:n kaikkia attribuutteja. Hybridiversioon tarvitaan sisäverkossa toimiva kerääjä.

| Kerättävä tieto | Toteutuksen lähtökohta |
| --- | --- |
| Esihenkilö | `Get-ADUser`, attribuutti `manager` |
| Tunnuksen vanheneminen | `accountExpires` / moduulin `AccountExpirationDate` |
| Käyttäjätunnisteet ja tehtävätiedot | Vain analyysille hyväksytyt attribuutit |
| Suorat jäsenyydet | `memberOf`, huomioiden että primary group ei sisälly siihen |
| Välilliset jäsenyydet | Erillinen ryhmälaajennus; määriteltävä kattavuus, primary group ja mahdolliset luottosuhteet |

Kerääjälle annetaan lukuoikeudet valittuihin objekteihin ja attribuutteihin. AD:n oletuslukeminen ja paikalliset ACL:t vaihtelevat; oikeudet pitää todentaa labrassa. **Domain Adminia tai käyttäjien/ryhmien muokkausoikeutta ei tarvita tähän suunnitelmaan.**

Kerääjä voisi toimia organisaation Windows-palvelimella hyväksytyllä palveluidentiteetillä, esimerkiksi gMSA:lla ympäristön tukiessa sitä. Se palauttaa vain tarvittavat tiedot suojattuun palveluun. Pilvipalvelulle ei avata suoraa julkista yhteyttä domain controlleriin.

Vanhenemisen erityisarvot ja aikavyöhykkeet testataan ennen käyttöönottoa. Työsopimuksen loppupäivä tarvitsee erillisen hyväksytyn HR-lähteen; AD:n expiry-arvo ei ole työsopimustieto.

## 6. Exchange Online: postilaatikko-oikeudet ja sähköpostitusryhmät

Entran ryhmäraportti ei yksin riitä jaettujen postilaatikoiden oikeuksien inventointiin.

| Tieto | Keräyksen lähtökohta |
| --- | --- |
| Full Access | `Get-EXOMailboxPermission` |
| Send As | `Get-EXORecipientPermission` |
| Send on behalf | Postilaatikon `GrantSendOnBehalfTo`, esimerkiksi `Get-Mailbox` |
| Tavallisen jakeluryhmän jäsenet | `Get-DistributionGroupMember` |
| Dynaamiset jakeluryhmät | Oma keräys ja jäsenyyden voimassaolon/kattavuuden määrittely |

Nämä ovat eri oikeustyyppejä. Niitä ei yhdistetä epämääräiseksi ”postilaatikon käyttö” -kentäksi. Ryhmien kautta tulevat oikeudet, deny-merkinnät ja periytyminen tarvitsevat erillisen käsittelyn. Suora oikeuslista ei vielä todista käyttäjän kaikkia efektiivisiä oikeuksia.

**Ehdotus:** erillinen Exchange Online PowerShell -kerääjä, jolla on app-only-yhteyttä varten `Exchange.ManageAsApp`, admin consent ja hyväksytyt **vain tarvittavat lukukomennot sallivat custom Exchange RBAC -roolit**. Pelkkä API-permission ei anna kaikkia cmdlet-oikeuksia. Organisaation Exchange-ylläpito tarkistaa cmdletit, parametrit ja roolien todellisen vaikutuksen testiympäristössä.

Tämä suunnitelma käyttää Exchange Online PowerShelliä. Uuden Exchange Admin REST API:n scope-nimet ovat eri asia; niitä ei sekoiteta tähän yhteysmalliin. Exchange Application RBAC:n mailbox-data-roolit eivät myöskään ole sama asia kuin PowerShellin hallintakomentojen custom-rooliryhmät.

Collectorille ei anneta kaikkia Exchange Administrator -oikeuksia vain helppouden vuoksi. Kirjoitusscope ei takaa lukudatan rajausta: laajasti lukevan kerääjän tiedot pitää suojata ja raporttipalvelun pitää rajata palautus esihenkilölle. Viestien sisältöön ei tarvita `Mail.Read`- tai `Mail.ReadWrite`-oikeuksia.

## 7. Jos käyttöliittymä olisi Copilot Studio -agentti

Low-code-osuus voisi olla keskustelun rakentaminen Copilot Studiossa ja API-työkalun yhdistäminen custom connectorilla.

Esimerkkityökalu: **GetEmployeeAccessReview(employeeId)**.

- Agentti tunnistautuu Microsoftin käyttäjällä. Myös työkalun yhteys/API-kutsu tunnistautuu loppukäyttäjänä.
- API todentaa kutsujan omasta tokenistaan ja tarkistaa raporttioikeuden. Se ei luota agentin antamaan `requesterId`-parametriin.
- Palautus sisältää vain hyväksytyn työntekijän raportin, lähteet ja keräystilan.
- Agentti voi esittää huomioita ja ohjata raporttinäkymään. Nykyinen AI-rajaus järjestää valmiita havaintoja; vapaa yhteenveto olisi uusi erikseen arvioitava ominaisuus.
- Valittujen muutosten pyyntöluonnos tehdään omalla rajatulla työkalulla, joka tarkistaa kutsujan uudelleen.
- Agentilla ei ole työkaluja ryhmämuutoksiin, tunnusten hallintaan tai tiketin lähettämiseen.

**Agentin kirjautuminen ja työkalun tunnistautuminen ovat eri asioita.** Copilotin `User.ID`-muuttuja tai Teamsissa näkyvä käyttäjän nimi ei yksin ole backendille hyväksyttävä todistus.

Microsoft suosittelee user authentication -yhteyttä työkaluille, kun tietoja pitää rajata käyttäjille. Tekijän henkilökohtaisilla tunnuksilla toimiva yhteys voisi muuten antaa muille tekijän oikeudet. Power Automate -flow ei automaattisesti korjaa tätä: connection- ja run-only-asetukset pitää tarkistaa, ja API tarvitsee edelleen luotettavan käyttäjäkontekstin. Jos valittu kanava/connector ei tue tätä, valitse toinen integraatio tai pysy kirjautuvassa verkkosovelluksessa.

## 8. Käyttöönoton vaiheistus

| Vaihe | Tehtävät | Valmiuden näyttö |
| --- | --- | --- |
| Nykyinen portfolio-demo | Synteettiset tapaukset, esittelyvideo ja rajojen kuvaus | Ei oikeita työntekijätietoja eikä tenant-yhteyttä |
| Kirjautuva labrapilotti | Suojattu web/API, pilotin käyttäjärooli, Entra Graph -lukuliitäntä, AD-kerääjä jos dual-source-sääntö säilytetään | Väärä esihenkilö, väärä tenant, vanhentunut token ja ristiriitainen esihenkilötieto estetään |
| Rajattu yrityspilotti | Omistaja, hyväksytyt oikeudet, lokit, tietojen tuoreus, Exchange-keräys, ylläpitomalli | Puuttuvat tiedot näkyvät; luku toimii ja muokkaus estyy myös teknisillä oikeuksilla |
| Valinnainen agentti | Copilot Studio + käyttäjäkohtainen API-työkalu | Samat raporttirajat pitävät sekä sovelluksessa että agentissa |

Labrapilotin ensimmäinen pieni tavoite voisi olla: **Roope kirjautuu ja näkee Akun Entra-ryhmät; Mummo ei näe Akun raporttia.** Hybridisäännön mukaisessa versiossa myös AD-esihenkilötieto tarkistetaan. Postilaatikot ja AI lisätään vasta tämän toimittua.

## 9. Mitä tuotantopalvelu tarvitsee?

- Nykyisen localhost-demo-serverin tilalle tuotantokelpoinen web/API-palvelu, HTTPS ja hallittu hosting.
- Erilliset dev/test/prod-ympäristöt ja hallitut sovellusidentiteetit; salaisuudet ja sertifikaatit turvalliseen säilytykseen.
- Lokitus siitä, kuka tarkasteli mitä ja milloin sekä miksi pyyntö sallittiin/estettiin. Tokeneita tai tarpeettomia henkilötietoja ei kirjata.
- Keräysaikojen ja tietolähteiden terveydentilan seuranta; päätetty tuoreusraja ja fail-closed esihenkilötiedon puuttuessa.
- Sivutuksen, API-rajoitusten, katkosten ja osittaisten raporttien käsittely.
- Tietojen minimointi ja säilytysajat, käyttöoikeuksien säännöllinen tarkistus sekä nimetty palvelun omistaja.
- Mallin käyttöä varten hyväksytty tietojenkäsittely, arvioitu hyöty, kustannukset ja vaihtoehto ilman mallia.
- Copilot/Power Platform -vaihtoehdossa tarkistetut ympäristö-, DLP-, connector-, kanava- ja lisenssivaatimukset. M365-lisenssin ei oleteta kattavan kaikkia ominaisuuksia.

Tämä dokumentti ei määritä valmista tuotantobudjettia tai takaa lisenssien saatavuutta. Hosting, kerääjät, ylläpito ja mahdollinen Copilot-kapasiteetti arvioidaan organisaation oman ympäristön perusteella.

## 10. Mitä tämä näyttää portfoliossa?

Projektin arvo on käyttäjän tarpeen muuttamisessa selkeäksi palveluksi: tietolähteet, oikeudet, luotettava kutsuja, päätössäännöt ja ihmisen hyväksyntä on erotettu toisistaan. Sama API voi palvella perinteistä käyttöliittymää tai low-code-agenttia.

**Nykyinen toteutus:** paikallinen synteettinen demo, sääntömoottori, raportti, pyyntöluonnos ja valinnainen paikallinen havaintojen AI-järjestys.  
**Tämän dokumentin ehdotus:** kirjautuminen, live-kerääjät, Graph/AD/Exchange-oikeudet, hosting ja Copilot Studio -integraatio. Näitä ei vielä esitetä toteutettuina.

## Microsoft-lähteet

Tarkista endpointin ajantasainen dokumentaatio ja oikeuksien toiminta ennen myöntämistä.

- [Graph: user manager](https://learn.microsoft.com/en-us/graph/api/user-list-manager?view=graph-rest-1.0)
- [Graph: user memberOf](https://learn.microsoft.com/en-us/graph/api/user-list-memberof?view=graph-rest-1.0)
- [Graph: user transitiveMemberOf](https://learn.microsoft.com/en-us/graph/api/user-list-transitivememberof?view=graph-rest-1.0)
- [Graph: group properties](https://learn.microsoft.com/en-us/graph/api/group-get?view=graph-rest-1.0)
- [Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
- [OAuth On-Behalf-Of flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-on-behalf-of-flow)
- [API claims validation](https://learn.microsoft.com/en-us/entra/identity-platform/claims-validation)
- [Get-ADUser](https://learn.microsoft.com/en-us/powershell/module/activedirectory/get-aduser)
- [Exchange Online PowerShell: app-only authentication and custom role groups](https://learn.microsoft.com/en-us/powershell/exchange/app-only-auth-powershell-v2)
- [Get-EXOMailboxPermission](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-exomailboxpermission)
- [Get-EXORecipientPermission](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-exorecipientpermission)
- [Get-Mailbox](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-mailbox)
- [Get-DistributionGroupMember](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-distributiongroupmember)
- [Copilot Studio: agent authentication](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configuration-end-user-authentication)
- [Copilot Studio: tool user authentication](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configure-enduser-authentication)
- [Copilot Studio: maker credential controls](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configure-no-maker-authentication)
- [Copilot Studio: licensing requirements](https://learn.microsoft.com/en-us/microsoft-copilot-studio/requirements-licensing-subscriptions)
