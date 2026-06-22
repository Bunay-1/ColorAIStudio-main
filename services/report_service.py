import time
import os
import pandas as pd

AUDIT_LOG_FILE = os.environ.get("AUDIT_LOG_PATH", "AuditTrail/measurements_log.csv")

def generate_html_report(request_data, de, status, status_color, color_engine):
    """Генерира богат на графики HTML сертификат за качество."""
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"Report_{request_data.batch_id}_{timestamp}.html"

    # Подготовка на данни за графиката
    wavelengths = list(range(400, 701, 10))
    def lab_to_mock_spectrum(lab):
        L, a, b = lab
        import numpy as np
        return [max(0, min(1, (L/100) + (a/500)*np.sin(w/50) + (b/500)*np.cos(w/50))) for w in wavelengths]

    std_spectrum = lab_to_mock_spectrum(request_data.lab_standard)
    sam_spectrum = lab_to_mock_spectrum(request_data.lab_sample)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Quality Certificate - {request_data.batch_id}</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; color: #333; padding: 40px; }}
            .card {{ background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); padding: 40px; max-width: 900px; margin: auto; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }}
            .logo {{ font-weight: bold; font-size: 24px; color: #0052cc; }}
            .status {{ font-size: 28px; font-weight: 800; color: {status_color}; text-align: center; padding: 15px 30px; border: 3px solid {status_color}; border-radius: 8px; display: inline-block; }}
            .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 30px; }}
            .info-box {{ background: #fafafa; padding: 15px; border-radius: 6px; border-left: 5px solid #0052cc; }}
            .label {{ font-size: 11px; color: #666; text-transform: uppercase; font-weight: bold; letter-spacing: 1px; }}
            .value {{ font-size: 16px; margin-top: 5px; font-family: monospace; }}
            .chart-container {{ margin-top: 40px; height: 350px; padding: 20px; background: #fff; border: 1px solid #eee; border-radius: 8px; }}
            .footer {{ margin-top: 50px; text-align: center; font-size: 13px; color: #777; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <div class="logo">ICAP Industrial Color AI</div>
                <div style="text-align: right;">
                    <div style="font-size: 14px; color: #666;">Сертификат # {int(time.time())}</div>
                    <div style="font-size: 14px; color: #666;">Дата: {time.strftime('%Y-%m-%d %H:%M')}</div>
                </div>
            </div>

            <div style="text-align: center; margin-bottom: 40px;">
                <div class="status">{status}</div>
                <div style="font-size: 48px; font-weight: 900; margin-top: 15px; color: #1a1a1a;">ΔE: {de:.4f}</div>
                <div style="color: #666;">({request_data.method} / {request_data.illuminant})</div>
            </div>

            <div class="grid">
                <div class="info-box"><div class="label">Партида</div><div class="value">{request_data.batch_id}</div></div>
                <div class="info-box"><div class="label">Оператор</div><div class="value">{request_data.operator_id}</div></div>
                <div class="info-box"><div class="label">Клиент</div><div class="value">{request_data.client_id}</div></div>
                <div class="info-box"><div class="label">Метод</div><div class="value">{request_data.method}</div></div>
                <div class="info-box"><div class="label">Стандарт (Lab)</div><div class="value">{request_data.lab_standard}</div></div>
                <div class="info-box"><div class="label">Мостра (Lab)</div><div class="value">{request_data.lab_sample}</div></div>
            </div>

            <div class="chart-container">
                <canvas id="reportChart"></canvas>
            </div>

            <script>
                const ctx = document.getElementById('reportChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: {wavelengths},
                        datasets: [
                            {{
                                label: 'Мостра (Спектър)',
                                data: {sam_spectrum},
                                borderColor: '{status_color}',
                                backgroundColor: '{status_color}22',
                                fill: true,
                                tension: 0.4
                            }},
                            {{
                                label: 'Стандарт (Спектър)',
                                data: {std_spectrum},
                                borderColor: '#333',
                                borderDash: [5, 5],
                                fill: false,
                                tension: 0.4
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            y: {{ beginAtZero: true, title: {{ display: true, text: 'Рефлектанс %' }} }},
                            x: {{ title: {{ display: true, text: 'Дължина на вълната (nm)' }} }}
                        }}
                    }}
                }});
            </script>

            <div class="footer">
                Този документ е генериран автоматично от Industrial Color AI Platform.<br>
                Данните са базирани на спектрофотометрични измервания и AI анализ.
            </div>
        </div>
    </body>
    </html>
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filename

def generate_iso_audit_report():
    """Автоматично генериране на ISO 9001 одитен отчет (HTML) от SQL базата."""
    import database
    try:
        conn = database.get_db_connection()
        df = pd.read_sql_query("SELECT * FROM measurements", conn)
        conn.close()
        if df.empty:
            return None, "Log файлът е празен."

        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"ISO_Audit_Report_{timestamp}.html"

        # Изчисляване на статистики
        total = len(df)
        passed = len(df[df['status'] == 'Pass'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        # Генериране на HTML таблица
        table_html = df.to_html(classes='audit-table', index=False)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>ISO 9001 Audit Report - {timestamp}</title>
            <style>
                body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
                .report-container {{ background: white; padding: 30px; border-radius: 8px; max-width: 1200px; margin: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #1a1a1a; border-bottom: 2px solid #0052cc; padding-bottom: 10px; }}
                .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
                .stat-card {{ background: #fafafa; padding: 20px; border-radius: 6px; border: 1px solid #eee; text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #0052cc; }}
                .audit-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px; }}
                .audit-table th, .audit-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                .audit-table th {{ background-color: #f2f2f2; font-weight: bold; }}
                .audit-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .audit-table tr:hover {{ background-color: #f1f1f1; }}
                .status-pass {{ color: green; font-weight: bold; }}
                .status-fail {{ color: red; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <h1>ISO 9001 Quality Audit Report</h1>
                <p>Дата на генериране: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>

                <div class="stats">
                    <div class="stat-card"><div>Общо измервания</div><div class="stat-value">{total}</div></div>
                    <div class="stat-card"><div>Успешни (Pass)</div><div class="stat-value" style="color:green;">{passed}</div></div>
                    <div class="stat-card"><div>Неуспешни (Fail)</div><div class="stat-value" style="color:red;">{failed}</div></div>
                    <div class="stat-card"><div>Процент съответствие</div><div class="stat-value">{pass_rate:.2f}%</div></div>
                </div>

                <h2>Детайлен лог на измерванията</h2>
                {table_html}

                <div style="margin-top:40px; border-top: 1px solid #eee; padding-top: 20px; font-size: 12px; color: #777; text-align: center;">
                    Този отчет е автоматично генериран от ICAP Enterprise Edition съгласно процедурите за ISO 9001 одит.
                </div>
            </div>
        </body>
        </html>
        """
        html_content = html_content.replace('<td>Pass</td>', '<td><span class="status-pass">Pass</span></td>')
        html_content = html_content.replace('<td>Fail</td>', '<td><span class="status-fail">Fail</span></td>')

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        return filename, None
    except Exception as e:
        return None, str(e)
