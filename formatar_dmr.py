# -*- coding: utf-8 -*-
"""Converte 20261006.csv -> formato RADIO_ID,CALLSIGN,FIRST_NAME,LAST_NAME,CITY,STATE,COUNTRY

================================================================================
VISAO GERAL
================================================================================
Le o arquivo de origem (texto livre, uma linha por operador no formato
    CALLSIGN - NOME [SOBRENOME] - CIDADE REGIAO PAIS -- RADIO_ID,RADIO_ID
) e gera um CSV estruturado com o schema fixo (NAO adicionar/remover colunas,
senao a aplicacao consumidora nao le):

    RADIO_ID,CALLSIGN,FIRST_NAME,LAST_NAME,CITY,STATE,COUNTRY

================================================================================
REGRAS POR CAMPO
================================================================================
- RADIO_ID : numero apos "--".
- CALLSIGN : 1a parte do texto (antes do 1o " - ").
- FIRST_NAME: nome; se composto, APENAS o primeiro nome (ex.: "Jose V" -> "Jose").
- LAST_NAME : sempre vazio (por requisito).
- CITY      : vazio para todos os paises, EXCETO Brasil. Para o Brasil, a cidade
              e extraida do texto (removendo pais e nome do estado) e ABREVIADA:
              * palavras proprias iniciais viram inicial+ponto;
              * COM preposicao (de/da/do/das/dos/e): abrevia as proprias antes da
                preposicao -> "Rio de Janeiro"=R. de Janeiro;
                "Sao Bernardo do Campo"=S.B. do Campo;
              * SEM preposicao: abrevia todas menos a ultima ->
                "Sao Paulo"=S.Paulo; "Porto Alegre"=P.Alegre;
              * cidade de 1 palavra fica por extenso (ex.: Aracaju);
              * tabela especial CIDADE_ESPECIAL (ex.: Florianopolis=Fpolis).
- STATE     : regiao/estado. Brasil -> sigla oficial (UF). Demais paises ->
              nome da regiao/estado. Preenchido por 2 vias, nesta prioridade:
                1) extraido do texto (quando o texto traz a regiao);
                2) derivado do INDICATIVO, mas SOMENTE quando o mapeamento
                   digito->regiao e UNICO (determinista). Casos ambiguos ficam
                   vazios para nao inventar dado.
- COUNTRY   : sigla do pais em 3 letras (USA, BRA, CAN, DEU, ...).

================================================================================
NORMALIZACAO ASCII (evita erro de leitura por caracteres especiais)
================================================================================
Todos os campos de texto da saida (CALLSIGN, FIRST_NAME, STATE) passam por
unidecode(): acentos e caracteres especiais sao transliterados para ASCII puro,
como nos textos de chamado. Exemplos:
    c->c  a->a  u->u  l->l  (diacriticos latinos)
    turco: I->I  i->i  s->s  g->g
    cirilico: Москва->Moskva
    chines: 市州->Shi Zhou
    polones: lodzkie->Lodzkie
Resultado: arquivo em UTF-8 porem 100% ASCII no conteudo.

================================================================================
EXTRACAO DE STATE A PARTIR DO TEXTO
================================================================================
REG_POR_PAIS mapeia cada pais a um dicionario de regioes conhecidas. A funcao
extrai_estado() procura a regiao conhecida que aparece MAIS A ESQUERDA no texto
(logo apos a cidade), pois varios registros trazem uma LISTA de regioes
(ex. Italia "Roma Lazio Umbria Sardinia" -> escolhe Lazio, nao Sardinia).
Paises cobertos por lista de regioes: BR, US, CA, GB, DE, AU, ES, FR, TR, IT,
NL, BE, CH, AT, PT, MX, JP, CN, PL.

================================================================================
DERIVACAO DE STATE PELO INDICATIVO (fallback, so casos UNICOS)
================================================================================
Aplicado apenas quando o texto nao trouxe a regiao. So preenche quando o
digito/prefixo mapeia a UMA unica regiao; ambiguos ficam vazios.

- BRASIL  uf_por_indicativo()  -- distribuicao oficial Anatel por prefixo+digito
          e, para PU, pela FAIXA de sufixo (ex.: PU5 A-L=SC, M-Y=PR;
          PU2 A-E=DF, F=GO, G-I=TO, K-Y=SP). Alem disso ha STATE_OVERRIDE por
          RADIO_ID para ~84 casos onde a cidade (nao o indicativo) define a UF.
          Fonte: https://py1geb.qsl.br/ARadio/PGRadio-Ind/PGRadio-Ind-HamBR.htm
- ESPANHA comunidade_por_indicativo_es() -- distrito EA/EB/EC + digito.
          Unicos: 3=Cataluna 6=Islas Baleares 7=Andalucia 8=Canarias
          9=Ceuta y Melilla. Ambiguos (1,2,4,5) -> vazio.
          Fonte (distritos URE): divulgacao publica de distritos de radio ES.
- CANADA  provincia_por_indicativo_ca() -- VE/VA + digito.
          Unicos: 1=Nova Scotia 2=Quebec 3=Ontario 4=Manitoba 5=Saskatchewan
          6=Alberta 7=British Columbia. Fonte: RAC / radioamateur.ca.
- ITALIA  regiao_por_indicativo_it() -- I/IK/IZ/IW + digito.
          Unicos: 2=Lombardy 3=Veneto 4=Emilia-Romagna 5=Tuscany 9=Sicily.
          Prefixos especiais unicos: IX1=Aosta IN3=Trentino-Alto Adige
          IV3=Friuli-Venezia Giulia IS0=Sardinia.
          Ambiguos (1,6,7,8,0) -> vazio. Fonte: distribuicao ARI/ministero IT.
- ARGENTINA provincia_por_indicativo_ar() -- LU/LW + digito + SUFIXO.
          Na Argentina a provincia e dada pela 1a letra do SUFIXO (nao pelo
          digito). Todas as letras mapeiam a uma provincia unica; faixas G e X
          dependem da 2a letra (GA-GO=Chaco GP-GZ=Formosa; XA-XO=Santa Cruz
          XP-XZ=Tierra del Fuego). Fonte: ENACOM / Call signs in Argentina.

Conteudo das fontes foi resumido/reescrito para conformidade de licenciamento.

================================================================================
OVERRIDES PONTUAIS (por RADIO_ID)
================================================================================
- STATE_OVERRIDE: UF/estado inferido pela cidade quando o texto nao traz a
  regiao (ex.: ~84 brasileiros; e os 2 W6FMG -> California).
- NOME_OVERRIDE : corrige FIRST_NAME digitado errado (ex.: CX7SS -> Eduilio).
- PAIS_OVERRIDE : corrige COUNTRY quando o pais digitado no texto esta errado E
  o indicativo + a cidade concordam com o pais correto. Ex.: 1106221/1106278
  (W6FMG, indicativo W6 = EUA, cidade American Canyon/CA) estavam como PHL por
  erro de digitacao -> corrigidos para USA. ATENCAO: nao reclassificar pais
  automaticamente pelo indicativo -- operadores que residem fora do pais de
  origem mantem o indicativo (ex.: F4BWG francês morando em Los Angeles e'
  corretamente USA). So' se corrige quando indicativo E cidade apontam o mesmo
  pais e o texto destoa dos dois.

================================================================================
OBSERVACOES
================================================================================
- Linhas 1268/1269 (de outro contexto) nao se aplicam aqui.
- Paises cujo indicativo NAO e determinista para regiao (ex.: EUA, Alemanha,
  Reino Unido, Japao, Polonia) tem STATE preenchido somente pelo texto.
- Requer o pacote 'Unidecode' (pip install Unidecode).
"""
import csv, re, unicodedata, sys, os
from unidecode import unidecode

# ----------------------------------------------------------------------------
# Caminhos: aceita argumentos de linha de comando
#   python formatar_dmr.py <ENTRADA> [SAIDA]
# Se SAIDA for omitida, gera <ENTRADA sem extensao>_formatado.csv na mesma pasta.
# ----------------------------------------------------------------------------
if len(sys.argv) >= 2:
    ALVO = sys.argv[1]
    if len(sys.argv) >= 3:
        SAIDA = sys.argv[2]
    else:
        # Sem SAIDA informada: nome com timestamp yyyymmddhhmm.csv na pasta da entrada.
        from datetime import datetime as _dt
        _pasta = os.path.dirname(os.path.abspath(ALVO))
        SAIDA = os.path.join(_pasta, _dt.now().strftime("%Y%m%d%H%M") + ".csv")
    # Idioma dos nomes de pais: 4o argumento posicional ('pt'/'en') ou flag '--en'.
    _IDIOMA_ARG = "pt"
    if "--en" in sys.argv:
        _IDIOMA_ARG = "en"
    elif len(sys.argv) >= 4 and sys.argv[3].strip().lower() in ("pt", "en"):
        _IDIOMA_ARG = sys.argv[3].strip().lower()
else:
    # fallback (uso manual): nome com timestamp yyyymmddhhmm.csv
    from datetime import datetime as _dt
    ALVO = r"C:\Users\DanielRégis\Downloads\cbridge_user.csv"
    SAIDA = os.path.join(os.path.dirname(os.path.abspath(ALVO)),
                         _dt.now().strftime("%Y%m%d%H%M") + ".csv")
    _IDIOMA_ARG = "pt"

def strip_acc(s):
    # normaliza para ASCII puro (lodzkie, Shi Zhou, Moskva, c, a, s, I...)
    return unidecode(s)

def ascii_clean(s):
    """Transliteracao ASCII para os campos de saida (como nos textos de chamado):
    remove acentos/diacriticos e caracteres especiais, mantendo o dado legivel."""
    return unidecode(s).strip()

# ----------------------------------------------------------------------------
# ENRIQUECIMENTO: arquivo de referencia (RADIO_ID -> REGIAO) usado para preencher
# a regiao (col5) quando o nosso resultado ficar VAZIO. Nunca sobrescreve o que
# ja temos. Fonte: lista COMPLETE DMR-ID CONTACT LIST (compactada p/ id+regiao).
# ----------------------------------------------------------------------------
import os as _os
import sys as _sys
# Caminho base: no modo empacotado (PyInstaller) os dados ficam em sys._MEIPASS;
# no modo normal, ao lado deste arquivo.
if getattr(_sys, "frozen", False) and hasattr(_sys, "_MEIPASS"):
    _BASE_REF = _os.path.join(_sys._MEIPASS, "ref", "regioes_ref.csv")
else:
    _BASE_REF = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "ref", "regioes_ref.csv")
REF_REGIOES = _BASE_REF
REGIAO_REF = {}
if _os.path.exists(REF_REGIOES):
    with open(REF_REGIOES, encoding="utf-8", errors="replace") as _f:
        _r = csv.reader(_f)
        next(_r, None)
        for _row in _r:
            if len(_row) >= 2 and _row[1].strip():
                REGIAO_REF[_row[0].strip()] = _row[1].strip()

