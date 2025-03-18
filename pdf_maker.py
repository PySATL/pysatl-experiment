import json
import sqlite3

from fpdf import FPDF, XPos, YPos


def format_alternative(alt_code):
    parts = alt_code.split("_")
    params = ", ".join(parts[1:])
    return f"{parts[0]}({params})"


def format_test_name(test_name):
    return test_name.replace("_GOODNESS_OF_FIT", "")


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


def generate_pdf(data, output_filename):
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

    for key in sorted(grouped_data.keys(), key=lambda x: (x[0], x[1])):
        alt_code, alpha = key
        group = grouped_data[key]
        sizes = group["sizes"]
        tests = group["tests"]

        pdf.set_font("helvetica", "B", 12)
        pdf.cell(
            0,
            10,
            f"Alternative: {alt_code}, Significance Level: alpha = {alpha}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(5)

        num_cols = len(sizes) + 1
        col_width = (280 - 20) / num_cols

        pdf.set_font("helvetica", "B", 10)
        pdf.cell(col_width, 10, "Test", border=1, align="C")
        for size in sizes:
            pdf.cell(col_width, 10, str(size), border=1, align="C")
        pdf.ln()

        pdf.set_font("helvetica", size=10)
        for test, values in tests.items():
            formatted_test_name = format_test_name(test)
            pdf.cell(col_width, 10, formatted_test_name, border=1, align="C")
            for size in sizes:
                power = values.get(size, "N/A")
                if isinstance(power, float):
                    power = f"{power:.3f}"
                pdf.cell(col_width, 10, str(power), border=1, align="C")
            pdf.ln()

        pdf.ln(10)

    pdf.output(output_filename)


def main():
    db_path = "exponential_experiment.sqlite"
    output_filename = "test_comparison_report_exponential_experiment.pdf"

    data = fetch_data_from_db(db_path)
    generate_pdf(data, output_filename)
    print(f"PDF отчет сохранен как: {output_filename}")


if __name__ == "__main__":
    main()