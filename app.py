import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Simulador de Carga Térmica - Edificações",
    page_icon="❄️",
    layout="wide"
)

st.title("❄️ Simulador Físico de Carga Térmica de Edificações")
st.markdown("""
Esta ferramenta computacional modela os fenômenos de **transferência de calor (condução, convecção e radiação)** 
e **psicrometria (calor sensível e latente)** em regime permanente, fundamentada nos princípios da **ASHRAE** e **ABNT NBR 16401**.
""")

# ==========================================
# BANCO DE DADOS TÉCNICOS (PARÂMETROS FÍSICOS)
# ==========================================
MATERIAIS_PAREDE = {
    "Alvenaria de tijolo furado (15 cm) com reboco (U = 2,40 W/m²K)": 2.40,
    "Alvenaria de bloco de concreto (19 cm) (U = 2,85 W/m²K)": 2.85,
    "Parede Drywall com isolamento em lã de vidro (U = 0,75 W/m²K)": 0.75,
    "Concreto maciço (12 cm) (U = 3,60 W/m²K)": 3.60,
}

MATERIAIS_COBERTURA = {
    "Laje de concreto + telha fibrocimento sem forro (U = 2,10 W/m²K)": 2.10,
    "Laje + forro acústico com câmara de ar (U = 1,20 W/m²K)": 1.20,
    "Telha termoacústica (sanduíche PIR/PUR 30mm) (U = 0,65 W/m²K)": 0.65,
}

TIPOS_VIDRO = {
    "Vidro Simples Incolor 6mm (U = 5,70 W/m²K | FS = 0,82)": {"U": 5.70, "FS": 0.82},
    "Vidro Simples Fumê/Verde 6mm (U = 5,70 W/m²K | FS = 0,62)": {"U": 5.70, "FS": 0.62},
    "Vidro Duplo Insulado com Controle Solar (U = 2,80 W/m²K | FS = 0,35)": {"U": 2.80, "FS": 0.35},
    "Vidro Simples com Cortina Interna Clara (U = 4,50 W/m²K | FS = 0,50)": {"U": 4.50, "FS": 0.50},
}

IRRADIANCIA_ORIENTACAO = {
    "Norte (Alta insolação no Hemisfério Sul - 550 W/m²)": 550.0,
    "Oeste (Insolação crítica à tarde - 680 W/m²)": 680.0,
    "Leste (Insolação matinal - 520 W/m²)": 520.0,
    "Sul (Radiação difusa predominante - 220 W/m²)": 220.0,
}

ATIVIDADES_METABOLICAS = {
    "Sentado em repouso / Auditório (70 W Sensível | 35 W Latente)": {"S": 70.0, "L": 35.0},
    "Trabalho de escritório / Sala de aula (75 W Sensível | 55 W Latente)": {"S": 75.0, "L": 55.0},
    "Em pé / Comércio / Laboratório leve (90 W Sensível | 95 W Latente)": {"S": 90.0, "L": 95.0},
    "Trabalho físico moderado / Academia leve (150 W Sensível | 270 W Latente)": {"S": 150.0, "L": 270.0},
}

# ==========================================
# BARRA LATERAL: ENTRADA DE DADOS
# ==========================================
st.sidebar.header("📋 Parâmetros de Projeto")

with st.sidebar.expander("1. Condições Termo-Higrométricas (Psicrometria)", expanded=True):
    T_ext = st.number_input("Temperatura de Bulbo Seco Externa (°C)", 15.0, 48.0, 34.0, 0.5)
    w_ext = st.number_input("Umidade Absoluta Externa (g vapor / kg ar seco)", 5.0, 30.0, 18.5, 0.5)
    T_int = st.number_input("Temperatura de Projeto Interna (°C)", 18.0, 28.0, 24.0, 0.5)
    w_int = st.number_input("Umidade Absoluta Interna (g vapor / kg ar seco)", 5.0, 20.0, 9.5, 0.5)

