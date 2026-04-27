from django.conf import settings
import os
import base64
from jinja2 import Template

def get_pdf_template(data, count):
    # Embed logo as base64 - works on any server
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

    # HTML template for PDF with improved design
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
            /* Specific column widths for better data display */
            th:nth-child(1), td:nth-child(1) { width: 3%; text-align: center; font-weight: 600; color: #2e7d32; } /* SrNo */
            th:nth-child(2), td:nth-child(2) { width: 7%; } /* Farmer Name */
            th:nth-child(3), td:nth-child(3) { width: 7%; } /* Father Name */
            th:nth-child(3), td:nth-child(3) { width: 7%; } /* Mobile Number */
            th:nth-child(4), td:nth-child(4) { width: 6%; } /* City */
            th:nth-child(5), td:nth-child(5) { width: 6%; } /* Village */
            th:nth-child(6), td:nth-child(6) { width: 5%; } /* State */
            th:nth-child(7), td:nth-child(7) { width: 7%; } /* House Status */
            th:nth-child(8), td:nth-child(8) { width: 6%; text-align: center; } /* Amount Needed */
            th:nth-child(9), td:nth-child(9) { width: 6%; text-align: center; } /* Amount Received */
            th:nth-child(10), td:nth-child(10) { width: 5%; text-align: center; } /* Total Land */
            th:nth-child(11), td:nth-child(11) { width: 5%; text-align: center; } /* Land Affected */
            th:nth-child(12), td:nth-child(12) { width: 5%; } /* Crops Planted */
            th:nth-child(13), td:nth-child(13) { width: 5%; } /* Crops Lost */
            th:nth-child(14), td:nth-child(14) { width: 13%; } /* Estimated Loss */
            
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
                <h2>Empowering Rural Punjab</h2>
                <div class="count">Total Records: {{ count }}</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Sr No</th>
                        <th>Farmer Name</th>
                        <th>Father Name</th>
                        <th>Mobile Number</th>
                        <th>City</th>
                        <th>Village</th>
                        <th>State</th>
                        <th>House Status</th>
                        <th>Amount Needed</th>
                        <th>Amount Received</th>
                        <th>Total Land</th>
                        <th>Land Affected</th>
                        <th>Crops Planted</th>
                        <th>Crops Lost</th>
                        <th>Est. Loss</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in data %}
                    <tr>
                        <td>{{ item.SrNo }}</td>
                        <td>{{ item.farmerName }}</td>
                        <td>{{ item.fatherName }}</td>
                        <td>{{ item.mobile_number }}</td>
                        <td>{{ item.city_name }}</td>
                        <td>{{ item.village_name }}</td>
                        <td>{{ item.state_name }}</td>
                        <td>{{ item.houseStatus }}</td>
                        <td class="numeric">{{ item.amount_needed }}</td>
                        <td class="numeric">{{ item.amount_received }}</td>
                        <td class="numeric">{{ item.totalLandOwned }}</td>
                        <td class="numeric">{{ item.landAffected }}</td>
                        <td>{{ item.cropsPlanted }}</td>
                        <td>{{ item.cropsLost }}</td>
                        <td class="numeric">{{ item.estimatedCropLoss }}</td>
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