# ---- paises: nome (no texto) -> 3 letras ----
PAIS_COD = {
    "united states": "USA", "united states of america": "USA", "usa": "USA",
    "canada": "CAN", "brazil": "BRA", "brasil": "BRA",
    "united kingdom": "GBR", "england": "GBR", "scotland": "GBR", "wales": "GBR",
    "northern ireland": "GBR",
    "germany": "DEU", "china": "CHN", "italy": "ITA", "spain": "ESP",
    "turkey": "TUR", "poland": "POL", "australia": "AUS", "chile": "CHL",
    "france": "FRA", "russia": "RUS", "russian federation": "RUS",
    "netherlands": "NLD", "india": "IND", "japan": "JPN", "austria": "AUT",
    "sweden": "SWE", "portugal": "PRT", "switzerland": "CHE", "belgium": "BEL",
    "mexico": "MEX", "argentina": "ARG", "norway": "NOR", "denmark": "DNK",
    "finland": "FIN", "ireland": "IRL", "new zealand": "NZL",
    "south korea": "KOR", "korea": "KOR", "czech republic": "CZE", "czechia": "CZE",
    "romania": "ROU", "greece": "GRC", "hungary": "HUN", "colombia": "COL",
    "venezuela": "VEN", "south africa": "ZAF", "thailand": "THA",
    "indonesia": "IDN", "philippines": "PHL", "malaysia": "MYS", "ukraine": "UKR",
    "croatia": "HRV", "slovenia": "SVN", "slovakia": "SVK", "serbia": "SRB",
    "bulgaria": "BGR", "israel": "ISR", "taiwan": "TWN", "hong kong": "HKG",
    "luxembourg": "LUX", "iceland": "ISL", "estonia": "EST", "latvia": "LVA",
    "lithuania": "LTU", "uruguay": "URY", "peru": "PER", "ecuador": "ECU",
    "costa rica": "CRI", "puerto rico": "PRI", "singapore": "SGP",
    "paraguay": "PRY", "bolivia": "BOL", "panama": "PAN", "cuba": "CUB",
    "guatemala": "GTM", "dominican republic": "DOM", "el salvador": "SLV",
    "honduras": "HND", "nicaragua": "NIC",
    # ampliacoes
    "turkiye": "TUR",
    "korea": "KOR", "republic of korea": "KOR", "south korea": "KOR",
    "bosnia and herzegovina": "BIH", "bosnia herzegovina": "BIH", "herzegovina": "BIH",
    "luxemburg": "LUX",
    "belarus": "BLR",
    "kazakhstan": "KAZ",
    "bangladesh": "BGD",
    "oman": "OMN",
    "north macedonia": "MKD", "macedonia": "MKD",
    "morocco": "MAR",
    "trinidad and tobago": "TTO", "tobago": "TTO",
    "cyprus": "CYP",
    "united arab emirates": "ARE", "emirates": "ARE",
    "malta": "MLT",
    "reunion": "REU",
    "moldova": "MDA",
    "montenegro": "MNE",
    "kuwait": "KWT",
    "lebanon": "LBN",
    "pakistan": "PAK",
    "bahrain": "BHR",
    "sri lanka": "LKA",
    "andorra": "AND",
    "guam": "GUM",
    "saudi arabia": "SAU", "arabia": "SAU",
    "dominica": "DMA",
    "san marino": "SMR",
    "albania": "ALB",
    "algeria": "DZA",
    "anguilla": "AIA",
    "armenia": "ARM",
    "aruba": "ABW",
    "azerbaijan": "AZE",
    "bahamas": "BHS",
    "barbados": "BRB",
    "antigua and barbuda": "ATG",
    "belize": "BLZ",
    "georgia country": "GEO",
    "egypt": "EGY",
    "jordan": "JOR",
    "qatar": "QAT",
    "tunisia": "TUN",
    "nigeria": "NGA",
    "kenya": "KEN",
    "iran": "IRN",
    "iraq": "IRQ",
    "vietnam": "VNM",
    "cambodia": "KHM",
    "nepal": "NPL",
    "mongolia": "MNG",
    "myanmar": "MMR",
    "brunei": "BRN",
    "fiji": "FJI",
    "jamaica": "JAM",
    "haiti": "HTI",
    "guyana": "GUY",
    "suriname": "SUR",
    "greenland": "GRL",
    "faroe islands": "FRO",
    "gibraltar": "GIB",
    "monaco": "MCO",
    "liechtenstein": "LIE",
    "kosovo": "XKX",
    "georgia (country)": "GEO",
    "maldives": "MDV",
    "mauritius": "MUS",
    "madagascar": "MDG",
    "zimbabwe": "ZWE",
    "zambia": "ZMB",
    "ghana": "GHA",
    "uganda": "UGA",
    "tanzania": "TZA",
    "cape verde": "CPV", "cabo verde": "CPV",
    "cayman islands": "CYM",
    "bermuda": "BMU",
    "curacao": "CUW",
    "martinique": "MTQ",
    "guadeloupe": "GLP",
    "french polynesia": "PYF",
    "new caledonia": "NCL",
    "macau": "MAC", "macao": "MAC",
    # variacoes de grafia / final diferente
    "korea republic of": "KOR", "korea  republic of": "KOR",
    "bosnia and hercegovina": "BIH", "hercegovina": "BIH",
    "corsica": "FRA",
    "u.s. virgin islands": "VIR", "virgin islands": "VIR",
    "uzbekistan": "UZB",
    "georgia country": "GEO",
    "saint lucia": "LCA", "lucia": "LCA",
    "saint vincent and the grenadines": "VCT", "grenadines": "VCT",
    "namibia": "NAM",
    "bonaire": "BES",
    "saint kitts and nevis": "KNA", "nevis": "KNA",
    "grenada": "GRD",
    "mozambique": "MOZ",
    "brunei darussalam": "BRN", "darussalam": "BRN",
    "kyrgyzstan": "KGZ",
    "micronesia": "FSM",
    "ivory coast": "CIV", "cote d ivoire": "CIV",
    "tajikistan": "TJK",
    "turkmenistan": "TKM",
    "palestine": "PSE",
    "syria": "SYR",
    "afghanistan": "AFG",
    "angola": "AGO",
    "botswana": "BWA",
    "senegal": "SEN",
    "cameroon": "CMR",
    "ethiopia": "ETH",
    "sudan": "SDN",
    "libya": "LBY",
    "yemen": "YEM",
    "sao tome and principe": "STP",
    "seychelles": "SYC",
    "gabon": "GAB",
    "benin": "BEN",
    "togo": "TGO",
    "mali": "MLI",
    "burkina faso": "BFA",
    "niger": "NER",
    "chad": "TCD",
    "mauritania": "MRT",
    "rwanda": "RWA",
    "malawi": "MWI",
    "lesotho": "LSO",
    "eswatini": "SWZ", "swaziland": "SWZ",
    "democratic republic of the congo": "COD", "congo": "COG",
    "palau": "PLW",
    "samoa": "WSM",
    "tonga": "TON",
    "vanuatu": "VUT",
    "papua new guinea": "PNG",
    "timor leste": "TLS", "east timor": "TLS",
    "laos": "LAO",
    # mais variacoes de final
    "argentina republic": "ARG",
    "central african republic": "CAF",
    "georgia": "GEO",
    "slovenia obalno kraska": "SVN", "obalno": "SVN", "primorsko": "SVN", "obalno kraska": "SVN",
    "donostia": "ESP",
    # territorios/paises raros (ultimo lote)
    "aaland islands": "ALA", "aland islands": "ALA",
    "french guiana": "GUF",
    "montserrat": "MSR",
    "kiribati": "KIR",
    "cook islands": "COK",
    "mauretania": "MRT", "mauritania": "MRT",
    "guinea": "GIN",
    "liberia": "LBR",
    "equatorial guinea": "GNQ",
    "djibouti": "DJI",
    "swasiland": "SWZ",
    "ascension island": "SHN",
    "falkland islands": "FLK",
}

# ---- nome legivel por sigla (col6). Compostos abreviados de forma intendivel. ----
# Regras: nomes simples por extenso; compostos abreviam a 1a palavra (C.Rica,
# Pol.Francesa); nomes oficiais longos ficam so com o nome principal (Micronesia).
PAIS_NOME = {
    "USA": "EUA", "GBR": "Reino Unido", "DEU": "Alemanha", "CHN": "China",
    "ITA": "Italia", "ESP": "Espanha", "TUR": "Turquia", "BRA": "Brasil",
    "CAN": "Canada", "POL": "Polonia", "AUS": "Australia", "CHL": "Chile",
    "FRA": "Franca", "RUS": "Russia", "NLD": "Holanda", "JPN": "Japao",
    "AUT": "Austria", "SWE": "Suecia", "KOR": "Coreia do Sul", "GRC": "Grecia",
    "ARG": "Argentina", "THA": "Tailandia", "CHE": "Suica", "PHL": "Filipinas",
    "BEL": "Belgica", "IDN": "Indonesia", "DNK": "Dinamarca", "PT": "Portugal",
    "FIN": "Finlandia", "NOR": "Noruega", "NZL": "N.Zelandia", "IND": "India",
    "ROU": "Romenia", "MYS": "Malasia", "SVN": "Eslovenia", "MEX": "Mexico",
    "CZE": "Tchequia", "UKR": "Ucrania", "HUN": "Hungria", "COL": "Colombia",
    "PRI": "P.Rico", "BGR": "Bulgaria", "SRB": "Servia", "ZAF": "Africa do Sul",
    "HRV": "Croacia", "VEN": "Venezuela", "TWN": "Taiwan", "BIH": "Bosnia",
    "URY": "Uruguai", "ISR": "Israel", "IRL": "Irlanda", "PAN": "Panama",
    "HKG": "Hong Kong", "DOM": "Rep.Dominicana", "SVK": "Eslovaquia", "ECU": "Equador",
    "CRI": "C.Rica", "LUX": "Luxemburgo", "BLR": "Belarus", "KAZ": "Cazaquistao",
    "LTU": "Lituania", "BGD": "Bangladesh", "OMN": "Oma", "EST": "Estonia",
    "PER": "Peru", "MKD": "Macedonia do Norte", "MAR": "Marrocos",
    "TTO": "Trinidad e Tobago", "LVA": "Letonia", "CUB": "Cuba", "CYP": "Chipre",
    "ARE": "Emirados Arabes", "MLT": "Malta", "SGP": "Singapura", "REU": "Reuniao",
    "GTM": "Guatemala", "VIR": "I.Virgens US", "VGB": "I.Virgens UK", "MDA": "Moldova",
    "MNE": "Montenegro", "PRY": "Paraguai", "KWT": "Kuwait", "LBN": "Libano",
    "PAK": "Paquistao", "LKA": "Sri Lanka", "BHR": "Bahrein", "AND": "Andorra",
    "ISL": "Islandia", "GUM": "Guam", "SAU": "Arabia Saudita", "SLV": "El Salvador",
    "HND": "Honduras", "SMR": "San Marino", "DMA": "Dominica", "GEO": "Georgia",
    "BRB": "Barbados", "HTI": "Haiti", "CUW": "Curacao", "QAT": "Catar",
    "NIC": "Nicaragua", "ABW": "Aruba", "BLZ": "Belize", "UZB": "Uzbequistao",
    "JAM": "Jamaica", "MTQ": "Martinica", "LIE": "Liechtenstein", "LCA": "Sta.Lucia",
    "GLP": "Guadalupe", "VCT": "S.Vicente e Granadinas", "BHS": "Bahamas",
    "DZA": "Argelia", "NAM": "Namibia", "GIB": "Gibraltar", "KNA": "S.Cristovao e Nevis",
    "BES": "Bonaire", "NCL": "Nova Caledonia", "VNM": "Vietna", "JOR": "Jordania",
    "MUS": "Mauricio", "ARM": "Armenia", "CYM": "Ilhas Cayman", "BMU": "Bermudas",
    "GRD": "Granada", "AZE": "Azerbaijao", "IRQ": "Iraque", "PNG": "Papua N.Guine",
    "CIV": "Costa do Marfim", "MOZ": "Mocambique", "GUY": "Guiana", "FRO": "Ilhas Faroe",
    "NPL": "Nepal", "GHA": "Gana", "KEN": "Quenia", "MCO": "Monaco",
    "GRL": "Groenlandia", "IRN": "Ira", "MDV": "Maldivas", "BRN": "Brunei",
    "CPV": "Cabo Verde", "KGZ": "Quirguistao", "FSM": "Micronesia", "ALA": "Ilhas Aland",
    "GUF": "Guiana Francesa", "AIA": "Anguilla", "MNG": "Mongolia", "MAC": "Macau",
    "NGA": "Nigeria", "ZMB": "Zambia", "MDG": "Madagascar", "ZWE": "Zimbabue",
    "FLK": "Ilhas Malvinas", "XKX": "Kosovo", "ALB": "Albania", "ATG": "Antigua e Barbuda",
    "MSR": "Montserrat", "LAO": "Laos", "VUT": "Vanuatu", "WSM": "Samoa",
    "PLW": "Palau", "EGY": "Egito", "BFA": "Burkina Faso", "LBR": "Liberia",
    "TCD": "Chade", "CAF": "Rep.Centro-Africana", "CMR": "Camaroes", "TZA": "Tanzania",
    "LSO": "Lesoto", "SWZ": "Essuatini", "BOL": "Bolivia", "SUR": "Suriname",
    "YEM": "Iemen", "TON": "Tonga", "KIR": "Kiribati", "COK": "Ilhas Cook",
    "SEN": "Senegal", "MRT": "Mauritania", "GIN": "Guine", "TGO": "Togo",
    "GNQ": "Guine Equatorial", "SYC": "Seychelles", "SDN": "Sudao", "DJI": "Djibuti",
    "MWI": "Malawi", "BWA": "Botsuana", "SHN": "Sta.Helena",
    # pais que pode aparecer em bases novas, nao presente na base de out/2026:
    "PYF": "Pol.Francesa",
}