with st.sidebar.expander("2. Geometria e Envoltória Opaca", expanded=False):
    comp = st.number_input("Comprimento da sala (m)", 2.0, 100.0, 8.0, 0.5)
    larg = st.number_input("Largura da sala (m)", 2.0, 100.0, 6.0, 0.5)
    pe_dir = st.number_input("Pé-direito (altura em m)", 2.2, 15.0, 3.0, 0.1)
    
    area_parede_ext = st.number_input("Área total de paredes externas expostas ao sol (m²)", 0.0, 500.0, 24.0, 1.0)
    mat_parede = st.selectbox("Composição das Paredes Externas", list(MATERIAIS_PAREDE.keys()))
    delta_t_sol_ar_par = st.slider("Acréscimo Sol-Ar nas paredes externas (°C)", 0.0, 15.0, 5.0, 0.5,
                                   help="Representa o efeito combinado da radiação solar absorvida pela superfície opaca externa.")
    
    possui_cobertura = st.checkbox("Ambiente possui cobertura/telhado exposto ao sol?", value=True)
    if possui_cobertura:
        mat_cob = st.selectbox("Composição da Cobertura", list(MATERIAIS_COBERTURA.keys()))
        delta_t_sol_ar_cob = st.slider("Acréscimo Sol-Ar na cobertura (°C)", 0.0, 25.0, 12.0, 0.5)

with st.sidebar.expander("3. Fenestração (Janelas e Radiação Solar)", expanded=False):
    area_vidro = st.number_input("Área total de vidros/janelas expostas (m²)", 0.0, 200.0, 6.0, 0.5)
    tipo_vidro = st.selectbox("Especificação do Vidro / Proteção", list(TIPOS_VIDRO.keys()))
    orientacao_vidro = st.selectbox("Orientação Solar Crítica da Fachada", list(IRRADIANCIA_ORIENTACAO.keys()))

with st.sidebar.expander("4. Cargas Internas (Pessoas, Luz, Equipamentos)", expanded=False):
    n_pessoas = st.number_input("Número de ocupantes", 0, 500, 15, 1)
    atividade = st.selectbox("Grau de atividade metabólica", list(ATIVIDADES_METABOLICAS.keys()))
    pot_ilum = st.number_input("Potência total de iluminação (W)", 0.0, 20000.0, 480.0, 20.0)
    pot_equip = st.number_input("Potência nominal de equipamentos/computadores (W)", 0.0, 50000.0, 1800.0, 50.0)
    fator_uso_equip = st.slider("Fator de simultaneidade dos equipamentos", 0.1, 1.0, 0.80, 0.05)

with st.sidebar.expander("5. Renovação de Ar (NBR 16401-3)", expanded=False):
    vazao_por_pessoa = st.number_input("Taxa de ar externo por pessoa (L/s·pessoa)", 0.0, 25.0, 7.5, 0.5)

# ==========================================
# PROCESSAMENTO FÍSICO E TERMODINÂMICO
# ==========================================
area_piso = comp * larg
volume_amb = area_piso * pe_dir
delta_T_base = max(0.0, T_ext - T_int)
delta_w_base = max(0.0, (w_ext - w_int) / 1000.0)  # kg_vapor / kg_ar_seco

# 1. Condução em Paredes Externas (descontando área de vidro caso inserida na mesma fachada)
U_parede = MATERIAIS_PAREDE[mat_parede]
area_parede_liquida = max(0.0, area_parede_ext - area_vidro)
dT_eq_parede = delta_T_base + delta_t_sol_ar_par
Q_cond_parede = U_parede * area_parede_liquida * dT_eq_parede

# 2. Condução na Cobertura
if possui_cobertura:
    U_cob = MATERIAIS_COBERTURA[mat_cob]
    dT_eq_cob = delta_T_base + delta_t_sol_ar_cob
    Q_cond_cobertura = U_cob * area_piso * dT_eq_cob
else:
    U_cob = 0.0
    dT_eq_cob = 0.0
    Q_cond_cobertura = 0.0

