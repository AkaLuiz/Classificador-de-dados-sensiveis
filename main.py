import re
import pandas as pd
import spacy

# =========================================================
# NLP INITIALIZATION (lazy load)
# =========================================================

_nlp = None

def get_nlp():
    """
    Lazy loader para o modelo spaCy.
    Evita custo de inicialização repetido.
    """
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("pt_core_news_lg")
    return _nlp


# =========================================================
# CONSTANTS / CONFIGURATION
# =========================================================

PALAVRAS_PROIBIDAS = {
    "associação", "associados", "advogados",
    "sociedade", "servidores", "setor",
    "recursos", "coletiva", "magistério",
    "telefônicas", "amostra", "total",
    "temperatura", "fósforo", "nitrogênio",
    "oxigênio", "validador", "sólidos",
    "totais", "gostaria", "gostar", "venho"
}

PREPOSICOES_NOME = {"da", "de", "do", "das", "dos", "e"}

TITULOS = {
    "dr", "dr.", "dra", "dra.",
    "sr", "sr.", "sra", "sra.",
    "prof", "prof.", "profª", "profª.",
    "doutor", "doutora", "doutorª",
    "doutorª.", "doutor.", "doutora."
}

SUFIXOS_LIXO = {"cpf", "cnh", "rg", "nome"}

TRATAMENTOS_FORMAIS = {
    "vossa senhoria",
    "vossa excelência",
    "vossa magnificência",
    "vossa alteza",
    "vossa santidade",

    "v. s.", "v.s.",
    "v. exa.", "v.exa.",
    "v. exª", "v.exª",

    "ilustríssimo senhor",
    "ilustríssima senhora",
    "excelentíssimo senhor",
    "excelentíssima senhora",
    "digníssimo senhor",
    "digníssima senhora",
    "meritíssimo juiz",
    "meritíssima juíza",

    "senhor secretário",
    "senhora secretária",
    "senhor ministro",
    "senhora ministra",
    "senhor governador",
    "senhora governadora",
    "senhor prefeito",
    "senhora prefeita",
    "senhor presidente",
    "senhora presidente",

    "senhor juiz",
    "senhora juíza",
    "senhor desembargador",
    "senhora desembargadora",
    "senhor promotor",
    "senhora promotora",
    "senhor procurador",
    "senhora procuradora",

    "ilustres senhores",
    "ilustres senhoras",
    "vossas senhorias",
    "vossas excelências"
}


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize(text: str) -> str:
    """
    Normalização mínima para evitar ruído de parsing.
    """
    return text.strip().replace("\u00a0", " ")


# =========================================================
# NAME CLEANING UTILITIES
# =========================================================

def limpar_sufixos(nome: str) -> str:
    """
    Remove sufixos claramente não pertencentes ao nome.
    """
    tokens = nome.split()
    while tokens and tokens[-1].lower().strip(":") in SUFIXOS_LIXO:
        tokens.pop()
    return " ".join(tokens)

def limpar_titulos(nome: str) -> str:
    """
    Remove títulos profissionais/honoríficos.
    """
    return " ".join(
        t for t in nome.split()
        if t.lower() not in TITULOS
    )


# =========================================================
# NAME VALIDATION LOGIC
# =========================================================

def nome_valido(nome: str) -> bool:
    """
    Validação semântica e estrutural de nomes próprios.
    """
    tokens = nome.split()

    if len(tokens) < 2 or len(tokens) > 7:
        return False

    if tokens[0].lower() in {"nossa", "nosso", "suas", "seus"}:
        return False

    if tokens[0] == tokens[-1]:
        return False

    for tok in tokens:
        tok_lower = tok.lower()

        if tok_lower in PREPOSICOES_NOME:
            continue

        if tok_lower in PALAVRAS_PROIBIDAS:
            return False

        if not tok[0].isupper():
            return False

    return True


# =========================================================
# NAME EXTRACTION (spaCy + heuristics)
# =========================================================

def extract_names(text: str) -> list[str]:
    """
    Extrai nomes de pessoas combinando NER + heurísticas.
    """
    doc = get_nlp()(text)
    nomes = set()

    for ent in doc.ents:
        if ent.label_ != "PER":
            continue

        raw = ent.text.strip()
        raw_norm = raw.lower()

        # descarta tratamentos formais explícitos
        if any(raw_norm.startswith(t) for t in TRATAMENTOS_FORMAIS):
            continue

        clean = limpar_titulos(raw)
        clean = limpar_sufixos(clean)

        if nome_valido(clean):
            nomes.add(clean)

    return list(nomes)