# Nomes de pais em INGLES (ASCII, curtos p/ caber no display de 20 chars com a
# sigla). Mesmas chaves de PAIS_NOME. Selecionado quando idioma = 'en'.
PAIS_NOME_EN = {
    "USA": "USA", "GBR": "United Kingdom", "DEU": "Germany", "CHN": "China",
    "ITA": "Italy", "ESP": "Spain", "TUR": "Turkey", "BRA": "Brazil",
    "CAN": "Canada", "POL": "Poland", "AUS": "Australia", "CHL": "Chile",
    "FRA": "France", "RUS": "Russia", "NLD": "Netherlands", "JPN": "Japan",
    "AUT": "Austria", "SWE": "Sweden", "KOR": "South Korea", "GRC": "Greece",
    "ARG": "Argentina", "THA": "Thailand", "CHE": "Switzerland", "PHL": "Philippines",
    "BEL": "Belgium", "IDN": "Indonesia", "DNK": "Denmark", "PT": "Portugal",
    "FIN": "Finland", "NOR": "Norway", "NZL": "New Zealand", "IND": "India",
    "ROU": "Romania", "MYS": "Malaysia", "SVN": "Slovenia", "MEX": "Mexico",
    "CZE": "Czechia", "UKR": "Ukraine", "HUN": "Hungary", "COL": "Colombia",
    "PRI": "Puerto Rico", "BGR": "Bulgaria", "SRB": "Serbia", "ZAF": "South Africa",
    "HRV": "Croatia", "VEN": "Venezuela", "TWN": "Taiwan", "BIH": "Bosnia",
    "URY": "Uruguay", "ISR": "Israel", "IRL": "Ireland", "PAN": "Panama",
    "HKG": "Hong Kong", "DOM": "Dominican Rep.", "SVK": "Slovakia", "ECU": "Ecuador",
    "CRI": "Costa Rica", "LUX": "Luxembourg", "BLR": "Belarus", "KAZ": "Kazakhstan",
    "LTU": "Lithuania", "BGD": "Bangladesh", "OMN": "Oman", "EST": "Estonia",
    "PER": "Peru", "MKD": "North Macedonia", "MAR": "Morocco", "TTO": "Trinidad",
    "LVA": "Latvia", "CUB": "Cuba", "CYP": "Cyprus", "ARE": "UAE",
    "MLT": "Malta", "SGP": "Singapore", "REU": "Reunion", "GTM": "Guatemala",
    "VIR": "Virgin Is. US", "VGB": "Virgin Is. UK", "MDA": "Moldova", "MNE": "Montenegro",
    "PRY": "Paraguay", "KWT": "Kuwait", "LBN": "Lebanon", "PAK": "Pakistan",
    "LKA": "Sri Lanka", "BHR": "Bahrain", "AND": "Andorra", "ISL": "Iceland",
    "GUM": "Guam", "SAU": "Saudi Arabia", "SLV": "El Salvador", "HND": "Honduras",
    "SMR": "San Marino", "DMA": "Dominica", "GEO": "Georgia", "BRB": "Barbados",
    "HTI": "Haiti", "CUW": "Curacao", "QAT": "Qatar", "NIC": "Nicaragua",
    "ABW": "Aruba", "BLZ": "Belize", "UZB": "Uzbekistan", "JAM": "Jamaica",
    "MTQ": "Martinique", "LIE": "Liechtenstein", "LCA": "St.Lucia", "GLP": "Guadeloupe",
    "VCT": "St.Vincent", "BHS": "Bahamas", "DZA": "Algeria", "NAM": "Namibia",
    "GIB": "Gibraltar", "KNA": "St.Kitts Nevis", "BES": "Bonaire", "NCL": "New Caledonia",
    "VNM": "Vietnam", "JOR": "Jordan", "MUS": "Mauritius", "ARM": "Armenia",
    "CYM": "Cayman Is.", "BMU": "Bermuda", "GRD": "Grenada", "AZE": "Azerbaijan",
    "IRQ": "Iraq", "PNG": "Papua N.Guinea", "CIV": "Ivory Coast", "MOZ": "Mozambique",
    "GUY": "Guyana", "FRO": "Faroe Is.", "NPL": "Nepal", "GHA": "Ghana",
    "KEN": "Kenya", "MCO": "Monaco", "GRL": "Greenland", "IRN": "Iran",
    "MDV": "Maldives", "BRN": "Brunei", "CPV": "Cape Verde", "KGZ": "Kyrgyzstan",
    "FSM": "Micronesia", "ALA": "Aland Is.", "GUF": "French Guiana", "AIA": "Anguilla",
    "MNG": "Mongolia", "MAC": "Macau", "NGA": "Nigeria", "ZMB": "Zambia",
    "MDG": "Madagascar", "ZWE": "Zimbabwe", "FLK": "Falkland Is.", "XKX": "Kosovo",
    "ALB": "Albania", "ATG": "Antigua", "MSR": "Montserrat", "LAO": "Laos",
    "VUT": "Vanuatu", "WSM": "Samoa", "PLW": "Palau", "EGY": "Egypt",
    "BFA": "Burkina Faso", "LBR": "Liberia", "TCD": "Chad", "CAF": "Centr.Afr.Rep.",
    "CMR": "Cameroon", "TZA": "Tanzania", "LSO": "Lesotho", "SWZ": "Eswatini",
    "BOL": "Bolivia", "SUR": "Suriname", "YEM": "Yemen", "TON": "Tonga",
    "KIR": "Kiribati", "COK": "Cook Is.", "SEN": "Senegal", "MRT": "Mauritania",
    "GIN": "Guinea", "TGO": "Togo", "GNQ": "Eq.Guinea", "SYC": "Seychelles",
    "SDN": "Sudan", "DJI": "Djibouti", "MWI": "Malawi", "BWA": "Botswana",
    "SHN": "St.Helena", "PYF": "Fr.Polynesia",
}

# Idioma dos nomes de pais na saida: 'pt' (padrao) ou 'en'. Definido via argv.
IDIOMA_PAIS = _IDIOMA_ARG if "_IDIOMA_ARG" in dir() else "pt"

def nome_pais_idioma(sigla):
    """Nome do pais no idioma selecionado (IDIOMA_PAIS). Fallback: PT -> sigla."""
    if IDIOMA_PAIS == "en":
        return PAIS_NOME_EN.get(sigla) or PAIS_NOME.get(sigla, "")
    return PAIS_NOME.get(sigla, "")

def nome_pais(sigla):
    """[DESATIVADO] Retorna nome legivel do pais. NAO usar na col6: a aplicacao
    consumidora valida a col6 esperando a SIGLA curta (CAN, BRA, ESP...); nome por
    extenso gera 'CSV File Invalid!'. Mantido aqui apenas como referencia."""
    return PAIS_NOME.get(sigla, sigla)

# ---- estados do Brasil -> UF ----
BR_UF = {
    "acre":"AC","alagoas":"AL","amapa":"AP","amazonas":"AM","bahia":"BA",
    "ceara":"CE","distrito federal":"DF","espirito santo":"ES","goias":"GO",
    "maranhao":"MA","mato grosso":"MT","mato grosso do sul":"MS","minas gerais":"MG",
    "para":"PA","paraiba":"PB","parana":"PR","pernambuco":"PE","piaui":"PI",
    "rio de janeiro":"RJ","rio grande do norte":"RN","rio grande do sul":"RS",
    "rondonia":"RO","roraima":"RR","santa catarina":"SC","sao paulo":"SP",
    "sergipe":"SE","tocantins":"TO",
}

# ---- estados dos EUA (nome completo) ----
US_STATES = [
    "alabama","alaska","arizona","arkansas","california","colorado","connecticut",
    "delaware","florida","georgia","hawaii","idaho","illinois","indiana","iowa",
    "kansas","kentucky","louisiana","maine","maryland","massachusetts","michigan",
    "minnesota","mississippi","missouri","montana","nebraska","nevada",
    "new hampshire","new jersey","new mexico","new york","north carolina",
    "north dakota","ohio","oklahoma","oregon","pennsylvania","rhode island",
    "south carolina","south dakota","tennessee","texas","utah","vermont",
    "virginia","washington","west virginia","wisconsin","wyoming",
    "district of columbia",
]
US_STATE_TITLE = {s: " ".join(w.capitalize() for w in s.split()) for s in US_STATES}

# ---- provincias do Canada ----
CA_PROV = {
    "ontario":"Ontario","quebec":"Quebec","british columbia":"British Columbia",
    "alberta":"Alberta","manitoba":"Manitoba","saskatchewan":"Saskatchewan",
    "nova scotia":"Nova Scotia","new brunswick":"New Brunswick",
    "newfoundland and labrador":"Newfoundland and Labrador","newfoundland":"Newfoundland and Labrador",
    "prince edward island":"Prince Edward Island","yukon":"Yukon",
    "northwest territories":"Northwest Territories","nunavut":"Nunavut",
}

# ---- Reino Unido ----
GB_REG = {
    "england":"England","scotland":"Scotland","wales":"Wales",
    "northern ireland":"N.Ireland",
}

# ---- Alemanha (16 Laender) ----
DE_REG = {
    "baden-wurttemberg":"Baden-Wurttemberg","baden-wuerttemberg":"Baden-Wurttemberg",
    "bayern":"Bayern","berlin":"Berlin","brandenburg":"Brandenburg","bremen":"Bremen",
    "hamburg":"Hamburg","hessen":"Hessen",
    "mecklenburg-vorpommern":"Mecklenburg-Vorpommern","mecklenburg-vorpommen":"Mecklenburg-Vorpommern",
    "niedersachsen":"Niedersachsen","nordrhein-westfalen":"Nordrhein-Westfalen",
    "rheinland-pfalz":"Rheinland-Pfalz","saarland":"Saarland","sachsen":"Sachsen",
    "sachsen-anhalt":"Sachsen-Anhalt","schleswig-holstein":"Schleswig-Holstein",
    "thuringen":"Thuringen","thueringen":"Thuringen",
}

# ---- Australia ----
AU_REG = {
    "new south wales":"New South Wales","victoria":"Victoria","queensland":"Queensland",
    "south australia":"South Australia","western australia":"Western Australia",
    "tasmania":"Tasmania","northern territory":"Northern Territory",
    "australian capital territory":"Australian Capital Territory",
}

# ---- Reino Espanha (comunidades autonomas) ----
ES_REG = {
    "andalucia":"Andalucia","aragon":"Aragon","asturias":"Asturias",
    "islas baleares":"Islas Baleares","baleares":"Islas Baleares",
    "canarias":"Canarias","cantabria":"Cantabria","castilla-la mancha":"Castilla-La Mancha",
    "castilla y leon":"Castilla y Leon","cataluna":"Cataluna","catalonia":"Cataluna",
    "extremadura":"Extremadura","galicia":"Galicia","la rioja":"La Rioja",
    "madrid":"Madrid","murcia":"Murcia","navarra":"Navarra",
    "pais vasco":"Pais Vasco","basque country":"Pais Vasco",
    "comunidad valenciana":"Valencia","valencia":"Valencia",
}

# ---- Franca (regioes) ----
FR_REG = {
    "auvergne-rhone-alpes":"Auvergne-Rhone-Alpes","bourgogne-franche-comte":"Bourgogne-Franche-Comte",
    "bretagne":"Bretagne","centre-val de loire":"Centre-Val de Loire","corsica":"Corsica",
    "grand est":"Grand Est","hauts-de-france":"Hauts-de-France","ile-de-france":"Ile-de-France",
    "normandie":"Normandie","nouvelle-aquitaine":"Nouvelle-Aquitaine","occitanie":"Occitanie",
    "pays de la loire":"Pays de la Loire","provence-alpes-cote d azur":"Provence-Alpes-Cote d Azur",
}

# ---- Turquia (regioes) ----
TR_REG = {
    "marmara region":"Marmara Region","marmara":"Marmara Region",
    "aegean region":"Aegean Region","aegean":"Aegean Region",
    "mediterranean region":"Mediterranean Region","mediterranean":"Mediterranean Region",
    "central anatolia region":"Central Anatolia Region","central anatolia":"Central Anatolia Region",
    "black sea region":"Black Sea Region","black sea":"Black Sea Region",
    "eastern anatolia region":"Eastern Anatolia Region","eastern anatolia":"Eastern Anatolia Region",
    "southeastern anatolia region":"Southeastern Anatolia Region","southeastern anatolia":"Southeastern Anatolia Region",
}

# ---- Italia (regioes; muitas vem agrupadas, pegamos a 1a palavra-regiao do fim) ----
IT_REG = {
    "abruzzo":"Abruzzo","basilicata":"Basilicata","calabria":"Calabria","campania":"Campania",
    "emilia-romagna":"Emilia-Romagna","friuli-venezia giulia":"Friuli-Venezia Giulia",
    "lazio":"Lazio","liguria":"Liguria","lombardy":"Lombardy","lombardia":"Lombardy",
    "marche":"Marche","molise":"Molise","piedmont":"Piedmont","piemonte":"Piedmont",
    "sardinia":"Sardinia","sardegna":"Sardinia","sicily":"Sicily","sicilia":"Sicily",
    "tuscany":"Tuscany","toscana":"Tuscany","trentino-alto adige":"Trentino-Alto Adige",
    "umbria":"Umbria","aosta":"Aosta","veneto":"Veneto","apulia":"Apulia","puglia":"Apulia",
}

# ---- Paises Baixos (provincias) ----
NL_REG = {
    "drenthe":"Drenthe","flevoland":"Flevoland","friesland":"Friesland","gelderland":"Gelderland",
    "groningen":"Groningen","limburg":"Limburg","noord-brabant":"Noord-Brabant",
    "noord-holland":"Noord-Holland","overijssel":"Overijssel","utrecht":"Utrecht",
    "zeeland":"Zeeland","zuid-holland":"Zuid-Holland",
}

# ---- Belgica (provincias/regioes) ----
BE_REG = {
    "antwerpen":"Antwerpen","antwerp":"Antwerpen","oost-vlaanderen":"Oost-Vlaanderen",
    "west-vlaanderen":"West-Vlaanderen","vlaams-brabant":"Vlaams-Brabant",
    "limburg":"Limburg","hainaut":"Hainaut","liege":"Liege","luxembourg":"Luxembourg",
    "namur":"Namur","brabant wallon":"Brabant Wallon","brussels":"Brussels",
}