# 3. Transferência de Calor em Vidros (Condução + Radiação Solar Transmitida)
U_vid = TIPOS_VIDRO[tipo_vidro]["U"]
FS_vid = TIPOS_VIDRO[tipo_vidro]["FS"]
I_sol = IRRADIANCIA_ORIENTACAO[orientacao_vidro]

Q_vidro_cond = U_vid * area_vidro * delta_T_base
Q_vidro_solar = area_vidro * FS_vid * I_sol

# 4. Carga Metabólica de Ocupação (Sensível e Latente)
q_sens_pes = ATIVIDADES_METABOLICAS[atividade]["S"]
q_lat_pes = ATIVIDADES_METABOLICAS[atividade]["L"]
Q_ocup_sens = n_pessoas * q_sens_pes
Q_ocup_lat = n_pessoas * q_lat_pes

# 5. Iluminação e Equipamentos (100% Calor Sensível por Efeito Joule)
Q_iluminacao = pot_ilum
Q_equipamentos = pot_equip * fator_uso_equip

# 6. Ventilação / Renovação de Ar Higiênica (Psicrometria)
# Propriedades padrão do ar ao nível do mar: rho = 1,20 kg/m³, cp = 1006 J/(kg·K), h_lv = 2.450.000 J/kg
rho_ar = 1.20
cp_ar = 1006.0
h_lv = 2450000.0

vazao_ar_ls = n_pessoas * vazao_por_pessoa
vazao_ar_m3s = vazao_ar_ls / 1000.0
fluxo_massico_ar = rho_ar * vazao_ar_m3s  # kg/s

Q_vent_sens = fluxo_massico_ar * cp_ar * delta_T_base
Q_vent_lat = fluxo_massico_ar * h_lv * delta_w_base

# ==========================================
# CONSOLIDAÇÃO DAS PARCELAS
# ==========================================
Q_sensivel_total = (
    Q_cond_parede + Q_cond_cobertura + Q_vidro_cond + Q_vidro_solar +
    Q_ocup_sens + Q_iluminacao + Q_equipamentos + Q_vent_sens
)
Q_latente_total = Q_ocup_lat + Q_vent_lat
Q_total_W = Q_sensivel_total + Q_latente_total

# Conversões de unidades técnicas
Q_total_kW = Q_total_W / 1000.0
Q_total_BTUh = Q_total_W * 3.41214
Q_total_TR = Q_total_W / 3516.85
FCS = Q_sensivel_total / Q_total_W if Q_total_W > 0 else 1.0

# ==========================================
# PAINEL DE RESULTADOS PRINCIPAIS
# ==========================================
st.subheader("📊 Indicadores Termodinâmicos Globais")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Carga Térmica Total", f"{Q_total_W:,.0f} W", f"{Q_total_kW:.2f} kW")
col2.metric("Capacidade em BTU/h", f"{Q_total_BTUh:,.0f} BTU/h")
col3.metric("Toneladas de Refrigeração", f"{Q_total_TR:.2f} TR")
col4.metric("Fator de Calor Sensível (FCS)", f"{FCS:.2%}")
col5.metric("Densidade Térmica Real", f"{Q_total_W / area_piso:.1f} W/m²", f"{Q_total_BTUh / area_piso:.0f} BTU/h·m²")

st.divider()

