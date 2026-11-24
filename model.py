import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="Электросеть", layout="wide")
st.title("Модель электрической сети")
st.write("Меняй параметры слева. Красный цвет — значит что-то не так.")

st.sidebar.header("Настройки")
k_dom = st.sidebar.slider("Кол-во домов", 1, 10, 5)
p_dom = st.sidebar.slider("Мощность 1 дома (кВт)", 1, 15, 6, 1)
k_fon = st.sidebar.slider("Кол-во фонарей", 0, 20, 8)
p_fon = st.sidebar.slider("Мощность фонаря (кВт)", 0.1, 1.0, 0.25, 0.05)

dl = st.sidebar.slider("Длина (м)", 50, 500, 150, 10)
s = st.sidebar.selectbox("Сечение (мм2)", [2.5, 4, 6, 10, 16, 25], index=3)
pr = st.sidebar.selectbox("Предохранитель (А)", [16, 20, 25, 32, 40, 50], index=3)
tp_p = st.sidebar.slider("Мощность ТП (кВт)", 20, 200, 60, 10)
res = st.sidebar.slider("Резерв (кВт)", 0, 30, 7, 1)
brk = st.sidebar.slider("Номер участка с обрывом", 0, k_dom, 1)

# физика
U = 400
cosf = 0.95
r_m = 0.0175

R_line = r_m * dl / s
sum_p = k_dom * p_dom + k_fon * p_fon

n_uch = k_dom
len_uch = dl / n_uch if n_uch > 0 else dl
r_1_uch = R_line / n_uch if n_uch > 0 else R_line
x_coord = [(i + 1) * len_uch for i in range(n_uch)]


def count_tok(power_kw):
    if power_kw == 0:
        return 0
    return power_kw * 1000 / (math.sqrt(3) * U * cosf)


def calc_drop(power_kw, r_ohm):
    return math.sqrt(3) * count_tok(power_kw) * r_ohm * cosf


seg_loads = [
    (n_uch - i) * p_dom + p_fon * k_fon * (n_uch - i) / n_uch
    for i in range(n_uch)
]

segment_drops = [calc_drop(seg_loads[k], r_1_uch) for k in range(n_uch)]

voltages = []
u_now = U
for drop_val in segment_drops:
    u_now -= drop_val
    voltages.append(u_now)

tot_drop = sum(segment_drops)
drop_percent = tot_drop / U * 100

print("Нагрузка:", sum_p, "кВт. Потери:", round(drop_percent, 2), "%")

# проверки
st.subheader("Проверка")
c1, c2, c3, c4 = st.columns(4)

with c1:
    if sum_p > tp_p:
        st.error(f"ТП не тянет: {round(sum_p)} > {tp_p}")
    elif sum_p > tp_p * 0.9:
        st.warning(f"ТП почти загружена: {round(sum_p)} / {tp_p}")
    else:
        st.success(f"ТП в порядке: {round(sum_p)} / {tp_p}")

with c2:
    if drop_percent > 5:
        st.error(f"Потери {round(drop_percent, 2)}% — больше 5%")
    elif drop_percent > 3:
        st.warning(f"Потери {round(drop_percent, 2)}% — многовато")
    else:
        st.success(f"Потери {round(drop_percent, 2)}% — всё ок")

with c3:
    i_dom = count_tok(p_dom)
    if i_dom > pr * 1.1:
        st.error(f"Ток дома {round(i_dom, 1)} А > {pr} А")
    else:
        st.success(f"Ток дома {round(i_dom, 1)} А < {pr} А")

with c4:
    if res >= p_dom:
        st.success("Резерв есть")
    elif res > 0:
        st.warning("Резерв маловат")
    else:
        st.error("Резерва нет")

# графики
st.subheader("Графики")
t1, t2, t3, t4 = st.tabs(["Схема", "Напряжение", "Потери и токи", "Обрыв"])