# ---- Suica (cantoes mais comuns) ----
CH_REG = {
    "zurich":"Zurich","bern":"Bern","vaud":"Vaud","geneva":"Geneva","geneve":"Geneva",
    "basel":"Basel","lucerne":"Lucerne","luzern":"Lucerne","ticino":"Ticino",
    "st gallen":"St Gallen","valais":"Valais","neuchatel":"Neuchatel","fribourg":"Fribourg",
    "thurgau":"Thurgau","aargau":"Aargau","graubunden":"Graubunden","solothurn":"Solothurn",
}

# ---- Austria (Laender) ----
AT_REG = {
    "wien":"Wien","vienna":"Wien","niederosterreich":"Niederosterreich","oberosterreich":"Oberosterreich",
    "salzburg":"Salzburg","tirol":"Tirol","vorarlberg":"Vorarlberg","karnten":"Karnten",
    "steiermark":"Steiermark","burgenland":"Burgenland",
}

# ---- Portugal (regioes) ----
PT_REG = {
    "regiao norte":"Regiao Norte","regiao centro":"Regiao Centro","regiao de lisboa":"Regiao de Lisboa",
    "alentejo":"Alentejo","algarve":"Algarve","acores":"Acores","madeira":"Madeira",
}

# ---- Mexico (estados comuns) ----
MX_REG = {
    "yucatan":"Yucatan","quintana roo":"Quintana Roo","mexico city":"Mexico City",
    "jalisco":"Jalisco","nuevo leon":"Nuevo Leon","tamaulipas":"Tamaulipas",
    "veracruz":"Veracruz","puebla":"Puebla","guanajuato":"Guanajuato","sonora":"Sonora",
    "chihuahua":"Chihuahua","baja california":"Baja California","coahuila":"Coahuila",
    "michoacan":"Michoacan","sinaloa":"Sinaloa","oaxaca":"Oaxaca","chiapas":"Chiapas",
    "queretaro":"Queretaro","morelos":"Morelos","hidalgo":"Hidalgo","durango":"Durango",
}

# ---- Japao (regioes) ----
JP_REG = {
    "hokkaido":"Hokkaido","tohoku":"Tohoku","kanto":"Kanto","chubu":"Chubu",
    "shinetsu":"Shinetsu","kansai":"Kansai","kinki":"Kansai","chugoku":"Chugoku",
    "shikoku":"Shikoku","kyushu":"Kyushu","okinawa":"Okinawa",
}

# ---- China (Hong Kong / Macau e algumas provincias) ----
CN_REG = {
    "hong kong":"Hong Kong","macau":"Macau","macao":"Macau","guangdong":"Guangdong",
    "beijing":"Beijing","shanghai":"Shanghai","zhejiang":"Zhejiang","jiangsu":"Jiangsu",
    "fujian":"Fujian","sichuan":"Sichuan","shandong":"Shandong","hubei":"Hubei",
}

# ---- Polonia (16 voivodias; chaves sem diacriticos pois o texto e normalizado) ----
PL_REG = {
    "dolnoslaskie":"Dolnoslaskie","kujawsko-pomorskie":"Kujawsko-Pomorskie",
    "lubelskie":"Lubelskie","lubuskie":"Lubuskie","lodzkie":"Lodzkie",
    "malopolskie":"Malopolskie","mazowieckie":"Mazowieckie","opolskie":"Opolskie",
    "podkarpackie":"Podkarpackie","podlaskie":"Podlaskie","pomorskie":"Pomorskie",
    "slaskie":"Slaskie","swietokrzyskie":"Swietokrzyskie",
    "warminsko-mazurskie":"Warminsko-Mazurskie","wielkopolskie":"Wielkopolskie",
    "zachodniopomorskie":"Zachodniopomorskie",
}

# Mapa pais-codigo -> dicionario de regioes (chave minuscula sem acento -> valor formatado)
REG_POR_PAIS = {
    "BRA": BR_UF,
    "USA": {s: US_STATE_TITLE[s] for s in US_STATES},
    "CAN": CA_PROV,
    "GBR": GB_REG,
    "DEU": DE_REG,
    "AUS": AU_REG,
    "ESP": ES_REG,
    "FRA": FR_REG,
    "TUR": TR_REG,
    "ITA": IT_REG,
    "NLD": NL_REG,
    "BEL": BE_REG,
    "CHE": CH_REG,
    "AUT": AT_REG,
    "PRT": PT_REG,
    "MEX": MX_REG,
    "JPN": JP_REG,
    "CHN": CN_REG,
    "POL": PL_REG,
}

def extrai_pais(local_low):
    for nome in sorted(PAIS_COD, key=len, reverse=True):
        if local_low.endswith(nome):
            resto = local_low[: len(local_low) - len(nome)].strip()
            return PAIS_COD[nome], resto
    return "", local_low

def extrai_estado(resto_low, cod_pais):
    """resto_low = texto sem o pais (minusculo, sem acento). Retorna STATE formatado.

    Estrategia: procura TODAS as regioes conhecidas do pais presentes no texto e
    escolhe a que aparece em posicao mais a esquerda (logo apos a cidade), pois
    muitos registros trazem uma lista de regioes (ex. Italia 'Lazio Umbria Sardinia')
    em que a 1a e a correta. Em empate de posicao, prefere o nome mais longo."""
    resto_low = resto_low.strip()
    regioes = REG_POR_PAIS.get(cod_pais)
    if not regioes:
        return ""
    melhor = None  # (pos, -len, valor)
    for nome in regioes:
        # casa a regiao como palavra(s) delimitada(s)
        idx = -1
        for mm in re.finditer(r"(?<![a-z])" + re.escape(nome) + r"(?![a-z])", resto_low):
            idx = mm.start()
            break
        if idx >= 0:
            cand = (idx, -len(nome), regioes[nome])
            if melhor is None or cand < melhor:
                melhor = cand
    return melhor[2] if melhor else ""

# Override pontual de STATE por RADIO_ID (casos sem UF no texto; inferido pela cidade)
# Override pontual de STATE por RADIO_ID (casos sem UF no texto; inferido pela cidade)
STATE_OVERRIDE = {
    "7240001": "SC",   # PP5VX - Sao Francisco do Sul
    "7243079": "RJ",   # PY1MV - Macae (texto trazia Espirito Santo errado)
    "7241147": "SP",   # PU2RZP - S.Judas (bairro de Sao Paulo; texto trazia ES errado)
    "7240030": "SP",   # PY2OKB - Sao Paulo (texto trazia Acre errado)
    "7244475": "SP",   # PU2RJF - Sao Paulo (texto trazia Pernambuco errado)
    "7240014": "SE",   # Aracaju
    "7240026": "SP",   # Itapecerica da Serra
    "7240032": "SP",   # Campinas
    "7240036": "PR",   # Curitiba
    "7240043": "SP",   # Aguas de Santa Barbara
    "7240044": "PR",   # Maringa
    "7240046": "PR",   # Maringa
    "7240049": "PR",   # Maringa
    "7240050": "PR",   # Maringa
    "7240055": "RS",   # Canoas
    "7240837": "SP",   # Campinas
    "7240907": "SP",   # Santos
    "7240959": "BA",   # Guanambi
    "7241058": "RJ",   # Tamoios (Cabo Frio)
    "7241350": "MT",   # Cuiaba
    "7241884": "SP",   # Itatiba
    "7241942": "PR",   # Curitiba
    "7242202": "RJ",   # Saquarema
    "7242218": "RJ",   # Duque de Caxias
    "7242262": "SP",   # Santos
    "7242313": "PR",   # Telemaco Borba
    "7242359": "ES",   # Santa Maria de Jetiba
    "7242467": "PR",   # Curitiba PR
    "7242469": "SP",   # Ribeirao Preto
    "7242529": "ES",   # Vitoria
    "7242546": "RJ",   # Petropolis
    "7242558": "RS",   # Camaqua
    "7242593": "PI",   # Teresina
    "7242607": "SC",   # Joinville
    "7242645": "RJ",   # Nova Friburgo
    "7242687": "RS",   # Porto Alegre
    "7242717": "RJ",   # Sao Goncalo
    "7242745": "SP",   # Jacarei-SP
    "7242771": "SP",   # Jaboticabal
    "7242783": "MG",   # Uberaba
    "7242794": "MG",   # Formiga
    "7242859": "DF",   # Brasilia
    "7242866": "GO",   # Goiania-Go
    "7242871": "ES",   # Cachoeiro de Itapemirim
    "7243052": "RS",   # Porto Alegre
    "7243071": "RS",   # Canoas
    "7243073": "RS",   # Viamao
    "7243265": "SP",   # Sao Paulo SP
    "7243353": "RJ",   # Angra dos Reis RJ
    "7243387": "SP",   # Perus Sao Paulo SP
    "7243430": "MA",   # Timon
    "7243460": "CE",   # Crato CE
    "7243479": "SP",   # Tatui
    "7243613": "RJ",   # Niteroi
    "7244008": "MG",   # Belo Horizonte
    "7244320": "SE",   # Aracaju
    "7244328": "MG",   # Itabira
    "7244370": "SP",   # Mongagua
    "7244426": "BA",   # Salvador
    "7244527": "SP",   # Rosana SP
    "7244547": "PI",   # Teresina
    "7244596": "SP",   # Osasco SP
    "7244641": "SP",   # Porto Feliz
    "7244656": "SC",   # Itajai
    "7244738": "MG",   # Contagem
    "7244831": "PR",   # Marumbi
    "7244844": "SP",   # Sao Paulo SP
    "7244859": "SP",   # Santa Barbara d'Oeste
    "7244910": "SP",   # Americana SP
    "7244941": "PB",   # Joao Pessoa
    "7244942": "SP",   # Monteiro Lobato Sp
    "7245166": "SP",   # Sao Jose dos Campos
    "7245221": "RS",   # Itaara
    "7245266": "SP",   # Nova Odessa Sp
    "7245301": "RN",   # Caico
    "1106221": "California",  # W6FMG - American Canyon/CA (pais corrigido p/ USA)
    "1106278": "California",  # W6FMG - American Canyon/CA (pais corrigido p/ USA)
    "7245382": "SC",   # Florianopolis
    "7245525": "SP",   # Lorena
    "7245566": "SP",   # Capivari Sp
    "7245706": "SP",   # Bauru
    "7245725": "SP",   # Santo Andre
    "7245929": "MG",   # Timoteo Vale do Aco
    "7246012": "SE",   # Aracaju
    "7246055": "RJ",   # Miguel Pereira
    "7247002": "RS",   # Rio Grande
    "7247005": "CE",   # Cear(a)
    "7247006": "RS",   # Rio Grande
    "7247008": "RN",   # Natal
    "7249004": "PE",   # Garanhuns
}

def uf_por_indicativo(callsign):
    """Deriva a UF a partir do indicativo brasileiro (prefixo+digito, e faixa de
    sufixo para PU), conforme distribuicao oficial Anatel.
    Retorna '' se nao for indicativo BR reconhecivel."""
    c = callsign.strip().upper()
    m = re.match(r"^(P[PQRSTVWXY]|P[UY]|Z[VWXYZ])(\d)([A-Z]*)", c)
    if not m:
        return ""
    pre, dig, suf = m.group(1), m.group(2), m.group(3)
    first = suf[0] if suf else ""

    # PU: faixa de sufixo define a UF em digitos ambiguos
    if pre == "PU":
        if dig == "1":   # ES: AAA-IZZ ; RJ: JAA-YZZ
            return "ES" if first and first <= "I" else "RJ"
        if dig == "2":   # DF A-E ; GO F ; TO G-I ; SP K-Y
            if first <= "E": return "DF"
            if first in ("F",): return "GO"
            if first in ("G","H","I"): return "TO"
            return "SP"
        if dig == "5":   # SC AAA-LZZ ; PR MAA-YZZ
            return "SC" if first and first <= "L" else "PR"
        if dig == "6":   # SE AAA-IZZ ; BA JAA-YZZ
            return "SE" if first and first <= "I" else "BA"
        if dig == "7":   # AL A-D ; PB E-H ; RN I-L ; CE M-P ; PE R-Y
            if first <= "D": return "AL"
            if first <= "H": return "PB"
            if first <= "L": return "RN"
            if first <= "P": return "CE"
            return "PE"
        if dig == "8":   # AC J-L ; AM A-C ; AP G-I ; MA M-O ; PA W-Y ; PI P-S ; RO D-F ; RR T-V
            tbl8 = {"A":"AM","B":"AM","C":"AM","D":"RO","E":"RO","F":"RO",
                    "G":"AP","H":"AP","I":"AP","J":"AC","K":"AC","L":"AC",
                    "M":"MA","N":"MA","O":"MA","P":"PI","Q":"PI","R":"PI","S":"PI",
                    "T":"RR","U":"RR","V":"RR","W":"PA","X":"PA","Y":"PA"}
            return tbl8.get(first, "")
        # digitos nao ambiguos para PU
        return {"3":"RS","4":"MG","9":"MS","0":""}.get(dig, "")

    # Prefixos de letra fixa (classe A/B) -> UF direta por (letra-inicial-grupo, digito)
    # Mapa por prefixo+digito
    fixo = {
        "PP1":"ES","PY1":"RJ",
        "PY2":"SP","PT2":"DF","PP2":"GO","PQ2":"TO",
        "PY3":"RS","PY4":"MG",
        "PP5":"SC","PY5":"PR",
        "PY6":"BA","PP6":"SE",
        "PY7":"PE","PR7":"PB","PS7":"RN","PT7":"CE","PP7":"AL",
        "PY8":"PA","PP8":"AM","PR8":"MA","PS8":"PI","PT8":"AC","PV8":"RR","PW8":"RO","PQ8":"AP",
        "PT9":"MS","PY9":"MT",
    }
    key = pre + dig
    if key in fixo:
        return fixo[key]
    # fallback por digito (classe A generica PP/PQ/PR/PS/PT/PV/PW/PX com AA-ZZ):
    # ES=1 (PP1..PX1), demais ja cobertos acima; usa PY-equivalente quando possivel
    gen = {"1":"", "3":"RS", "4":"MG"}
    return gen.get(dig, "")


