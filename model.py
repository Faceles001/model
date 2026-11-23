"""
Модель электрической сети посёлка.
Streamlit-приложение для расчёта потерь, токов и проверки по ПУЭ.
"""

import math
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Настройки страницы
st.set_page_config(page_title="Модель сети посёлка", layout="wide")
st.title("Модель электрической сети посёлка")
st.markdown("Меняйте параметры слева — графики пересчитаются автоматически.")

# Ползунки в боковой панели
st.sidebar.header("Исходные данные")

n_houses = st.sidebar.slider("Число домов", 1, 10, 5)
power_house = st.sidebar.slider("Мощность дома, кВт", 1.0, 15.0, 6.0, 0.5)
n_lamps = st.sidebar.slider("Число фонарей", 0, 20, 8)
power_lamp = st.sidebar.slider("Мощность фонаря, кВт", 0.1, 1.0, 0.25, 0.05)

length = st.sidebar.slider("Длина линии, м", 50, 500, 150, 10)
section = st.sidebar.selectbox("Сечение провода, мм²", [2.5, 4, 6, 10, 16, 25], index=3)
fuse = st.sidebar.selectbox("Предохранитель, А", [16, 20, 25, 32, 40, 50], index=3)
power_tp = st.sidebar.slider("Мощность ТП, кВт", 20, 200, 60, 10)
reserve = st.sidebar.slider("Резервный генератор, кВт", 0, 30, 7, 1)
break_at = st.sidebar.slider("Обрыв на участке №", 0, n_houses, 2)

# Константы
voltage = 400.0        # линейное напряжение, В
cos_phi = 0.95         # коэффициент мощности
rho_copper = 0.0175    # удельное сопротивление меди, Ом·мм²/м

# Сопротивление всей линии R = ρ·L/S и суммарная нагрузка
r_line = rho_copper * length / section
total_kw = n_houses * power_house + n_lamps * power_lamp

# Параметры участков
n = n_houses
seg_length = length / n if n else length
r_segment = r_line / n if n else r_line
x_houses = [(i + 1) * seg_length for i in range(n)]

# Функции расчёта
def get_current(p_kw, u=voltage, cosf=cos_phi):
    """Ток трёхфазной нагрузки, А: I = P/(√3·U·cosφ)."""
    return p_kw * 1000.0 / (math.sqrt(3) * u * cosf)


def get_voltage_drop(p_kw, r, u=voltage, cosf=cos_phi):
    """Потеря напряжения, В: ΔU = √3·I·R·cosφ."""
    return math.sqrt(3) * get_current(p_kw, u, cosf) * r * cosf


# Расчёт нагрузок и потерь по участкам
load_segment = []
for k in range(n):
    # дома с k-го по последний + доля фонарей, оставшихся позади
    load = (n - k) * power_house + power_lamp * n_lamps * (n - k) / n
    load_segment.append(load)

drops = [get_voltage_drop(load_segment[k], r_segment) for k in range(n)]

voltages = []
u = voltage
for du in drops:
    u -= du
    voltages.append(u)

total_drop = sum(drops)
drop_percent = total_drop / voltage * 100.0

# Проверки (светофоры)
st.subheader("Проверки")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if total_kw > power_tp:
        st.error(f"ТП перегружена: {total_kw:.0f} > {power_tp} кВт")
    elif total_kw > power_tp * 0.9:
        st.warning(f"ТП близко к пределу: {total_kw:.0f} / {power_tp} кВт")
    else:
        st.success(f"ТП: {total_kw:.0f} / {power_tp} кВт")

with col2:
    if drop_percent > 5:
        st.error(f"Потери {drop_percent:.2f}% > 5% (ПУЭ)")
    elif drop_percent > 3:
        st.warning(f"Потери {drop_percent:.2f}% — норма, но высокие")
    else:
        st.success(f"Потери {drop_percent:.2f}% < 5% (ПУЭ)")

with col3:
    current_house = get_current(power_house)
    if current_house > fuse * 1.1:
        st.error(f"Ток дома {current_house:.1f} А > {fuse} А")
    else:
        st.success(f"Ток дома {current_house:.1f} А < {fuse} А")

with col4:
    if reserve >= power_house:
        st.success(f"Резерв {reserve} кВт хватает")
    elif reserve > 0:
        st.warning(f"Резерв {reserve} кВт < дома {power_house} кВт")
    else:
        st.error("Резерва нет")

# Вкладки с графиками
st.subheader("Результаты моделирования")
tab1, tab2, tab3, tab4 = st.tabs(["Схема", "Напряжение", "Потери и токи", "Обрыв"])