with t1:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(-40, dl + 60)
    ax.set_ylim(-60, 70)
    ax.axis("off")

    ax.add_patch(patches.Rectangle((-30, -12), 24, 24, facecolor="#8a9a5b", edgecolor="black"))
    ax.text(-18, 4, "ТП", ha="center", va="center", fontweight="bold")
    ax.text(-18, -5, f"{tp_p} кВт", ha="center", fontsize=8)

    ax.plot([-6, dl + 12], [0, 0], color="black", lw=2.5)
    ax.text(dl + 15, 0, f"Ток: {round(count_tok(sum_p))} А", fontsize=9, va="center")

    for i, x_pos in enumerate(x_coord):
        ax.plot([x_pos, x_pos], [0, 22], color="black", lw=1.5)
        ax.add_patch(patches.Rectangle((x_pos - 8, 22), 16, 16, facecolor="#a52a2a", edgecolor="black"))
        ax.text(x_pos, 30, str(i + 1), ha="center", va="center", color="white", fontweight="bold")
        ax.text(x_pos, 42, f"{p_dom} кВт", ha="center", fontsize=7)

    if k_fon > 0:
        for j in range(k_fon):
            x_lamp = (j + 0.5) * dl / k_fon
            ax.plot([x_lamp, x_lamp], [0, -12], color="gray", lw=1)
            ax.plot(x_lamp, -16, marker="o", color="#f0c419", markersize=7, markeredgecolor="black")

    st.pyplot(fig)
    plt.close(fig)

with t2:
    fig, ax = plt.subplots(figsize=(10, 4))
    xs = [0] + x_coord
    ys = [U] + voltages
    ax.plot(xs, ys, marker="o", color="#1f4e79", lw=2, label="Напряжение")
    ax.axhline(U, color="gray", ls="--", lw=1, label="Номинал 400В")
    ax.axhline(U * 0.95, color="red", ls=":", lw=1.2, label="-5% ПУЭ")

    for px, py in zip(xs, ys):
        ax.annotate(f"{round(py, 1)}", (px, py), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)

    ax.set_xlabel("Расстояние от ТП, м")
    ax.set_ylabel("Напряжение, В")
    ax.set_title("Падение напряжения")
    ax.set_ylim(350, 410)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    st.pyplot(fig)
    plt.close(fig)

with t3:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    lbls = [f"Уч.{i + 1}" for i in range(n_uch)]

    ax1.bar(lbls, segment_drops, color="#c0504d")
    ax1.set_title("Потери напряжения (В)")
    ax1.grid(axis="y", alpha=0.3)

    toks = [count_tok(x) for x in seg_loads]
    ax2.bar(lbls, toks, color="#4f81bd")
    ax2.set_title("Токи на участках (А)")
    ax2.grid(axis="y", alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

with t4:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(-40, dl + 60)
    ax.set_ylim(-60, 70)
    ax.axis("off")

    ax.add_patch(patches.Rectangle((-30, -12), 24, 24, facecolor="#8a9a5b", edgecolor="black"))
    ax.text(-18, 4, "ТП", ha="center", va="center", fontweight="bold")

    if n_uch > 0 and 0 <= brk < n_uch:
        x_break = len_uch / 2 if brk == 0 else x_coord[brk - 1] + len_uch / 2
    else:
        x_break = dl / 2

    ax.plot([-6, x_break], [0, 0], color="black", lw=2.5)
    ax.plot([x_break, dl + 12], [0, 0], color="gray", lw=2.5, ls="--")
    ax.plot(x_break, 0, marker="x", color="red", markersize=14, mew=3)
    ax.text(x_break, 8, "ОБРЫВ", color="red", ha="center", fontweight="bold")

    for i, x_pos in enumerate(x_coord):
        alive = i < brk
        col = "#a52a2a" if alive else "#cccccc"
        ax.plot([x_pos, x_pos], [0, 22], color="black", lw=1.5)
        ax.add_patch(patches.Rectangle((x_pos - 8, 22), 16, 16, facecolor=col, edgecolor="black"))
        ax.text(x_pos, 30, str(i + 1), ha="center", va="center", color="white", fontweight="bold")
        ax.text(x_pos, 15, "свет" if alive else "нет", ha="center", fontsize=7, color="green" if alive else "red")

    ax.text(dl / 2, -40, f"Резерв: {res} кВт", ha="center", color="#1f4e79")
    st.pyplot(fig)
    plt.close(fig)

st.subheader("Итоговые значения")
st.write(f"Суммарная нагрузка: {round(sum_p, 1)} кВт")
st.write(f"Ток на входе: {round(count_tok(sum_p), 1)} А")
st.write(f"Суммарные потери: {round(drop_percent, 2)}%")
st.write(f"Напряжение в конце: {round(voltages[-1] if voltages else U, 1)} В")