def comunidade_por_indicativo_es(callsign):
    """Espanha: deriva a comunidade autonoma a partir do distrito (digito do
    indicativo EA/EB/EC/ED/EE/EF/EG/EH + digito). Preenche APENAS os distritos
    que mapeiam a uma unica comunidade (3,6,7,8,9); os ambiguos (1,2,4,5)
    retornam '' para nao inventar dado. Distrito oficial (URE)."""
    c = callsign.strip().upper()
    m = re.match(r"^E[A-H](\d)", c)
    if not m:
        return ""
    dig = m.group(1)
    unicos = {
        "3": "Cataluna",
        "6": "Islas Baleares",
        "7": "Andalucia",
        "8": "Canarias",
        "9": "Ceuta y Melilla",
    }
    return unicos.get(dig, "")


def provincia_por_indicativo_ca(callsign):
    """Canada: VE/VA + digito -> provincia (apenas digitos que mapeiam a uma
    unica provincia). 1=NS 2=QC 3=ON 4=MB 5=SK 6=AB 7=BC. Demais ('' )."""
    c = callsign.strip().upper()
    m = re.match(r"^V[AE](\d)", c)
    if not m:
        return ""
    unicos = {
        "1": "Nova Scotia", "2": "Quebec", "3": "Ontario", "4": "Manitoba",
        "5": "Saskatchewan", "6": "Alberta", "7": "British Columbia",
    }
    return unicos.get(m.group(1), "")


def provincia_por_indicativo_ar(callsign):
    """Argentina: a PROVINCIA e dada pela 1a letra do SUFIXO (apos LU#/LW#),
    nao pelo digito. Todas as letras mapeiam a uma unica provincia; as faixas
    G e X dependem da 2a letra do sufixo.
    Fonte: https://en.wikipedia.org/wiki/Call_signs_in_Argentina"""
    c = callsign.strip().upper()
    m = re.match(r"^(?:LU|LW|L[2-9]|AY|AZ)\d([A-Z])([A-Z]?)", c)
    if not m:
        return ""
    a, b = m.group(1), m.group(2)
    simples = {
        "A":"Buenos Aires","B":"Buenos Aires","C":"Buenos Aires",
        "D":"Buenos Aires","E":"Buenos Aires","F":"Santa Fe","H":"Cordoba","I":"Misiones",
        "J":"Entre Rios","K":"Tucuman","L":"Corrientes","M":"Mendoza","N":"Santiago del Estero",
        "O":"Salta","P":"San Juan","Q":"San Luis","R":"Catamarca","S":"La Rioja","T":"Jujuy",
        "U":"La Pampa","V":"Rio Negro","W":"Chubut","Y":"Neuquen","Z":"Antarctica",
    }
    if a == "G":   # GA-GO=Chaco ; GP-GZ=Formosa
        if b and b <= "O": return "Chaco"
        if b: return "Formosa"
        return ""
    if a == "X":   # XA-XO=Santa Cruz ; XP-XZ=Tierra del Fuego
        if b and b <= "O": return "Santa Cruz"
        if b: return "Tierra del Fuego"
        return ""
    return simples.get(a, "")


def regiao_por_indicativo_it(callsign):
    """Italia: prefixo I/IK/IZ/IW/IU... + digito -> regiao. Preenche APENAS os
    casos que mapeiam a uma unica regiao. Fonte: distribuicao ARI/ministero.
    Digitos unicos: 2=Lombardy 3=Veneto 4=Emilia-Romagna 5=Tuscany 9=Sicily.
    Prefixos especiais unicos: IX1=Aosta IN3=Trentino-Alto Adige
    IV3=Friuli-Venezia Giulia IS0=Sardinia.
    Ambiguos (1,6,7,8,0) -> '' ."""
    c = callsign.strip().upper()
    # prefixos especiais (checar antes do digito generico)
    especiais = {
        "IX1": "Aosta",
        "IN3": "Trentino-Alto Adige",
        "IV3": "Friuli-Venezia Giulia",
        "IS0": "Sardinia",
    }
    for pre, reg in especiais.items():
        if c.startswith(pre):
            return reg
    m = re.match(r"^I[A-Z]?(\d)", c)
    if not m:
        return ""
    unicos = {
        "2": "Lombardy", "3": "Veneto", "4": "Emilia-Romagna",
        "5": "Tuscany", "9": "Sicily",
    }
    return unicos.get(m.group(1), "")

total = 0
# Override pontual de FIRST_NAME por RADIO_ID (nome incorreto/abreviado no texto)
NOME_OVERRIDE = {
    "7489001": "Eduilio",   # CX7SS - texto trazia "E. Eugenio"
    "7244645": "Jeferson",  # PY2JEF - texto trazia "Cheff-Jeff"
    "7244569": "Jose",      # PU8PAV - texto trazia "Nonejose Afonso"
    "7240391": "Luciano",   # PU4LCD - texto trazia "Luciano-Cec"
    "7245148": "Erivelton", # PU2UNQ - nome era o proprio callsign
    "7245282": "",          # PU6LTT - deixar em branco
    "7241669": "Radioescotismo",  # PR8GEN - 13o Grupo Escoteiro do Mar
    "7242530": "Radioescotismo",  # ZW8JN - Equipe Nacional de Radioescotismo
    "7242383": "Neidir",    # PY1BSK - era "N P"
    "7246767": "",          # PU8ARA - nome era o proprio callsign
}

# Override pontual de COUNTRY por RADIO_ID (pais digitado errado no texto;
# indicativo + cidade concordam com o pais correto).
PAIS_OVERRIDE = {
    "1106221": "USA",   # W6FMG - American Canyon/CA; texto trazia Philippines
    "1106278": "USA",   # W6FMG - American Canyon/CA; texto trazia Philippines
}

# Override pontual da 5a coluna final (qualquer pais), para casos especiais em que
# se quer mostrar a cidade (ou outro valor) em vez da regiao padrao.
COL5_OVERRIDE = {
    "2223002": "Trieste",   # IV3DVE - mostrar a cidade em vez da regiao
    "7240838": "Campinas-SP",   # PU2PXW - texto "Sao Paulo-Campinas-SP" (2 cidades); fica Campinas
}

PREPOSICOES_BR = {"de", "da", "do", "das", "dos", "e"}

# UFs validas (siglas) para reconhecer "cidade SP" no fim do texto brasileiro
UF_SIGLAS = {
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB",
    "PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO",
}
# UF -> nome do estado por extenso (ASCII). Usado para aproveitar o espaco do
# display quando o contato BR tem SO a UF (sem cidade). So e aplicado se o nome
# couber em 20 chars no display (nome + ",BR"); senao mantem a sigla.
UF_NOME = {
    "AC":"Acre","AL":"Alagoas","AP":"Amapa","AM":"Amazonas","BA":"Bahia",
    "CE":"Ceara","DF":"Distrito Federal","ES":"Espirito Santo","GO":"Goias",
    "MA":"Maranhao","MT":"Mato Grosso","MS":"Mato Grosso do Sul","MG":"Minas Gerais",
    "PA":"Para","PB":"Paraiba","PR":"Parana","PE":"Pernambuco","PI":"Piaui",
    "RJ":"Rio de Janeiro","RN":"Rio Grande do Norte","RS":"Rio Grande do Sul",
    "RO":"Rondonia","RR":"Roraima","SC":"Santa Catarina","SP":"Sao Paulo",
    "SE":"Sergipe","TO":"Tocantins",
}
# nomes de estado por extenso -> para remover do fim (sem acento, minusculo)
BR_NOMES_ESTADO = set(BR_UF.keys())

# abreviacoes especiais de cidade (tem prioridade sobre a regra geral)
CIDADE_ESPECIAL = {
    "florianopolis": "Fpolis",
    "pindamonhangaba": "Pinda",
    "itaquaquecetuba": "Itaqua",
}

