# IT Inventory Dashboard 📦

A lightweight web application for tracking IT hardware and software assets. Built with Python Flask and Bootstrap, with SQLite storage and CSV import/export for easy data management.

![Dashboard](https://via.placeholder.com/800x400?text=IT+Inventory+Dashboard)

## Features

- **Asset tracking** for hardware, software, licenses, and network equipment
- **Dashboard** with visual summaries by status and category
- **Search & filter** by name, asset tag, serial number, assignee, category, status
- **CSV export** - Download full inventory as spreadsheet
- **CSV import** - Bulk load assets from existing spreadsheets
- **Full CRUD** - Create, edit, and delete assets
- Priority status tracking: Active, In Repair, In Storage, Retired
- Warranty expiry tracking
- Assignment tracking (who has what)
- Bootstrap 5 responsive UI

## Tech Stack

- Python 3.10+
- Flask 3.0
- Flask-SQLAlchemy
- SQLite (zero-config, file-based)
- Bootstrap 5.3
- Bootstrap Icons

## Installation

```bash
git clone https://github.com/kevinmenay/it-inventory-dashboard.git
cd it-inventory-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the App

```bash
python app.py
```

Open http://localhost:5000 in your browser. The SQLite database (`inventory.db`) is created automatically with sample data on first run.

## Configuration

Set environment variables before running:

```bash
export SECRET_KEY="your-secure-secret-key"
export DATABASE_URL="sqlite:///inventory.db"  # or postgresql://...
```

Or create a `.env` file:
```
SECRET_KEY=your-secure-secret-key
DATABASE_URL=sqlite:///inventory.db
```

## CSV Import Format

Import assets from a CSV file with these columns:

```
asset_tag, name, category, asset_type, manufacturer, model, 
serial_number, status, assigned_to, location, 
purchase_date, warranty_expiry, cost, notes
```

**Example CSV:**
```csv
asset_tag,name,category,asset_type,manufacturer,model,status,assigned_to,location,cost
HW-101,Dell Latitude 5540,Hardware,Laptop,Dell,Latitude 5540,Active,Sarah Jones,HQ Floor 3,1299.99
NET-050,Cisco Catalyst 2960,Hardware,Network Switch,Cisco,2960-48PS,Active,,Server Room,2450.00
SW-010,Adobe Creative Suite,Software,Design Suite,Adobe,,Active,Design Team,Cloud,599.00
```

**Import process:**
1. Go to Assets → Import CSV
2. Select your CSV file
3. Duplicate asset tags are automatically skipped

## Screenshots

### Dashboard
Shows total asset count, active/repair counts, total inventory value, and breakdown charts by status and category.

### Asset List
Full searchable/filterable table with inline edit and delete. Batch export to CSV.

### Asset Form
Comprehensive form covering all asset fields including warranty dates and cost.

## Project Structure

```
it-inventory-dashboard/
├── app.py              # Flask application, models, routes
├── requirements.txt    # Python dependencies
├── templates/
│   ├── base.html       # Sidebar layout template
│   ├── dashboard.html  # Stats dashboard
│   ├── assets.html     # Asset list with search/filter
│   └── asset_form.html # Create/edit form
└── README.md
```

## Deployment

### Production with Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn
COPY . .
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "app:app"]
```

## License

MIT License - See [LICENSE](LICENSE) for details.
