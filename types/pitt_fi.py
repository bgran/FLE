# Progressive Inquiry knowledge types by:
#   Kai Hakkarainen
#   Minna Lakkala
#   Pirita Seitamaa-Hakkarainen
#   Samu Mielonen
#   Teemu Leinonen
#
name='Tutkiva oppiminen'
translated_from='Progressive Inquiry'
language='suomi'
description= \
"""Oppiminen voidaan nähdä tutkimuksena, joka tähtää yksilön ja ryhmän ymmärryksen parantamiseen. Tähän voidaan pyrkiä keskustelemalla avoimesti tutkimushaasteista, teorioista, omista ideoista ja muualta löydetystä tieteellisestä tiedosta. Prosessin tarkoituksena on edetä porrastetusti kohti kehittyneempiä käsityksiä ja haasteellisempia tutkimusongelmia sekä niiden ratkaisuja. Tarkoituksena on kuitenkin aloittaa opiskelijoiden omista ongelmista ja käsityksistä ja kehittää näitä eteenpäin keskustelemalla esitettyjen ajatustyyppien avulla.

Tutkiva oppiminen -ajattelutyypistö auttaa oppijoita jakamaan omat käsisitykset ongelmiksi, teorioiksi, muualta löydetyksi tieteelliseksi tiedoksi, prosessia organisoiviksi kommenteiksi ja yhteenvedoiksi. Näiden keskusteluviestien lukeminen ja kirjoittaminen auttaa opiskelijoita käsittelemään aiheen haasteita ja oppimisprosessia tieteellisen prosessin mukaisesti. Oman ajattelun jäsentäminen, ajatusten tuominen julki itselle ja muille viesteinä ja näiden viestien käsittely nähdään siis prosessin päätavoitteena ja sen tuloksena syntyy kehittyneempi ymmärrys aiheesta.
"""
types=({'id': 'ong',
        'name': 'Tutkimusongelma',
        'starting_phrase':"""Haluaisin selvittää, miksi/miten...
Haluaisin tutkia miksi/miten...""",
        'description':\
"""Tutkimuksen tarkoituksena on ratkoa ongelmia. Oppimisprosessi tähtää
oppijoiden omien ongelmien esittämiseen ja ratkaisuiden löytämiseen näihin.
Ongelman määrittäminen palvelee omien oppimistavoitteiden määrittelyä:
kirjaamalla ongelmaksi sen, mitä et ymmärrä olet määritellyt tavoitteeksi
laajentaa ymmärrystäsi ongelman suuntaan.

Kun ensimmäisiä ongelmia on käsitelty omien teorioiden ja muun tarjolla olevan
tiedon perusteella, ongelmat usen tarkentuvat pienemmiksi ala-ongelmiksi tai
jopa muuttuvat kokonaan.""",
        'checklist':
"""Oletko esittelemässä ongelmia, joista <b>olet itse kiinnostunut</b>?

Oletko selittämässä <b>tutkimustavoitteitasi</b>?

Anna selitykset ongelmaan toisessa viestissä.""",
        'colour': "tt_yellowlt",
        'icon': "ui/images/types/coi/problem.gif",
        },
        {'id': 'teoria',
        'name': 'Oma teoria',
        'starting_phrase': """Minun mielestäni...
Minä luulen, että...""",
        'description':\
"""Oma teoria esitää omat ajatuksesi käsiteltävästä ongelmasta, olivat ne
sitten valmiita tai omasta mielestäsi aukottomia. Omien teorioiden ei
siis tarvitse olla täydellisiä, eikä ole mielekästä pantata niitä muilta,
kunnes ne ovat omasta mielestä virheettömiä.

Ymmärtäminen ja oppiminen jakautuu muiden oppijoiden kanssa, mitä aikaisemmin
ongelmat ja teoriat jaetaan muiden kanssa selkeinä viesteinä. On kuitenkin
tärkeää kiinnittää huomiota, että omat teoriasi kehittyvät oppimisprosesin
aikana ja heijastavat myös muiden ihmisten esittämiä käsityksiä, ongelmia
ja teorioita.""",
         'checklist':
"""Oletko kertomassa <b>omasta ajattelustasi</b> (luulo, hypoteesi, teoria, selitys tai tulkinta)?

<b>Älä viimeistele</b> selitystäsi. Kirjoita kehitellymmät versiot myöhemmin.""",
         'colour': "tt_aqua",
        'icon': "ui/images/types/coi/work_th.gif",
        },
        {'id': 'tieto',
        'name': 'Tieteellinen tieto',
        'starting_phrase': """Olen löytänyt tietoa...""",
        'description':\
"""Tieteellinen tieto edustaa tutkittavan aiheen hyvää tieteellistä
ymmärrystä tai alan yleistä näkemystä. Tieteellisen tiedon avulla
voidaan keskusteluun tuoda uusia asioita, jotka voivat tukea tai
olla ristiriidassa jo esitettyjen teorioiden kanssa.

Tieteellinen tieto on muiden tuottamaa ja tieteellisen
kriteeristön täyttämää tietoa (teorioita, malleja, kuvauksia), joka
täydentää ymmärrystä tutkittavasta aiheesta.

Hyvän käytännön mukaista on liittää Tieteellisen tiedon viestiin
myös käytetty tiedon lähde (lähdeviite).
""",
        'checklist':
"""Oletko kertomassa alan <b>asiantuntijan antamaa tietoa</b>?

<b>Liittyykö selitys</b> lähettämiisi ongelmiin ja selityksiin?

Muista mainita, <b>mistä löysit tiedon</b> (kirja, artikkeli, www-sivusto, tv-ohjelma, luento, keskustelu).""",
         'colour': "tt_orangelt",
        'icon': "ui/images/types/coi/deep_kn.gif",
        },
        {'id': 'org',
        'name': 'Työn organisointi',
        'starting_phrase': """Mielestäni ideamme...
Mielestäni oppimisprosessimme...""",
        'description':\
"""Työn organisointia kuvaavat viestit kertovat käsittelevät omaa
tai ryhmän työskentelyä, eivätkä varsinaisesti käsiteltävää aihetta.
Tarkoituksena on siis arvioida ja edesauttaa ryhmän toiminnan organisointia
siihen suuntaan, että se tukee asetettujen ongelmia ymmärtämistä ja
ratkaisemista syvällisesti ja tehokkaasti.

Organisointiviesti voi käsitellä nykyistä työn etenemisen arviointia,
käytettävää menetelmäkirjoa, tiedon jakamista tai työnjakoa.
""",
        'checklist':
"""Käsitteletkö ryhmäsi <b>työn organisointia</b>?

Oletko ilmaissut <b>mielipiteesi</b> oppimisprosessin etenemisestä?

Oletko <b>jakamassa tehtäviä</b> tai <b>keskustelemassa käytetyistä menetelmistä</b>?""",
         'colour': "tt_purple",
        'icon': "ui/images/types/coi/meta_co.gif",
        },
        {'id': 'yht',
        'name': 'Yhteenveto',
        'starting_phrase': """Olemme oppineet, että...
Pääsimme siihen lopputulokseen, että...""",
        'description':\
"""Yhteenveto tähtää keskustelun keskeisimpien osien tuomiseksi yhteen
niin, että niistä voidaan esittää yhtenäinen kokonaisuus. Tarkoituksena
on käydä läpi ainakin alkuongelma, lopulliset käsitellyt ongelmat,
keskeisimmät teoriat ja lopputulema siitä, mikä aiheen ympärillä on
oleellista.

Yhteenveto voi olla henkilökohtainen tai pyrkiä tuomaan esiin ryhmän
yleistä näkemystä. Yhteenvetoja voi myös olla useita, mikäli alkuperäinen
ongelma on jakautunut useammaksi omaksi alueekseen. Nämä uudet osa-alueet
voivat yhteenvetoineen toimia uusien kurssikotenkstien aloituksina.
""",
        'checklist':
"""Oletko <b>kerrannut kaikki viestit</b> keskustelusta?

Oletko <b>vetämässä yhteen</b> keskustelun osia?

Oletko <b>selittämässä mitä olet oppinut</b> alunperin asetetuista ongelmista?""",
         'colour': "tt_greenlt",
        'icon': "ui/images/types/coi/summary.gif",
        },
)
thread_start=('ong',)
# With what you can respond.
# For a better example, please consult cvs repo!

relations={}
tt_ids = [x['id'] for x in types]
for type in types:
        relations[type['id']] = tt_ids

# EOF