# Вкладка 1: схема сети
with tab1:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(-40, length + 60)
    ax.set_ylim(-60, 70)
    ax.axis("off")

    # ТП
    ax.add_patch(patches.Rectangle((-30, -12), 24, 24,
                                   facecolor="#8a9a5b", edgecolor="black", lw=1.5))
    ax.text(-18, 4, "ТП", ha="center", va="center", fontsize=10, fontweight="bold")
    ax.text(-18, -5, f"{power_tp} кВт", ha="center", fontsize=8)

    # Магистраль
    ax.plot([-6, length + 12], [0, 0], color="black", lw=2.5)
    ax.text(length + 15, 0, f"I = {get_current(total_kw):.0f} А", fontsize=9, va="center")

    # Дома
    for i, d in enumerate(x_houses):
        ax.plot([d, d], [0, 22], color="black", lw=1.5)
        ax.add_patch(patches.Rectangle((d - 8, 22), 16, 16,
                                       facecolor="#a52a2a", edgecolor="black", lw=1.2))
        ax.text(d, 30, str(i + 1), ha="center", va="center",
                color="white", fontsize=10, fontweight="bold")
        ax.text(d, 42, f"{power_house:.1f} кВт", ha="center", fontsize=7)

    # Фонари
    if n_lamps > 0:
        lamp_x = [(j + 0.5) * length / n_lamps for j in range(n_lamps)]
        for x in lamp_x:
            ax.plot([x, x], [0, -12], color="gray", lw=1)
            ax.plot(x, -16, marker="o", color="#f0c419", markersize=7,
                    markeredgecolor="black")

    st.pyplot(fig)
    plt.close(fig)

# Вкладка 2: напряжение вдоль линии
with tab2:
    fig, ax = plt.subplots(figsize=(10, 4))
    x_axis = [0] + x_houses
    u_axis = [voltage] + voltages
    ax.plot(x_axis, u_axis, marker="o", color="#1f4e79", lw=2, label="Напряжение")
    ax.axhline(voltage, color="gray", ls="--", lw=1, label="Номинал 400 В")
    ax.axhline(voltage * 0.95, color="red", ls=":", lw=1.2, label="-5% ПУЭ")
    for x, uu in zip(x_axis, u_axis):
        ax.annotate(f"{uu:.1f}", (x, uu), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8)
    ax.set_xlabel("Расстояние от ТП, м")
    ax.set_ylabel("Напряжение, В")
    ax.set_title(f"Напряжение вдоль линии (потери {drop_percent:.2f}%)")
    ax.set_ylim(350, 410)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    st.pyplot(fig)
    plt.close(fig)

# Вкладка 3: потери и токи
with tab3:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    labels = [f"уч.{i+1}" for i in range(n)]

    ax1.bar(labels, drops, color="#c0504d", edgecolor="black")
    ax1.set_ylabel("Потеря, В")
    ax1.set_title("Потери по участкам")
    ax1.grid(axis="y", alpha=0.3)

    currents = [get_current(p) for p in load_segment]
    ax2.bar(labels, currents, color="#4f81bd", edgecolor="black")
    ax2.set_ylabel("Ток, А")
    ax2.set_title("Ток по участкам")
    ax2.grid(axis="y", alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

# Вкладка 4: сценарий обрыва
with tab4:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(-40, length + 60)
    ax.set_ylim(-60, 70)
    ax.axis("off")

    # ТП
    ax.add_patch(patches.Rectangle((-30, -12), 24, 24,
                                   facecolor="#8a9a5b", edgecolor="black", lw=1.5))
    ax.text(-18, 4, "ТП", ha="center", va="center", fontsize=10, fontweight="bold")

    # Точка обрыва
    if n > 0 and 0 <= break_at < n:
        break_x = x_houses[break_at - 1] + seg_length / 2 if break_at > 0 else seg_length / 2
    else:
        break_x = length / 2

    ax.plot([-6, break_x], [0, 0], color="black", lw=2.5)
    ax.plot([break_x, length + 12], [0, 0], color="gray", lw=2.5, ls="--")
    ax.plot(break_x, 0, marker="x", color="red", markersize=14, mew=3)
    ax.text(break_x, 8, "ОБРЫВ", color="red", ha="center", fontsize=10, fontweight="bold")

    # Дома (живые и обесточенные)
    for i, d in enumerate(x_houses):
        is_alive = i < break_at
        color = "#a52a2a" if is_alive else "#cccccc"
        ax.plot([d, d], [0, 22], color="black", lw=1.5)
        ax.add_patch(patches.Rectangle((d - 8, 22), 16, 16,
                                       facecolor=color, edgecolor="black", lw=1.2))
        ax.text(d, 30, str(i + 1), ha="center", va="center",
                color="white", fontsize=10, fontweight="bold")
        ax.text(d, 15, "есть свет" if is_alive else "нет света",
                ha="center", fontsize=7, color="green" if is_alive else "red")

    ax.text(length / 2, -40, f"Решение: резерв {reserve} кВт",
            ha="center", fontsize=9, color="#1f4e79")

    st.pyplot(fig)
    plt.close(fig)

# Итоговые цифры
st.subheader("Итоговые цифры")
st.write(f"**Суммарная нагрузка:** {total_kw:.1f} кВт")
st.write(f"**Ток в голове линии:** {get_current(total_kw):.1f} А")
st.write(f"**Потери напряжения:** {total_drop:.2f} В ({drop_percent:.2f}%)")
st.write(f"**Напряжение у дальнего дома:** {voltages[-1] if voltages else voltage:.1f} В")