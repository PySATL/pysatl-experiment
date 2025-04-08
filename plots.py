import json
import sqlite3
from fpdf import FPDF
import matplotlib
from matplotlib.colors import LinearSegmentedColormap

from stattest.experiment.generator import symmetric_generators, asymmetric_generators

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import seaborn as sns
import pandas as pd
import numpy as np


def format_alternative(alt_code):
	parts = alt_code.split("_")
	params = ", ".join(parts[1:])
	return f"{parts[0]}({params})"


def get_formatted_alternative_codes(generators):
	"""Получаем отформатированные коды альтернатив"""
	return [format_alternative(gen.code()) for gen in generators]


# Получаем отформатированные коды альтернатив
symmetric_codes = get_formatted_alternative_codes(symmetric_generators)
asymmetric_codes = get_formatted_alternative_codes(asymmetric_generators)
all_codes = symmetric_codes + asymmetric_codes


def get_top_tests(grouped_data, alt_codes, sample_sizes, top_n=5):
	"""Возвращает топ-N критериев для заданных альтернатив и размеров выборки"""
	results = []

	# Создаем обратное отображение отформатированных кодов к исходным
	code_mapping = {}
	for gen in symmetric_generators + asymmetric_generators:
		formatted = format_alternative(gen.code())
		code_mapping[formatted] = gen.code()

	for formatted_alt in alt_codes:
		original_code = code_mapping.get(formatted_alt)
		if not original_code:
			continue

		key = (formatted_alt, 0.05)  # Используем исходный код для поиска в grouped_data
		if key not in grouped_data:
			print("debug")
			continue

		for size in sample_sizes:
			if size not in grouped_data[key]["sizes"]:
				continue

			for test, power in grouped_data[key]["tests"].items():
				if size in power:
					results.append({
						'test': test,
						'alt': formatted_alt,  # Сохраняем отформатированное название
						'size': size,
						'power': power[size]
					})

	df = pd.DataFrame(results)

	# Группируем и находим среднюю мощность для каждого критерия
	grouped = df.groupby(['test', 'size'])['power'].mean().reset_index()

	# Получаем топ критериев для каждого размера выборки
	top_tests = {}
	for size in sample_sizes:
		top = grouped[grouped['size'] == size].nlargest(top_n, 'power')
		top_tests[size] = top[['test', 'power']].values.tolist()

	return top_tests


def print_results_table(top_results, title, sample_sizes, top_n=5):
	"""Выводит результаты в виде таблицы"""
	print(f"\n{title}")
	print("{:<10} {:<15} {:<10} {:<10} {:<10}".format(
		"Size", "1st", "2nd", "3rd", "4th", "5th"))

	for size in sample_sizes:
		if size in top_results:
			tests = [f"{t[0]} ({t[1]:.3f})" for t in top_results[size]]
			# # Дополняем до 5 элементов, если нужно
			# tests += [""] * (5 - len(tests))
			print("{:<10} {:<15} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
				size, *tests[:top_n]))


def prepare_heatmap_data(grouped_data, n):
	all_tests = set()
	all_alts = set()

	for key in grouped_data:
		alt_code, alpha = key
		if alpha != 0.05:  # Изменено с 0.95 на 0.05
			continue
		all_alts.add(alt_code)
		all_tests.update(grouped_data[key]["tests"].keys())

	if not all_tests or not all_alts:
		return None, None, None

	all_tests = sorted(all_tests)
	all_alts = sorted(all_alts)

	heatmap_data = np.zeros((len(all_tests), len(all_alts)))

	for alt_idx, alt_code in enumerate(all_alts):
		for test_idx, test_code in enumerate(all_tests):
			key = (alt_code, 0.05)  # Изменено на 0.05
			if key not in grouped_data:
				continue
			if test_code not in grouped_data[key]["tests"]:
				continue
			if n not in grouped_data[key]["tests"][test_code]:
				continue
			heatmap_data[test_idx, alt_idx] = grouped_data[key]["tests"][test_code][n]

	return heatmap_data, all_tests, all_alts