# Override pontual de CITY por RADIO_ID (texto de origem truncado/errado)
CITY_OVERRIDE = {
    # SP/RJ enriquecido via QRZ (apenas cidades limpas, revisadas)
    "7240137": "Sorocaba",
    "7240149": "Resende",
    "7240229": "Carapicuiba",
    "7240260": "Itanhaem",
    "7240507": "C.Frio",
    "7241146": "Jacarei",
    "7241199": "P.D'oeste",
    "7241206": "P.D'oeste",
    "7241207": "Jundiai",
    "7241216": "Jundiai",
    "7241228": "Guararema",
    "7241267": "Ibiuna",
    "7241284": "Paraty",
    "7241324": "S.Amaro",
    "7241352": "S.Isabel",
    "7241354": "S.Isabel",
    "7241385": "P.Grande",
    "7241407": "M.Cruzes",
    "7241543": "Mairinque",
    "7241941": "Santos",
    "7242076": "Indaiatuba",
    "7242080": "Itapevi",
    "7242420": "Bebedouro",
    "7242588": "Lins",
    "7242734": "Atibaia",
    "7243137": "Santos",
    "7243261": "R.Preto",
    "7243415": "Sumare",
    "7243772": "Araraquara",
    "7244357": "Santos",
    "7244387": "Santos",
    "7244882": "Piracicaba",
    "7244895": "Campinas",
    "7244908": "Guarulhos",
    "7245688": "P.Prudente",
    "7245710": "Goiania",
    "7245748": "Caraguatatuba",
    "7246259": "Botucatu",
    "7246412": "A.Lindoia",
    "7246433": "Taubate",
    "7246618": "Boituva",
    # RJ enriquecido via API radioid (cidade preenchida automaticamente)
    "7241517": "R.Janeiro",
    "7240003": "R.Janeiro",
    "7240004": "R.Janeiro",
    "7240006": "R.Janeiro",
    "7240007": "R.Janeiro",
    "7240008": "R.Janeiro",
    "7240010": "R.Janeiro",
    "7240011": "R.Janeiro",
    "7240012": "R.Janeiro",
    "7240015": "R.Janeiro",
    "7240031": "R.Janeiro",
    "7240066": "R.Janeiro",
    "7240096": "R.Janeiro",
    "7240097": "R.Janeiro",
    "7240120": "R.Janeiro",
    "7240127": "R.Janeiro",
    "7240140": "R.Janeiro",
    "7240148": "R.Janeiro",
    "7240173": "R.Janeiro",
    "7240222": "R.Janeiro",
    "7240247": "R.Janeiro",
    "7240254": "R.Janeiro",
    "7240255": "R.Janeiro",
    "7240306": "R.Janeiro",
    "7240307": "R.Janeiro",
    "7240325": "R.Janeiro",
    "7240355": "R.Janeiro",
    "7240385": "R.Janeiro",
    "7240456": "R.Janeiro",
    "7240475": "R.Janeiro",
    "7240477": "R.Janeiro",
    "7240500": "R.Janeiro",
    "7240550": "R.Janeiro",
    "7240752": "R.Janeiro",
    "7240773": "R.Janeiro",
    "7240778": "R.Janeiro",
    "7240784": "R.Janeiro",
    "7241001": "R.Janeiro",
    "7241002": "R.Janeiro",
    "7241003": "R.Janeiro",
    "7241038": "R.Janeiro",
    "7241043": "R.Janeiro",
    "7241047": "R.Janeiro",
    "7241048": "R.Janeiro",
    "7241049": "R.Janeiro",
    "7241051": "R.Janeiro",
    "7241052": "R.Janeiro",
    "7241053": "R.Janeiro",
    "7241054": "R.Janeiro",
    "7241063": "R.Janeiro",
    "7241064": "R.Janeiro",
    "7241066": "R.Janeiro",
    "7241069": "R.Janeiro",
    "7241071": "R.Janeiro",
    "7241072": "R.Janeiro",
    "7241116": "R.Janeiro",
    "7241118": "R.Janeiro",
    "7241309": "R.Janeiro",
    "7241430": "R.Janeiro",
    "7241436": "R.Janeiro",
    "7241437": "R.Janeiro",
    "7241476": "R.Janeiro",
    "7241477": "R.Janeiro",
    "7241500": "R.Janeiro",
    "7241501": "R.Janeiro",
    "7241517": "R.Janeiro",
    "7244525": "Recife",
    "7241534": "R.Janeiro",
    "7241609": "R.Janeiro",
    "7241613": "R.Janeiro",
    "7241619": "R.Janeiro",
    "7241633": "R.Janeiro",
    "7241634": "R.Janeiro",
    "7241658": "R.Janeiro",
    "7241678": "R.Janeiro",
    "7241697": "R.Janeiro",
    "7241708": "R.Janeiro",
    "7241715": "R.Janeiro",
    "7241781": "R.Janeiro",
    "7241807": "R.Janeiro Rj",
    "7241872": "R.Janeiro",
    "7241919": "R.Janeiro",
    "7241922": "R.Janeiro",
    "7241923": "R.Janeiro",
    "7241933": "R.Janeiro",
    "7242180": "R.Janeiro",
    "7242181": "R.Janeiro",
    "7242186": "R.Janeiro",
    "7242200": "R.Janeiro",
    "7242216": "R.Janeiro",
    "7242217": "R.Janeiro",
    "7242275": "R.Janeiro",
    "7242285": "R.Janeiro",
    "7242302": "R.Janeiro",
    "7242321": "R.Janeiro",
    "7242343": "R.Janeiro",
    "7242362": "R.Janeiro",
    "7242430": "R.Janeiro",
    "7242438": "R.Janeiro",
    "7242440": "R.Janeiro",
    "7242512": "R.Janeiro",
    "7242514": "R.Janeiro",
    "7242521": "R.Janeiro",
    "7242527": "R.Janeiro",
    "7242543": "R.Janeiro",
    "7242576": "R.Janeiro",
    "7242601": "R.Janeiro",
    "7242659": "R.Janeiro",
    "7242665": "R.Janeiro",
    "7242677": "R.Janeiro",
    "7242680": "R.Janeiro",
    "7242685": "R.Janeiro",
    "7242688": "R.Janeiro",
    "7242692": "R.Janeiro",
    "7242710": "R.Janeiro",
    "7242720": "R.Janeiro",
    "7242748": "R.Janeiro",
    "7242815": "R.Janeiro",
    "7242954": "R.Janeiro",
    "7242963": "R.Janeiro",
    "7243120": "R.Janeiro",
    "7243211": "R.Janeiro",
    "7243251": "R.Janeiro",
    "7243266": "R.Janeiro",
    "7243328": "R.Janeiro",
    "7243356": "R.Janeiro",
    "7243470": "R.Janeiro",
    "7243481": "R.Janeiro",
    "7243487": "R.Janeiro",
    "7243538": "R.Janeiro",
    "7243541": "R.Janeiro",
    "7243552": "R.Janeiro",
    "7243581": "R.Janeiro",
    "7243608": "R.Janeiro",
    "7243671": "R.Janeiro",
    "7243697": "R.Janeiro",
    "7243709": "R.Janeiro",
    "7243752": "R.Janeiro",
    "7243801": "R.Janeiro",
    "7243807": "R.Janeiro",
    "7243910": "R.Janeiro",
    "7243922": "R.Janeiro",
    "7244039": "R.Janeiro",
    "7244128": "R.Janeiro",
    "7244136": "R.Janeiro",
    "7244150": "R.Janeiro",
    "7244173": "R.Janeiro",
    "7244194": "R.Janeiro",
    "7244208": "R.Janeiro",
    "7244210": "R.Janeiro",
    "7244268": "R.Janeiro",
    "7244303": "R.Janeiro",
    "7244325": "R.Janeiro",
    "7244330": "R.Janeiro",
    "7244434": "R.Janeiro",
    "7244448": "R.Janeiro",
    "7244458": "R.Janeiro",
    "7244496": "R.Janeiro",
    "7244507": "R.Janeiro",
    "7244550": "R.Janeiro",
    "7244562": "R.Janeiro",
    "7244572": "R.Janeiro",
    "7244601": "R.Janeiro",
    "7244664": "R.Janeiro Rj",
    "7244677": "R.Janeiro",
    "7244693": "R.Janeiro",
    "7244785": "R.Janeiro",
    "7244792": "R.Janeiro",
    "7244806": "R.Janeiro Rj",
    "7244825": "R.Janeiro",
    "7244838": "R.Janeiro",
    "7244865": "R.Janeiro",
    "7244867": "R.Janeiro",
    "7244876": "R.Janeiro",
    "7244885": "R.Janeiro",
    "7244920": "R.Janeiro",
    "7244959": "R.Janeiro",
    "7244981": "R.Janeiro",
    "7244997": "R.Janeiro",
    "7245104": "R.Janeiro",
    "7245109": "R.Janeiro",
    "7245145": "R.Janeiro",
    "7245167": "R.Janeiro",
    "7245171": "R.Janeiro",
    "7245226": "R.Janeiro Rj",
    "7245229": "R.Janeiro",
    "7245252": "R.Janeiro",
    "7245261": "R.Janeiro",
    "7245324": "R.Janeiro",
    "7245349": "R.Janeiro",
    "7245351": "R.Janeiro",
    "7245362": "R.Janeiro",
    "7245413": "R.Janeiro",
    "7245476": "R.Janeiro",
    "7245495": "R.Janeiro",
    "7245560": "R.Janeiro",
    "7245580": "R.Janeiro",
    "7245609": "R.Janeiro",
    "7245651": "R.Janeiro",
    "7245677": "R.Janeiro",
    "7245682": "R.Janeiro",
    "7245689": "R.Janeiro",
    "7245772": "R.Janeiro",
    "7245778": "R.Janeiro",
    "7245794": "R.Janeiro",
    "7245821": "R.Janeiro",
    "7245864": "R.Janeiro",
    "7245867": "R.Janeiro",
    "7245868": "R.Janeiro",
    "7245903": "R.Janeiro",
    "7246208": "R.Janeiro",
    "7246228": "R.Janeiro",
    "7246246": "R.Janeiro",
    "7246249": "R.Janeiro",
    "7246275": "R.Janeiro",
    "7246301": "R.Janeiro",
    "7246319": "R.Janeiro",
    "7246322": "R.Janeiro",
    "7246323": "R.Janeiro",
    "7246327": "R.Janeiro",
    "7246336": "R.Janeiro",
    "7246339": "R.Janeiro",
    "7246395": "R.Janeiro",
    "7246396": "R.Janeiro",
    "7246402": "R.Janeiro",
    "7246417": "R.Janeiro",
    "7246470": "R.Janeiro",
    "7246523": "R.Janeiro",
    "7246531": "R.Janeiro",
    "7246542": "R.Janeiro",
    "7246545": "R.Janeiro",
    "7246562": "R.Janeiro",
    "7246586": "R.Janeiro",
    "7246589": "R.Janeiro",
    "7246665": "R.Janeiro",
    "7246670": "R.Janeiro",
    "7246694": "R.Janeiro",
    "7246701": "R.Janeiro",
    "7246702": "R.Janeiro",
    "7246722": "R.Janeiro",
    "7246729": "R.Janeiro",
    "7246754": "R.Janeiro",
    "7246785": "R.Janeiro",
    "7246787": "R.Janeiro",
    "7246815": "R.Janeiro",
    "7246836": "R.Janeiro",
    "7246858": "R.Janeiro",
    "7246869": "R.Janeiro",
    "7246876": "R.Janeiro",
    "7246886": "R.Janeiro",
    "7246908": "R.Janeiro",
    "7246911": "R.Janeiro",
    "7246973": "R.Janeiro",
    "7247033": "R.Janeiro",
    "7247043": "R.Janeiro",
    "7247089": "R.Janeiro",
    "7247093": "R.Janeiro",
    "7247116": "R.Janeiro",
    "7240001": "S.F.Sul",   # PP5VX - texto trazia "Sao Francisco do Su" (truncado)
    # correcoes manuais (base out/2026): cidade correta; o script junta " - UF"
    "7244567": "P. do Lumiar",  # PR8ADN (Paco do Lumiar/MA) - script nao removeu "Maranhao"
    "7244519": "Linhares",      # PU1ABJ - texto bagunçado "Lagoa do Meio Linhares"
    "7244520": "Jardim Jaragua",# PU2RZT - script abreviou demais
    "7244571": "Tiradentes",    # PU2ODQ - texto so tinha "Sp"
    "7244584": "Frei Paulo",    # PP6PE - script nao removeu "Sergipe"
    "7244592": "Belford Roxo",  # PU1STZ - texto so tinha "RJ"
    "7244497": "Vitoria",       # PP1JL - texto so tinha "Espirito Santo"
    "7244465": "V. Valerio",    # PU1AHI - texto bagunçado (Vila Valerio)
    "7244641": "P.Feliz",       # PU2SPU - "CITY PORTO FELIZ"
    "7244569": "",              # PU8PAV - texto so tinha estado (PI); fica so a UF
    "7244570": "Teresina",      # PU8PBR - texto "Teresina - PI"
    "7245492": "Vila Velha",    # PP1HT - texto era endereco (Ed Narcizo... Praia de Itaparica Vila Velha)
    # correcoes de endereco->cidade (base out/2026, revisadas manualmente)
    "7240196": "Antonio Prado",         # PU3ELD
    "7240323": "Volta Redonda",         # PU1LCR
    "7241265": "Praia Grande",          # PU2KBZ
    "7241266": "Praia Grande",          # PU2KBZ
    "7241303": "S.Mateus Sul",       # PU5RGM
    "7241710": "Vila Velha",            # PP1AR
    "7241797": "B.Horizonte",           # PU4LSB (Belo Horizonte)
    "7242469": "R.Preto",               # PU2XSX (Ribeirao Preto)
    "7242593": "Teresina",              # PU8PSF
    "7242629": "B.Mansa",               # PU1KSS (Barra Mansa)
    "7243090": "Botucatu",              # PY2PJA
    "7243500": "Socorro",               # PU6ASA
    "7243556": "Guarulhos",             # PU2PEZ
    "7244260": "S.G.Rio Abaixo",    # PU4EDU (Sao Goncalo do Rio Abaixo)
    "7244381": "Pouso Alegre",          # PY4YZZ
    "7244903": "Sorocaba",              # PY2RTD
    "7245082": "Pinhais",               # PY5RH
    "7245545": "Chapeco",               # PU5FCP
    "7245581": "Niteroi",               # PY1NBL
    "7245632": "Itaguai",               # PY1SFF
    "7245709": "Ponte Nova",            # PU4MOS
    "7245717": "S.Capanema",        # PU4GAA (Serra do Capanema)
    "7245869": "Pindamonhangaba",       # PY2KWG
    "7245929": "Vale Aco",          # PY4PF
    "7246302": "Araraquara",            # PY2ARA
    "7246357": "Miguel Pereira",        # PU1NEN
    "7246680": "Japeri",                # PU1JVH
    "7247075": "Brasilia",              # PU2EFR
    # 2a rodada de revisao (cidades >20 chars): remove bairro / abrevia mais
    "7240043": "A.S.Barbara",       # Aguas de Santa Barbara
    "7240380": "Chateaubriand",   # Assis Chateaubriand (encurtado p/ caber no display)
    "7240572": "M.Cruzes",          # Mogi das Cruzes
    "7240939": "Fpolis",            # Armacao (bairro) + Florianopolis
    "7240997": "Fortaleza",         # Cidade dos Funcionarios (bairro) + Fortaleza
    "7241454": "R.Janeiro",         # Jacarepagua (bairro)
    "7241456": "R.Janeiro",         # Jacarepagua (bairro)
    "7242317": "S.R.P.Quatro",      # Santa Rita do Passa Quatro
    "7242590": "S.R.P.Quatro",      # Santa Rita do Passa Quatro
    "7242490": "Mesquita",          # Banco de Areia (bairro) + Mesquita
    "7242495": "R.Janeiro",         # Madureira (bairro)
    "7242794": "Formiga",           # Nossa Senhora de Lourdes (bairro) + Formiga
    "7243508": "V.Paulista",        # Varzea Paulista
    "7243631": "R.Pires",           # Parque das Fontes (bairro) + Ribeirao Pires
    "7243646": "S.J.R.Preto",       # Sao Jose do Rio Preto
    "7243791": "S.J.Meriti",        # Vilar dos Teles (bairro) + Sao Joao de Meriti
    "7243821": "A.Reis",            # Japuiba (bairro) + Angra dos Reis
    "7244088": "R.Neves",           # Ribeirao das Neves
    "7244089": "R.Neves",           # Ribeirao das Neves
    "7244156": "L.Mangabeira",      # Lavras da Mangabeira (+ distrito removido)
    "7244834": "C.S.Agostinho",     # Cabo de Santo Agostinho
    "7245201": "R.Janeiro",         # Centro (bairro)
    "7245288": "Ibirite",           # Durval de Barros (bairro) + Ibirite
    "7245869": "Pinda",             # Pindamonhangaba (+ lixo Zip Code removido)
    "7245955": "L.N.Senhora",       # Livramento de Nossa Senhora
    "7246520": "",                  # "Dos Santos Pinheiro Filho" = nome, nao cidade
    "7242530": "",                  # "Equipe Nacional de Radioescotismo" = entidade
    # 3a rodada: bairro - cidade (fica a cidade, remove bairro)
    "7240679": "",                  # Pq Silva Azevedo - S (bairro, cidade=lixo)
    "7241204": "",                  # idem
    "7240921": "Itajai",            # Bairro: Dom Bosco - Itajai
    "7241932": "Carapicuiba",       # Vila Menk - Carapicuiba
    "7242426": "S.Paulo",           # Bairro Jaragua - Sao Paulo
    "7242607": "Joinville",         # Bairro: Bom retiro - Joinville
    "7242657": "S.L.Mata",          # Tiuma - Sao Lourenco da Mata
    "7242764": "D.Caxias",          # Santa Cruz da Serra - Duque de Caxias
    # 4a rodada: cidades que ficaram estranhas/erradas (revisao de legibilidade)
    "7241380": "S.B.Doeste", "7241787": "S.B.Doeste", "7243713": "S.B.Doeste",
    "7245193": "S.B.Doeste", "7246639": "S.B.Doeste", "7246641": "S.B.Doeste",
    "7247150": "S.B.Doeste", "7246254": "S.B.Doeste", "7242008": "S.B.Doeste",
    "7242014": "S.B.Doeste",        # unifica Santa Barbara d'Oeste
    "7241195": "S.B.Campo", "7241196": "S.B.Campo",
    "7242172": "S.B.Campo", "7242173": "S.B.Campo",   # Sao Bernardo do Campo (truncado)
    "7244061": "B.Horizonte", "7244063": "B.Horizonte",  # Luxemburgo (bairro) + BH
    "7244525": "",                  # era email (augustobarbosams gmail com)
    "7240302": "",                  # Milton Keynes UK (nao e cidade BR; sem cidade BR)
    "7244051": "Contagem",          # "Contagem Minas Ger"
    "7243548": "B.Horizonte",       # "belo hori zonte"
    "7242839": "",                  # "Southern coast of RJ" (texto ingles)
    "7240579": "R.Pardo",           # "7o Distrito Rio Pardo"
    "7241262": "S.Paulo", "7241849": "S.Paulo", "7245971": "S.Paulo",
    "7246454": "S.Paulo", "7241740": "S.Paulo",   # Sao Paulo Capital/Tatuape
    "7245015": "Curitiba",          # "Curitiba Boa Vista" (bairro)
    "7242444": "B.Horizonte",       # "BELO HORIZONTE -MG-BRAZIL"
    "7244466": "P.Grande",          # "- Praia Grande"
    "7241084": "S.J.Rio Pardo",     # Sao Jose do Rio Pardo (truncado)
    "7242096": "S.J.Rio Preto",     # Sao Jose do Rio Preto (truncado)
    "7242091": "V.G.Paulista",      # Vargem Grande Paulista (truncado)
    # 5a rodada: bairro no inicio -> fica a cidade real
    "7240208": "S.Paulo",       # Jardim Rincao -Jaragua / Sao Paulo
    "7240227": "Antonio Carlos",# Campolide Antonio Carlos
    "7240840": "Itupeva",       # JD Primavera Itupeva
    "7240871": "P.Grossa",      # Oficinas - Ponta Grossa
    "7241078": "Curitiba",      # Bairro Tingui Curitiba
    "7241147": "S.Judas",       # Sao Judas (bairro SP) - texto truncado
    "7241506": "Mongagua",      # Florida Mirim Mongagua
    "7241589": "B.Horizonte",   # Planalto Belo Horizonte
    "7241884": "Itatiba",       # Jd Nacoes Itatiba
    "7241996": "P.Alegre",      # Porto Alegre Ipanema
    "7242449": "Cabreuva",      # Bairro Jacare Cabreuva
    "7242482": "Araras",        # Olivia Park Araras
    "7242916": "J.Pessoa",      # Bessa Joao Pessoa
    "7243079": "Macae",         # (STATE forcado p/ RJ no STATE_OVERRIDE)
    "7243106": "Muniz Freire",  # Centro Muniz Freire
    "7243194": "Itapemirim",    # Itapemirim Praia de Itaoca
    "7243559": "Uba",           # Bairro Industrial Uba
    "7244219": "Maceio",        # Bairro Mangabeiras Maceio
    "7244346": "N.Lima",        # Centro Nova Lima
    "7244445": "Maracanau",     # Jereissati I Maracanau
    "7244535": "Recife",        # Boa Viagem Recife
    "7244623": "Cacador",       # Bairro Sao Cristovao -> Cacador/SC
    "7244774": "Jacarei",       # Parque Itamaraty Jacarei
    "7244854": "Ipatinga",      # Bairro Cana Ipatinga
    "7245436": "Guarulhos",     # Jardim Girassol Guarulhos
    "7245616": "J.Pessoa",      # Torre Joao Pessoa
    "7245776": "Palhoca",       # Jardim Eldorado Palhoca
    "7246019": "Aracaju",       # Bairro Luzia Aracaju
    "7246684": "Limeira",       # Jardim Caieira Limeira
    "7246718": "Joinville",     # Bairro Bucarein Joinville
    "7247012": "Santos",        # Bairro Aparecida Santos
    "7247060": "Salvador",      # Salvador Bairro Ribeira
    # 6a rodada: hifen/ponto sobrando e dado errado
    "7241442": "Guaratuba",     # era "Guaratuba--PR"
    # cidades SC informadas manualmente (texto so trazia "Santa Catarina")
    "7246544": "Palhoca",       # PP5NB
    "7246378": "Jaragua do Sul",# PU5EDF
    "7245323": "Penha",         # PU5BRO
    "7245061": "Itajai",        # PU5GYN
    "7244804": "Fpolis",        # PU5LMD
    "7244726": "T.Central",     # PU5FLP
    "7244367": "Penha",         # PU5CEK
    "7243962": "B.Camboriu",    # PP5FT
    "7241117": "Itajai",        # PP5CG
    "7240694": "Laguna",        # PU5ATS
    "7240693": "Laguna",        # PU5ATS (mesmo operador/callsign do 7240694)
    # cidades informadas manualmente (estados com poucos faltantes)
    "7242669": "Maceio",        # PU7ARM / AL
    "7241874": "B.Jesus",       # PP2BZ / GO (Bom Jesus)
    "7244189": "Tres Lagoas",   # PT9SS / MS
    "7241111": "Alta Floresta", # PY9BKW / MT
    "7243667": "Pombal",        # PU7EIM / PB
    "7249045": "Monteiro",      # PU7FFF / PB
    "7249046": "Monteiro",      # PU7FFF / PB (mesmo operador)
    "7241821": "Teresina",      # PU8SBJ / PI
    "7243722": "Macau",         # PU7KSA / RN
    "7244190": "Natal",         # PS7PN / RN
    "7245325": "Aracaju",       # PU6BMB / SE
    "7246007": "N.S.Socorro",   # PP6CFN / SE
    "7245912": "Araguaina",     # PQ2AT / TO
    "7245913": "Araguaina",     # PQ2AT / TO (mesmo operador)
    # BA
    "7240308": "Salvador", "7243486": "Salvador", "7243672": "Salvador",
    "7244651": "Salvador", "7245504": "M.Chapeu",
    # CE
    "7241411": "Fortaleza", "7242364": "Fortaleza", "7243574": "Fortaleza",
    # DF - Distrito Federal nao tem municipios; tudo Brasilia
    "7241826": "Brasilia", "7242977": "Brasilia", "7245888": "Brasilia",
    "7245975": "Brasilia", "7246355": "Brasilia", "7246386": "Brasilia",
    # ES
    "7241586": "Vitoria", "7241592": "V.Velha", "7241593": "V.Velha",
    "7243146": "C.Itapemirim", "7245265": "Serra",
    # MA
    "7240944": "S.Luiz", "7240968": "S.Luiz", "7240983": "S.Luiz", "7245643": "S.Luiz",
    # PE
    "7240436": "Olinda", "7240894": "Paulista", "7243283": "Pesqueira",
    "7243601": "Limoeiro", "7243793": "Camaru", "7244525": "Recife", "7245311": "Caruaru",
    "7244475": "S.Paulo",   # PU2RJF - na verdade SP (UF corrigida abaixo)
    # MG/PR/RS informados manualmente
    "7240105": "Ijui", "7240106": "Ijui",
    "7240109": "Varginha", "7240110": "Varginha",
    "7240206": "Curitiba", "7240274": "J.Fora", "7240276": "J.Fora",
    "7240285": "P.Grossa", "7240317": "Colombo", "7240341": "Curitiba",
    "7240431": "Curitiba", "7240498": "P.Alegre", "7240510": "N.Lima",
    "7240760": "P.Osorio", "7240761": "P.Osorio", "7240777": "Itajuba",
    "7240866": "Santiago", "7241112": "Curitiba", "7241617": "Umuarama",
    "7241647": "F.Iguacu", "7241705": "S.Vicente", "7241711": "Ibaiti",
    "7241775": "Irati", "7241988": "Parobe", "7242604": "Caxias Sul",
    "7242666": "B.Horizonte", "7242767": "Missal", "7243045": "Canoas",
    "7243103": "S.V.Palmar", "7243529": "P.Alegre", "7243721": "Cacapava",
    "7243947": "Curitiba", "7243960": "Pouso Alegre", "7244070": "B.Horizonte",
    "7244085": "Pouso Alegre", "7244087": "Pouso Alegre", "7244102": "B.Horizonte",
    "7244103": "B.Horizonte", "7244709": "S.Pereira", "7244826": "B.Horizonte",
    "7245089": "Curitiba", "7245090": "Curitiba", "7245093": "Curitiba",
    "7245097": "Cambe", "7245141": "Curitiba", "7245199": "S.Maria",
    "7245222": "S.Maria", "7245655": "Erechim", "7245838": "Caete",
    "7246169": "T.Coracoes", "7246520": "S.J.Pinhais", "7246594": "S.Maria",
    "7246626": "",   # PU5SSS em branco
    # correcao: cidades compostas com nome de estado que a abreviacao cortou errado
    "7240205": "C.Tocantins",   # Colinas do Tocantins
    "7241582": "Belem",         # Belem do Para
    "7243114": "V.Ceara",       # Vicosa do Ceara
    "7244099": "C.Alagoas",     # Conceicao das Alagoas
    "7244233": "C.Alagoas",     # Conceicao das Alagoas
    "7244285": "S.Izabel",      # Santa Izabel do Para
    "7245861": "P.Parana",      # Pontal do Parana
    "7246059": "Boca Acre",     # Boca do Acre
    "7246885": "B.Vista",       # Bela Vista de Goias
    # bairros de capital -> cidade (RJ/SP) e Centro-PA -> Belem
    "7240577": "R.Janeiro",     # Jacarepagua (bairro RJ)
    "7241183": "R.Janeiro",     # Grajau (bairro RJ)
    "7242984": "R.Janeiro",     # Grajau (bairro RJ)
    "7244195": "R.Janeiro",     # Meier (bairro RJ)
    "7242990": "R.Janeiro",     # Flamengo (bairro RJ)
    "7241169": "S.Paulo",       # Itaquera (bairro SP)
    "7241260": "S.Paulo",       # Itaquera (bairro SP)
    "7242386": "S.Paulo",       # Butanta (bairro SP)
    "7243387": "S.Paulo",       # Perus (bairro SP)
    "7245046": "S.Paulo",       # Interlagos (bairro SP)
    "7246846": "Belem",         # Centro (bairro) - Para -> Belem
    "7243240": "Bal.B.Sul",     # Balneario Barra do Sul
    "7242717": "S.Goncalo",     # era "-.S.Goncalo"
    "7244310": "Fpolis",        # "FLORIANOPOLIS - SANTA CATARINA" quebrado
}


