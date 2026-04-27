from django.conf import settings
import os
import base64
from jinja2 import Template

def get_affected_villages_pdf_template(data, count):
    # Embed logo as base64
    logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
    logo_url = None
    
    if os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                logo_url = f'data:image/jpeg;base64,{encoded_string}'
        except Exception as e:
            print(f"Error loading logo: {e}")
            logo_url = None

    # HTML template for PDF
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @page {
                size: landscape;
                margin: 10mm;
            }
            body { 
                font-family: 'Arial', 'Helvetica Neue', sans-serif;
                margin: 0;
                padding: 0;
                background: white;
            }
            .container {
                background: white;
                padding: 0;
            }
            .header {
                text-align: center;
                margin: 0;
                padding: 0;
                background: #ffffff;
                border-bottom: 3px solid #2e7d32;
            }
            .logo { 
                margin: 0;
                padding: 5px 0;
            }
            .logo img { 
                max-width: 180px;
                height: auto;
                border: none;
                background: transparent;
                display: block;
                margin: 0 auto;
            }
            h1 { 
                color: #2e7d32;
                font-size: 28px;
                margin: 2px 0;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 3px;
                font-family: 'Arial Black', Gadget, sans-serif;
            }
            h2 {
                color: #558b2f;
                font-size: 14px;
                margin: 2px 0 8px 0;
                font-weight: 500;
                font-family: 'Arial', sans-serif;
            }
            .count { 
                font-size: 14px;
                color: #2e7d32;
                background: #f1f8e9;
                padding: 8px 20px;
                border-radius: 20px;
                display: inline-block;
                font-weight: 600;
                border: 1px solid #c5e1a5;
                font-family: 'Arial', sans-serif;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 0;
            }
            th {
                background: #2e7d32;
                color: white;
                padding: 10px 6px;
                text-align: left;
                font-weight: 600;
                font-size: 10px;
                text-transform: uppercase;
                border: none;
                font-family: 'Arial', sans-serif;
            }
            td {
                border: none;
                border-bottom: 1px solid #e0e0e0;
                padding: 8px 6px;
                text-align: left;
                font-size: 9px;
                color: #424242;
                font-family: 'Arial', sans-serif;
            }
            tr:nth-child(even) {
                background-color: #fafafa;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            tr:last-child td {
                border-bottom: none;
            }
            /* Specific column widths */
            th:nth-child(1), td:nth-child(1) { width: 10%; text-align: center; font-weight: 600; color: #2e7d32; } /* SrNo */
            th:nth-child(2), td:nth-child(2) { width: 30%; } /* Village Name */
            th:nth-child(3), td:nth-child(3) { width: 25%; } /* Tehsil Name */
            th:nth-child(4), td:nth-child(4) { width: 25%; } /* City Name */
            th:nth-child(5), td:nth-child(5) { width: 10%; text-align: center; } /* Affected Farmers Count */
            .numeric {
                color: #2e7d32;
                font-weight: 600;
            }
            .footer {
                margin-top: 15px;
                text-align: center;
                color: #558b2f;
                font-size: 11px;
                padding: 12px 0;
                background: #f9fbe7;
                font-weight: 600;
                border-top: 2px solid #c5e1a5;
                font-family: 'Arial', sans-serif;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                {% if logo_url %}
                <div class="logo">
                    <img src="{{ logo_url }}" alt="Mera Pind Logo">
                </div>
                {% endif %}
                <h1>Mera Pind</h1>
                <h2>Affected Villages Report</h2>
                <div class="count">Total Villages: {{ count }}</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Sr No</th>
                        <th>Village Name</th>
                        <th>Tehsil Name</th>
                        <th>City Name</th>
                        <th>Affected Farmers Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in data %}
                    <tr>
                        <td>{{ item.SrNo }}</td>
                        <td>{{ item.village_name }}</td>
                        <td>{{ item.tehsil_name }}</td>
                        <td>{{ item.city_name }}</td>
                        <td class="numeric">{{ item.person_count }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <div class="footer">
                Mera Pind Agricultural Relief System
            </div>
        </div>
    </body>
    </html>
    """

    # Render the template with data
    template = Template(html_template)
    return template.render(data=data, count=count, logo_url=logo_url)