def animate_heatmaps(grouped_data):
	# Получаем все уникальные размеры выборок
	all_sizes = sorted({size for key in grouped_data for size in grouped_data[key]["sizes"]})

	# Фильтрация размеров с данными для alpha=0.05
	valid_sizes = []
	for n in all_sizes:
		data, _, _ = prepare_heatmap_data(grouped_data, n)
		if data is not None and np.any(data != 0):
			valid_sizes.append(n)

	if not valid_sizes:
		raise ValueError("Нет данных для alpha=0.05")

	# Получаем размеры сетки из первого валидного кадра
	initial_data, all_tests, all_alts = prepare_heatmap_data(grouped_data, valid_sizes[0])
	X, Y = np.arange(initial_data.shape[1] + 1), np.arange(initial_data.shape[0] + 1)

	# Создаем кастомный красно-зеленый колормап
	colors = ["#ff0000", "#ffff00", "#00ff00"]  # Красный -> Желтый -> Зеленый
	cmap = LinearSegmentedColormap.from_list("RdYlGn", colors)

	# Инициализация фигуры
	fig, ax = plt.subplots(figsize=(18, 12))
	cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])

	# Создаем mesh с нашим цветовым градиентом
	mesh = ax.pcolormesh(X, Y, initial_data, cmap=cmap, vmin=0, vmax=1)
	fig.colorbar(mesh, cax=cbar_ax, label="Мощность")

	# Настройка осей
	ax.set_xticks(np.arange(initial_data.shape[1]) + 0.5)
	ax.set_xticklabels(all_alts, rotation=90)
	ax.set_yticks(np.arange(initial_data.shape[0]) + 0.5)
	ax.set_yticklabels(all_tests)
	ax.set_title(f"Мощность критериев (n = {valid_sizes[0]}, alpha=0.05)")

	def init():
		"""Функция инициализации для анимации"""
		return [mesh]

	def update(frame):
		"""Обновление данных для каждого кадра"""
		n = valid_sizes[frame]
		data, _, _ = prepare_heatmap_data(grouped_data, n)
		mesh.set_array(data.ravel())  # Обновляем данные
		ax.set_title(f"Мощность критериев (n = {n}, alpha=0.05)")
		return [mesh]

	# Создаем анимацию
	ani = animation.FuncAnimation(
		fig,
		update,
		frames=len(valid_sizes),
		init_func=init,
		interval=500,
		blit=True
	)

	return ani


def format_test_name(test_name):
	return test_name.replace("_GOODNESS_OF_FIT", "").replace("_EXP", "")


def fetch_data_from_db(db_path):
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	cursor.execute("SELECT data FROM result")
	rows = cursor.fetchall()
	conn.close()

	extracted_data = []
	for row in rows:
		try:
			data = json.loads(row[0])
			extracted_data.append(data)
		except json.JSONDecodeError:
			continue
	return extracted_data


def get_grouped_data(data):
	pdf = FPDF(orientation="L")
	pdf.set_auto_page_break(auto=True, margin=15)
	pdf.add_page()

	pdf.set_font("helvetica", size=10)

	grouped_data = {}
	for entry in data:
		test_code = entry.get("test_code", "Unknown")
		alt_code = format_alternative(entry.get("alternative_code", "Unknown"))
		alpha = entry.get("alpha", "Unknown")
		size = entry.get("size", 0)
		power = entry.get("power", 0)

		key = (alt_code, alpha)
		if key not in grouped_data:
			grouped_data[key] = {"sizes": set(), "tests": {}}

		grouped_data[key]["sizes"].add(size)
		if test_code not in grouped_data[key]["tests"]:
			grouped_data[key]["tests"][test_code] = {}
		grouped_data[key]["tests"][test_code][size] = power

	for key in grouped_data:
		grouped_data[key]["sizes"] = sorted(grouped_data[key]["sizes"])
		grouped_data[key]["tests"] = dict(sorted(grouped_data[key]["tests"].items()))

	return grouped_data


def generate_animation_powers_increase(grouped_data, output_filename):
	try:
		ani = animate_heatmaps(grouped_data)
		ani.save(output_filename, writer="pillow", dpi=100)
	except ValueError as e:
		print(f"Ошибка: {e}")


def main():
	db_path = "exponential_experiment_cv.sqlite"
	output_filename = "all files"

	data = fetch_data_from_db(db_path)
	grouped_data = get_grouped_data(data)

	# generate_animation_powers_increase(grouped_data, "power_heatmaps.gif")

	# Размеры выборок для анализа
	sample_sizes = [10, 100, 1000]

	# Получаем топ критериев
	top_symmetric = get_top_tests(grouped_data, symmetric_codes, sample_sizes, top_n=10)
	top_asymmetric = get_top_tests(grouped_data, asymmetric_codes, sample_sizes, top_n=10)
	top_all = get_top_tests(grouped_data, all_codes, sample_sizes, top_n=10)

	# Выводим результаты
	print_results_table(top_symmetric, "Топ критериев для симметричных альтернатив", sample_sizes, top_n=10)
	print_results_table(top_asymmetric, "Топ критериев для асимметричных альтернатив", sample_sizes, top_n=10)
	print_results_table(top_all, "Топ критериев для всех альтернатив", sample_sizes, top_n=10)

	print(f"PDF отчет сохранен как: {output_filename}")


if __name__ == "__main__":
	main()
