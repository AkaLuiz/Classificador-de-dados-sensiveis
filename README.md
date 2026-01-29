# Classificador de Pedidos Públicos x Não Públicos (PII Detection)

Este projeto implementa um **classificador automático de pedidos** do tipo e-SIC / LAI, com foco em **detecção de informações pessoais (PII)** e **classificação do pedido como PÚBLICO ou NÃO PÚBLICO**, conforme critérios legais e técnicos.

A solução foi pensada para **funcionar de forma geral**, não dependente de um dataset específico, combinando:
- Regras linguísticas
- Expressões regulares
- NLP (spaCy)
- Heurísticas semânticas e estruturais

---

## 🎯 Objetivo

Identificar automaticamente, em textos livres:

- Dados pessoais explícitos (CPF, RG, endereço, e-mail, telefone, nome)
- Classificar pedidos como:
  - **PÚBLICO** → não contém PII forte
  - **NÃO PÚBLICO** → contém qualquer PII forte

A classificação segue a regra:

```python
PII_FORTE = {"cpf", "rg", "endereco", "email", "telefone", "nome"}
```
---

## 🧠 Abordagem Técnica

A solução utiliza pipeline híbrido:

### 1. Regras determinísticas (Regex)

- CPF
- RG
- Telefone
- E-mail
- Endereço (logradouro + número)

### 2. NLP com spaCy

- Modelo: pt_core_news_lg
- Extração de entidades do tipo PER
- Limpeza de títulos, sufixos e tratamentos formais
- Validação estrutural de nomes próprios

### 3. Heurísticas semânticas

- Validação contextual de RG
- Rejeição de falsos positivos
- Deduplicação entre categorias (resolver conflitos)

---

## 📁 Estrutura do Projeto

``` text
.
├── main.py                 # Script principal (pipeline completo)
├── requirements.txt        # Dependências do projeto
├── README.md               # Documentação
├── AMOSTRA_e-SIC.xlsx      # Arquivo de entrada (exemplo)
```

---

## ⚙️ Pré-requisitos

- Python 3.9 ou superior
- Pip atualizado

---

## 📦 Instalação
### 1. Clone o repositório

``` bash
git clone https://github.com/AkaLuiz/Classificador-de-dados-sensiveis.git
cd Classificador-de-dados-sensiveis

```

### 2. Crie um ambiente virtual

``` bash
python -m venv venv

```

### 3. Ative o ambiente virutal
#### Windows
```bash
venv\Scripts\activate

```
#### Linux/MacOS
``` bash
source venv/bin/activate

```

### 4. Instale as dependencias

``` bash
pip install -r requirements.txt

```

### 5. Baixe o modelo spaCy da língua portuguesa

```bash
python -m spacy download pt_core_news_lg

```
---

## ▶️ Execução
### O script principal é o main.py.
``` bash
python main.py

```

---

## 📥 Entrada
### O script espera um arquivo Excel com a seguinte estrutura mínima:

- Nome do arquivo: AMOSTRA_e-SIC.xlsx
- Coluna obrigatória: Texto Mascarado
- Cada linha representa um pedido

## 📤 Saída
### A saída é impressa no terminal, no formato:
``` text

REGISTRO 7
NÃO PÚBLICO
CPF: ['210.201.140-24']
NOME: ['Maria Martins Mota Silva']

```

Ou, caso não contenha um PII forte:
``` text

REGISTRO 12
PÚBLICO

```
---

## 🛠️ Observações de Projeto

- A classificação é conservadora, priorizando recall conforme exigências de edital
- Também foi adicionado o campo **endereço** para complementar mais casos para a classificação, não se restringindo unicamente ao edital
- Qualquer presença de PII forte torna o pedido NÃO PÚBLICO
- O modelo é agnóstico de domínio, não treinado para um conjunto fixo de dados
- A arquitetura permite fácil extensão para:
  - Classificador semântico de “pedido individualizado”
  - Separação entre PII explícita e informação pessoal indireta
  - Exportação dos resultados para CSV ou JSON