# ==========================================
# TABELA E GRÁFICOS POR FENÔMENO FÍSICO
# ==========================================
df_parcelas = pd.DataFrame([
    {"Parcela": "Condução - Paredes Opacas", "Mecanismo Físico": "Condução (Lei de Fourier / U·A·ΔTeq)", "Natureza": "Sensível", "Potência (W)": Q_cond_parede},
    {"Parcela": "Condução - Cobertura", "Mecanismo Físico": "Condução (Lei de Fourier / U·A·ΔTeq)", "Natureza": "Sensível", "Potência (W)": Q_cond_cobertura},
    {"Parcela": "Condução - Vidros", "Mecanismo Físico": "Condução / Convecção de Fronteira", "Natureza": "Sensível", "Potência (W)": Q_vidro_cond},
    {"Parcela": "Radiação Solar - Vidros", "Mecanismo Físico": "Radiação de Onda Curta Transmitida", "Natureza": "Sensível", "Potência (W)": Q_vidro_solar},
    {"Parcela": "Ocupação - Sensível", "Mecanismo Físico": "Metabolismo (Convecção + Radiação)", "Natureza": "Sensível", "Potência (W)": Q_ocup_sens},
    {"Parcela": "Ocupação - Latente", "Mecanismo Físico": "Metabolismo (Evaporação / Sudorese)", "Natureza": "Latente", "Potência (W)": Q_ocup_lat},
    {"Parcela": "Iluminação", "Mecanismo Físico": "Dissipação Elétrica (Efeito Joule)", "Natureza": "Sensível", "Potência (W)": Q_iluminacao},
    {"Parcela": "Equipamentos", "Mecanismo Físico": "Dissipação Elétrica (Efeito Joule)", "Natureza": "Sensível", "Potência (W)": Q_equipamentos},
    {"Parcela": "Ventilação - Sensível", "Mecanismo Físico": "Entalpia de Ar Seco (m_ar·cp·ΔT)", "Natureza": "Sensível", "Potência (W)": Q_vent_sens},
    {"Parcela": "Ventilação - Latente", "Mecanismo Físico": "Entalpia de Vapor d'Água (m_ar·hlv·Δω)", "Natureza": "Latente", "Potência (W)": Q_vent_lat},
])
df_parcelas["Potência (BTU/h)"] = df_parcelas["Potência (W)"] * 3.41214
df_parcelas["Participação (%)"] = (df_parcelas["Potência (W)"] / Q_total_W * 100.0) if Q_total_W > 0 else 0.0

col_graf1, col_graf2 = st.columns([3, 2])

with col_graf1:
    st.subheader("🔍 Contribuição de Cada Fenômeno Físico")
    fig_bar = px.bar(
        df_parcelas,
        x="Potência (W)",
        y="Parcela",
        color="Natureza",
        orientation="h",
        text_auto=".0f",
        color_discrete_map={"Sensível": "#FF6B6B", "Latente": "#4DABF7"},
        title="Distribuição das Parcelas de Carga Térmica (W)"
    )
    fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