def extrai_cidade_br(resto_low, local_original):
    """Para Brasil: remove do FIM o 'lixo de localizacao' (estado 1-4 palavras,
    sigla UF, brazil/brasil/city/state), inclusive quando a UF/estado vem COLADA
    por hifen no ultimo token (ex.: 'recife-pe' -> 'recife'; 'foz do iguacu-parana'
    -> 'foz do iguacu'). Preserva hifens internos legitimos (Ji-Parana, Embu-Guacu)
    quando a parte apos o hifen NAO e uma UF/estado."""
    LIXO1 = {"brazil", "brasil", "city", "cidade", "state", "estado"}
    toks = resto_low.split()
    if not toks:
        return ""
    mudou = True
    while mudou and toks:
        mudou = False
        ult = toks[-1]
        # token do fim e lixo puro (pais/city/UF sozinho)?
        if ult in LIXO1 or ult.upper() in UF_SIGLAS:
            toks = toks[:-1]; mudou = True; continue
        # UF/estado COLADO por hifen no ultimo token: "iguacu-parana", "recife-pe"
        if "-" in ult:
            cabeca, _, cauda = ult.rpartition("-")
            if cauda and (cauda.upper() in UF_SIGLAS or cauda in BR_NOMES_ESTADO):
                # remove so a cauda (UF/estado), preserva a cabeca da cidade
                toks[-1] = cabeca if cabeca else ""
                if not toks[-1]:
                    toks = toks[:-1]
                mudou = True; continue
        # nome de estado por extenso no fim (1 a 4 palavras).
        # usa >= n para remover tambem quando o estado e a UNICA coisa no texto
        # (ex.: texto so "Rio Grande do Sul" -> cidade vazia, nao "R.G.Sul").
        for n in (4, 3, 2, 1):
            if len(toks) >= n and " ".join(toks[-n:]) in BR_NOMES_ESTADO:
                toks = toks[:-n]; mudou = True; break
    return " ".join(toks).strip()