# =========================================================
# REGEX PATTERNS
# =========================================================

CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{1,2}\b")
RG = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[0-9Xx]\b")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
TELEFONE = re.compile(r"\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?9?\d{4}-?\d{4}\b")
CEP = re.compile(r"\b\d{5}-?\d{3}\b")
LOGRADOURO = re.compile(r"\b(?:Rua|R\.|Avenida|Av\.?|Travessa|Tv\.?|Alameda|Estrada|Rodovia)\s+[A-Za-zÀ-ÿ0-9\s]{3,}",re.IGNORECASE)
QUADRA_LOTE = re.compile(r"\b(Qd\.?|Quadra|Lt\.?|Lote|Bloco|BLC|Conjunto|CJ)\s*[A-Za-z0-9\-]+\b",re.IGNORECASE)

# =========================================================
# GENERIC REGEX EXTRACTION
# =========================================================

def endereco_valido(e: str) -> bool:
    e_lower = e.lower()

    tem_logradouro = any(
        p in e_lower
        for p in ["rua", "avenida", "av", "quadra", "lote", "bloco"]
    )
    tem_numero = any(char.isdigit() for char in e)

    return tem_logradouro and tem_numero


def telefone_valido(tel: str) -> bool:
    digits = re.sub(r"\D", "", tel)

    # Brasil: 10 ou 11 dígitos
    if len(digits) not in (10, 11):
        return False

    # DDD válido começa de 11 a 99
    ddd = int(digits[:2])
    return 11 <= ddd <= 99


def rg_valido(rg: str, text: str) -> bool:
    rg_norm = re.sub(r"\D", "", rg)
    if not (7 <= len(rg_norm) <= 9):
        return False

    for m in re.finditer(rg, text):
        janela = text[max(0, m.start()-15):m.start()].lower()
        if any(p in janela for p in ["rg", "registro geral", "identidade"]):
            return True

    return False




def cpf_formato_valido(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    return len(cpf) == 11

def extract(pattern, text: str) -> list[str]:
    return list(set(pattern.findall(text)))

def extract_endereco(text: str) -> list[str]:
    encontrados = []
    encontrados += LOGRADOURO.findall(text)
    encontrados += QUADRA_LOTE.findall(text)

    return [
        e for e in set(encontrados)
        if endereco_valido(e)
    ]



# =========================================================
# PII DETECTION
# =========================================================

def extract_all(text: str) -> dict:
    """
    Extrai todos os tipos de PII relevantes.
    """
    return {
        "cpf": [c for c in extract(CPF, text) if cpf_formato_valido(c)],
        "rg": [
            r for r in extract(RG, text)
            if rg_valido(r, text)
        ],
        "email": extract(EMAIL, text),
        "telefone": [
            t for t in extract(TELEFONE, text)
            if telefone_valido(t)
        ],
        "endereco": extract_endereco(text),
    }

def detect_pii(text: str) -> dict:
    text = normalize(text)
    pii = extract_all(text)
    pii = resolver_conflitos(pii)
    pii["nome"] = extract_names(text)
    return pii


# =========================================================
# CLASSIFICATION
# =========================================================

PII_FORTE = {"cpf", "rg", "endereco", "email", "telefone", "nome"}

def classificar_pedido(pii: dict) -> str:
    if any(pii[k] for k in PII_FORTE):
        return "NÃO PÚBLICO"
    return "PÚBLICO"

def resolver_conflitos(pii: dict) -> dict:
    usados = set()

    for campo in ["cpf", "rg", "telefone", "endereco"]:
        filtrados = []
        for v in pii.get(campo, []):
            if v not in usados:
                filtrados.append(v)
                usados.add(v)
        pii[campo] = filtrados

    return pii



# =========================================================
# PIPELINE EXECUTION
# =========================================================

df = pd.read_excel("AMOSTRA_e-SIC.xlsx")
texts = df["Texto Mascarado"].dropna().astype(str)

for idx, text in enumerate(texts):
    pii = detect_pii(text)

    dados_sensiveis = {
        k: v for k, v in pii.items() if v
    }

    print(f"\nREGISTRO {idx+1}")
    print(classificar_pedido(pii))

    if dados_sensiveis:
        for campo, valores in dados_sensiveis.items():
            print(f"{campo.upper()}: {valores}")