with col_graf2:
    st.subheader("💧 Balanço Sensível vs. Latente")
    fig_pie = px.pie(
        df_parcelas,
        values="Potência (W)",
        names="Natureza",
        color="Natureza",
        color_discrete_map={"Sensível": "#FF6B6B", "Latente": "#4DABF7"},
        hole=0.45,
        title="Proporção Psicrométrica no Ambiente"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("📑 Quadro Analítico de Rastreabilidade")
st.dataframe(
    df_parcelas.style.format({
        "Potência (W)": "{:,.1f}",
        "Potência (BTU/h)": "{:,.0f}",
        "Participação (%)": "{:.1f}%"
    }),
    use_container_width=True
)

# ==========================================
# MEMORIAL DE CÁLCULO E HIPÓTESES ADOTADAS
# ==========================================
st.divider()
st.subheader("📝 Memorial de Cálculo Técnico e Hipóteses Simplificadoras")

relatorio_md = f"""
### 1. Hipóteses Termodinâmicas do Modelo
* **Regime Permanente Estacionário:** Os fluxos de calor são avaliados para a condição crítica de projeto, assumindo propriedades termofísicas constantes na seção transversal dos fechamentos opacos.
* **Propriedades Psicrométricas do Ar Padrão:** Massa específica $\\rho_{{ar}} = 1,20 \\text{{ kg/m}}^3$, calor específico à pressão constante $c_p = 1.006 \\text{{ J/(kg\\cdot K)}}$ e entalpia de vaporização da água $h_{{lv}} = 2.450.000 \\text{{ J/kg}}$.
* **Temperatura Sol-Ar ($\\Delta T_{{eq}}$):** O ganho radiativo incidente sobre superfícies opacas externas é incorporado ao diferencial de temperatura equivalente.

### 2. Rastreamento das Equações Aplicadas
1. **Condução em Paredes Opacas:** $\\dot{{Q}}_{{par}} = U_{{par}} \\cdot A_{{liq}} \\cdot \\Delta T_{{eq}} = {U_parede:.2f} \\times {area_parede_liquida:.1f} \\times {dT_eq_parede:.1f} = \\mathbf{{{Q_cond_parede:.1f} \\text{{ W}}}}$
2. **Condução na Cobertura:** $\\dot{{Q}}_{{cob}} = U_{{cob}} \\cdot A_{{piso}} \\cdot \\Delta T_{{eq,cob}} = {U_cob:.2f} \\times {area_piso:.1f} \\times {dT_eq_cob:.1f} = \\mathbf{{{Q_cond_cobertura:.1f} \\text{{ W}}}}$
3. **Condução nos Vidros:** $\\dot{{Q}}_{{vid,c}} = U_{{vid}} \\cdot A_{{vid}} \\cdot (T_{{ext}} - T_{{int}}) = {U_vid:.2f} \\times {area_vidro:.1f} \\times {delta_T_base:.1f} = \\mathbf{{{Q_vidro_cond:.1f} \\text{{ W}}}}$
4. **Radiação Solar Direta/Difusa em Vidros:** $\\dot{{Q}}_{{vid,rad}} = A_{{vid}} \\cdot \\text{{FS}} \\cdot I_{{sol}} = {area_vidro:.1f} \\times {FS_vid:.2f} \\times {I_sol:.0f} = \\mathbf{{{Q_vidro_solar:.1f} \\text{{ W}}}}$
5. **Metabolismo Humano (Ocupação):** 
   * Sensível: ${n_pessoas} \\text{{ ocupantes}} \\times {q_sens_pes:.0f} \\text{{ W}} = \\mathbf{{{Q_ocup_sens:.1f} \\text{{ W}}}}$
   * Latente: ${n_pessoas} \\text{{ ocupantes}} \\times {q_lat_pes:.0f} \\text{{ W}} = \\mathbf{{{Q_ocup_lat:.1f} \\text{{ W}}}}$
6. **Cargas Eletrotérmicas Internas:** $\\dot{{Q}}_{{ilum}} + \\dot{{Q}}_{{equip}} = {Q_iluminacao:.1f} + ({pot_equip:.1f} \\times {fator_uso_equip:.2f}) = \\mathbf{{{Q_iluminacao + Q_equipamentos:.1f} \\text{{ W}}}}$
7. **Renovação de Ar Higiênica (Vazão = ${vazao_ar_ls:.1f} \\text{{ L/s}}$ | $\\dot{{m}}_{{ar}} = {fluxo_massico_ar:.4f} \\text{{ kg/s}}$):**
   * Sensível: $\\dot{{m}}_{{ar}} \\cdot c_p \\cdot \\Delta T = \\mathbf{{{Q_vent_sens:.1f} \\text{{ W}}}}$
   * Latente: $\\dot{{m}}_{{ar}} \\cdot h_{{lv}} \\cdot \\Delta \\omega = \\mathbf{{{Q_vent_lat:.1f} \\text{{ W}}}}$

### 3. Síntese para Seleção de Equipamento
* **Carga Sensível Total ($\\dot{{Q}}_S$):** ${Q_sensivel_total:,.1f} \\text{{ W}}$
* **Carga Latente Total ($\\dot{{Q}}_L$):** ${Q_latente_total:,.1f} \\text{{ W}}$
* **Carga Térmica Global ($\\dot{{Q}}_{{tot}}$):** ${Q_total_W:,.1f} \\text{{ W}}$ (${Q_total_BTUh:,.0f} \\text{{ BTU/h}}$ | ${Q_total_TR:.2f} \\text{{ TR}}$)
* **Fator de Calor Sensível ($\\text{{FCS}}$):** ${FCS:.3f}$
"""

st.markdown(relatorio_md)

st.download_button(
    label="📥 Baixar Relatório Técnico (Formato Markdown/Texto)",
    data=relatorio_md,
    file_name="memorial_carga_termica.md",
    mime="text/markdown"
)