def extrai_cidade_generica(resto_low, cod_pais, state_fmt):
    """Para qualquer pais: recebe o 'resto' (local sem o pais, minusculo/sem acento)
    e o STATE ja formatado. Remove a regiao do fim e devolve a cidade por extenso
    (capitalizada). Nao aplica a abreviacao brasileira."""
    toks = resto_low.split()
    if not toks:
        return ""
    reg_low = strip_acc(state_fmt).lower().strip() if state_fmt else ""
    if reg_low:
        rtok = reg_low.split()
        n = len(rtok)
        if n and len(toks) > n and " ".join(toks[-n:]) == reg_low:
            toks = toks[:-n]
    def cap(w):
        return w[:1].upper() + w[1:] if w else w
    out = []
    for i, t in enumerate(toks):
        if i > 0 and t in PREPOSICOES_BR:
            out.append(t)
        else:
            out.append(cap(t))
    return " ".join(out).strip()


def abrevia_cidade(cidade_low):
    """Aplica as regras de abreviacao a cidade (recebida minuscula, sem acento):
    - tabela especial (Fpolis) tem prioridade;
    - cidade de 1 palavra: por extenso capitalizada;
    - COM preposicao (de/da/do/das/dos/e): as palavras proprias ANTES da
      preposicao viram inicial+ponto; as PREPOSICOES sao descartadas e a palavra
      seguinte fica colada na inicial (economiza espaco no display):
        "rio de janeiro"        -> "R.Janeiro"
        "sao bernardo do campo" -> "S.B.Campo"
        "sao jose dos campos"   -> "S.J.Campos"
    - SEM preposicao: todas as palavras proprias menos a ULTIMA viram inicial;
      a ultima fica por extenso.
        "sao paulo"    -> "S.Paulo"
        "porto alegre" -> "P.Alegre"
        "porto velho"  -> "P.Velho"
    """
    cidade_low = cidade_low.strip()
    if not cidade_low:
        return ""
    if cidade_low in CIDADE_ESPECIAL:
        return CIDADE_ESPECIAL[cidade_low]

    toks = cidade_low.split()

    def cap(w):
        return w[:1].upper() + w[1:] if w else w

    if len(toks) == 1:
        return cap(toks[0])

    # posicao da 1a preposicao
    prep_idx = next((k for k, t in enumerate(toks) if t in PREPOSICOES_BR), None)

    if prep_idx is not None and prep_idx > 0:
        # palavras proprias antes da preposicao viram inicial+ponto;
        # as preposicoes sao DESCARTADAS; o resto proprio fica por extenso, colado.
        proprias = toks[:prep_idx]
        resto = [t for t in toks[prep_idx:] if t not in PREPOSICOES_BR]
        iniciais = ".".join(p[0].upper() for p in proprias) + "."
        resto_fmt = " ".join(cap(t) for t in resto)
        # cola a 1a palavra do resto na inicial (ex.: "R.Janeiro"); demais com espaco
        if resto_fmt:
            partes = resto_fmt.split(" ", 1)
            out = iniciais + partes[0]
            if len(partes) > 1:
                out += " " + partes[1]
            return out
        return iniciais

    # sem preposicao util -> iniciais de todas menos a ultima; ultima por extenso
    if prep_idx is None:
        proprias = toks[:-1]
        ultima = toks[-1]
        iniciais = ".".join(p[0].upper() for p in proprias) + "."
        return iniciais + cap(ultima)

    # começa com preposicao (raro) -> por extenso
    return " ".join(cap(t) for t in toks)


def ajusta_state(state, cod_pais):
    """Portugal: 'Regiao ...' -> 'Reg ...'. Demais: remove a palavra 'Region'."""
    if not state:
        return state
    # unifica a capital argentina: "Ciudad de Buenos Aires" -> "Buenos Aires"
    if cod_pais == "ARG" and state.strip().lower() in (
        "ciudad de buenos aires", "ciudad autonoma de buenos aires", "caba"):
        return "Buenos Aires"
    if cod_pais == "PRT":
        state = re.sub(r"\bRegiao\b", "Reg", state)
    else:
        state = re.sub(r"\s*\bRegion\b", "", state).strip()
    return state

# ----------------------------------------------------------------------------
# CONTATOS EXTRAS: registros que NAO estao na base de origem mas devem ser
# incluidos na saida (inseridos na ordem correta por RADIO_ID).
# Formato ja final: [RADIO_ID, CALLSIGN, FIRST_NAME, "", col5(regiao/cidade), PAIS, ""].
# Para pais != BR, col5 = regiao. Para BR, use "Cidade - UF".
# ----------------------------------------------------------------------------
CONTATOS_EXTRAS = [
    ["7380007", "8R1C", "Chris", "", "Georgetown", "GUY", ""],
]

linhas_saida = []  # (radio_id_int, [campos])

with open(ALVO, "r", encoding="utf-8", newline="") as fin:
    for linha in fin:
        linha = linha.rstrip("\r\n")
        if not linha.strip():
            continue
        m = re.match(r"^(.*?)\s*--\s*(\d+)\s*,", linha)
        if not m:
            continue
        total += 1
        corpo, rid = m.group(1), m.group(2)
        partes = [p.strip() for p in corpo.split(" - ")]
        callsign = partes[0] if len(partes) > 0 else ""
        nome_full = partes[1] if len(partes) > 1 else ""
        # local = ultima parte (sempre contem cidade+pais); se so houver callsign+nome, fica vazio
        local = partes[-1] if len(partes) > 2 else ""
        # first name = primeiro token
        first = nome_full.split()[0] if nome_full.split() else ""
        # limpeza: nome no formato "CALLSIGN-Nome" (indicativo repetido no nome)
        # -> fica so o Nome. Ex.: "DL1SPE-Juergen" -> "Juergen".
        if "-" in first and first.upper().startswith(callsign.upper() + "-"):
            resto_nome = first[len(callsign) + 1:].strip()
            if resto_nome:
                first = resto_nome
            else:
                # "CALL- Nome" (hifen seguido de espaco): pega o proximo token
                toks_nome = nome_full.split()
                first = toks_nome[1] if len(toks_nome) > 1 else first
        # pais + estado
        local_low = strip_acc(local).lower().strip()
        cod_pais, resto = extrai_pais(local_low)
        # override de pais (texto digitado errado; indicativo+cidade concordam)
        if rid in PAIS_OVERRIDE:
            cod_pais = PAIS_OVERRIDE[rid]
            resto = ""  # texto do local nao e confiavel nesse caso
        state = extrai_estado(resto, cod_pais)
        if rid in STATE_OVERRIDE:
            state = STATE_OVERRIDE[rid]
        # "All Regions" (e variantes) e um valor generico/lixo da base do radioid,
        # nao e uma regiao real. Trata como vazio para que a logica de
        # preenchimento assuma (regiao por indicativo ou nome do pais por extenso).
        if state and strip_acc(state).strip().lower() in ("all regions", "all region", "allregions"):
            state = ""
        # fallback: Brasil sem estado -> derivar do indicativo
        if cod_pais == "BRA" and not state:
            state = uf_por_indicativo(callsign)
        # fallback: Espanha sem comunidade -> distrito do indicativo (so os unicos)
        if cod_pais == "ESP" and not state:
            state = comunidade_por_indicativo_es(callsign)
        # fallback: Canada sem provincia -> digito do indicativo (so os unicos)
        if cod_pais == "CAN" and not state:
            state = provincia_por_indicativo_ca(callsign)
        # fallback: Italia sem regiao -> indicativo (so os unicos)
        if cod_pais == "ITA" and not state:
            state = regiao_por_indicativo_it(callsign)
        # fallback: Argentina sem provincia -> 1a letra do sufixo do indicativo
        if cod_pais == "ARG" and not state:
            state = provincia_por_indicativo_ar(callsign)
        # override de nome pontual
        if rid in NOME_OVERRIDE:
            first = NOME_OVERRIDE[rid]
        # enriquecimento: se a regiao ficou vazia, tenta preencher pela referencia
        if not state and rid in REGIAO_REF:
            state = REGIAO_REF[rid]
        # "All Regions" (e variantes) e valor generico/lixo (vem do texto OU da
        # referencia). Trata como vazio para cair no preenchimento por pais extenso.
        if state and strip_acc(state).strip().lower() in ("all regions", "all region", "allregions"):
            state = ""
        # ajuste de STATE (Portugal Regiao->Reg; outros remove 'Region')
        state = ajusta_state(state, cod_pais)
        # col5: Brasil -> "Cidade-UF" (cidade abreviada); demais -> so a regiao
        if cod_pais == "BRA":
            # a cidade pode estar em partes do MEIO quando ha " - " extra
            # (ex.: 'CALL - Nome - Curitiba - Parana Parana Brazil'). Junta tudo
            # apos o nome (partes[2:]) e deixa o extrai_cidade_br remover o lixo final.
            if len(partes) > 3:
                texto_cidade = " ".join(partes[2:])
                cidade_src = strip_acc(texto_cidade).lower().strip()
                # remove o nome do pais do fim antes de extrair a cidade
                _, cidade_src = extrai_pais(cidade_src)
            else:
                cidade_src = resto
            cidade_raw = extrai_cidade_br(cidade_src, local)
            city = abrevia_cidade(cidade_raw) if cidade_raw else ""
            if rid in CITY_OVERRIDE:
                city = CITY_OVERRIDE[rid]
            if city and state:
                col5 = f"{city}-{state}"
            else:
                col5 = city or state
                # Sem cidade e col5 ficou so com a UF: aproveita o espaco do
                # display expandindo a UF para o nome do estado por extenso,
                # desde que caiba em 20 chars (nome + ",BR"). Senao mantem a sigla.
                if not city and col5 in UF_NOME:
                    nome_uf = UF_NOME[col5]
                    if len(nome_uf) + len(",BR") <= 20:
                        col5 = nome_uf
        else:
            col5 = state
        # override pontual da 5a coluna (qualquer pais), p/ casos especiais
        if rid in COL5_OVERRIDE:
            col5 = COL5_OVERRIDE[rid]
        # normaliza Northern Ireland -> N.Ireland (venha do texto ou da referencia)
        if col5 and strip_acc(col5).strip().lower() == "northern ireland":
            col5 = "N.Ireland"
        # Siglas de saida mais curtas (economia de espaco no display):
        #   Portugal PRT->PT ; Brasil BRA->BR
        if cod_pais == "PRT":
            pais_out = "PT"
        elif cod_pais == "BRA":
            pais_out = "BR"
        else:
            pais_out = cod_pais
        # Opcao A: quando NAO ha cidade/regiao (col5 vazio), preenche a col5 com o
        # nome do pais por extenso (sobra espaco no display do radio). A sigla
        # permanece na col6 (a aplicacao exige sigla la). Tenta pela sigla de
        # saida (PT/BR) e, se nao houver, pela sigla de 3 letras (cod_pais).
        if not col5:
            col5 = nome_pais_idioma(pais_out) or nome_pais_idioma(cod_pais)
        # Regra de largura do display (linha = "col5,col6", limite 20 chars).
        # Para paises != BR: se a regiao fizer a linha passar de 20, troca a
        # regiao pelo nome do pais por extenso. Se mesmo o nome por extenso
        # estourar, deixa a regiao vazia (mostra so a sigla do pais).
        # Brasil e preservado (cidades BR ja sao abreviadas).
        if cod_pais != "BRA" and col5:
            if len(col5) + 1 + len(pais_out) > 20:
                nome_pais = nome_pais_idioma(pais_out) or nome_pais_idioma(cod_pais)
                if nome_pais and (len(nome_pais) + 1 + len(pais_out) <= 20):
                    col5 = nome_pais
                else:
                    col5 = ""
        # Layout FISICO identico ao arquivo modelo (20260924_USERS_ID):
        #   col5 = regiao (BR: "Cidade - UF") ; col6 = codigo do pais ; col7 = vazio
        linhas_saida.append((int(rid), [
            rid,
            ascii_clean(callsign),
            ascii_clean(first),
            "",
            ascii_clean(col5),
            pais_out,
            "",
        ]))

# adiciona os contatos extras (evita duplicar se o ID ja veio da base)
ids_existentes = {rid for rid, _ in linhas_saida}
for extra in CONTATOS_EXTRAS:
    if extra[0] not in ids_existentes:
        linhas_saida.append((int(extra[0]), [ascii_clean(x) if i in (1,2,4) else x
                                             for i, x in enumerate(extra)]))

# ordena por RADIO_ID e escreve
linhas_saida.sort(key=lambda t: t[0])
with open(SAIDA, "w", encoding="utf-8", newline="") as fout:
    w = csv.writer(fout)
    w.writerow(["RADIO_ID","CALLSIGN","FIRST_NAME","LAST_NAME","CITY","STATE","COUNTRY"])
    for _, campos in linhas_saida:
        w.writerow(campos)

print(f"Linhas processadas: {total}")
print(f"Contatos extras incluidos: {len(CONTATOS_EXTRAS)}")
print(f"Total na saida: {len(linhas_saida)}")
print(f"Saida: {SAIDA}")

