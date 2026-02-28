"""SQLite database for lawyers directory."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "lawyers.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create table and seed demo data if empty."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    # Drop old table if schema changed (distance_km column added)
    cur.execute("PRAGMA table_info(lawyers)")
    columns = [row[1] for row in cur.fetchall()]
    if columns and "distance_km" not in columns:
        cur.execute("DROP TABLE lawyers")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lawyers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            location TEXT NOT NULL,
            experience_years INTEGER NOT NULL,
            bar_council_id TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            languages TEXT NOT NULL,
            rating REAL NOT NULL,
            cases_won INTEGER NOT NULL,
            distance_km INTEGER NOT NULL,
            avatar_url TEXT NOT NULL
        )
    """)

    if cur.execute("SELECT COUNT(*) FROM lawyers").fetchone()[0] == 0:
        _seed(cur)

    conn.commit()
    conn.close()


def _seed(cur: sqlite3.Cursor):
    """Insert demo Kerala lawyers across all 18 specializations."""
    # (name, specialization, location, exp_years, bar_id, phone, email, languages, rating, cases_won, distance_km, avatar_url)
    lawyers = [
        # Criminal Lawyer
        ("Adv. Ramesh Krishnan", "Criminal Lawyer", "Thiruvananthapuram", 18, "KER/1234/2007", "+91-9876500001", "ramesh.k@example.com", "Malayalam, English, Hindi", 4.8, 312, 5, "https://api.dicebear.com/9.x/initials/svg?seed=RK"),
        ("Adv. Manoj George", "Criminal Lawyer", "Thrissur", 20, "KER/7890/2005", "+91-9876500009", "manoj.g@example.com", "Malayalam, English, Tamil", 4.8, 380, 45, "https://api.dicebear.com/9.x/initials/svg?seed=MG"),
        ("Adv. Sajan Philip", "Criminal Lawyer", "Kochi", 14, "KER/2201/2011", "+91-9876500013", "sajan.p@example.com", "Malayalam, English", 4.5, 195, 12, "https://api.dicebear.com/9.x/initials/svg?seed=SP"),
        # Civil Lawyer
        ("Adv. Suresh Nair", "Civil Lawyer", "Kozhikode", 22, "KER/0987/2003", "+91-9876500003", "suresh.n@example.com", "Malayalam, English, Tamil", 4.9, 420, 150, "https://api.dicebear.com/9.x/initials/svg?seed=SN"),
        ("Adv. Meera Warrier", "Civil Lawyer", "Thiruvananthapuram", 11, "KER/2202/2014", "+91-9876500014", "meera.w@example.com", "Malayalam, English", 4.4, 110, 8, "https://api.dicebear.com/9.x/initials/svg?seed=MW"),
        # Family Lawyer
        ("Adv. Priya Menon", "Family Lawyer", "Kochi", 12, "KER/2345/2013", "+91-9876500002", "priya.m@example.com", "Malayalam, English", 4.6, 198, 18, "https://api.dicebear.com/9.x/initials/svg?seed=PM"),
        ("Adv. Sreelatha Das", "Family Lawyer", "Thiruvananthapuram", 14, "KER/8901/2011", "+91-9876500010", "sreelatha.d@example.com", "Malayalam, English", 4.6, 210, 3, "https://api.dicebear.com/9.x/initials/svg?seed=SD"),
        # Corporate / Business Lawyer
        ("Adv. Vivek Sharma", "Corporate / Business Lawyer", "Kochi", 16, "KER/2203/2009", "+91-9876500015", "vivek.s@example.com", "Malayalam, English, Hindi", 4.7, 245, 22, "https://api.dicebear.com/9.x/initials/svg?seed=VS"),
        ("Adv. Nisha Kurian", "Corporate / Business Lawyer", "Kozhikode", 9, "KER/2204/2016", "+91-9876500016", "nisha.k@example.com", "Malayalam, English", 4.3, 78, 160, "https://api.dicebear.com/9.x/initials/svg?seed=NK"),
        # Constitutional Lawyer
        ("Adv. Vijay Thomas", "Constitutional Lawyer", "Kochi", 25, "KER/0011/2000", "+91-9876500007", "vijay.t@example.com", "Malayalam, English, Hindi", 4.9, 510, 15, "https://api.dicebear.com/9.x/initials/svg?seed=VT"),
        # Tax Lawyer
        ("Adv. Anjali Raj", "Tax Lawyer", "Kozhikode", 10, "KER/6789/2015", "+91-9876500008", "anjali.r@example.com", "Malayalam, English", 4.5, 132, 140, "https://api.dicebear.com/9.x/initials/svg?seed=AR"),
        ("Adv. Rohit Menon", "Tax Lawyer", "Kochi", 13, "KER/2205/2012", "+91-9876500017", "rohit.m@example.com", "Malayalam, English", 4.6, 165, 20, "https://api.dicebear.com/9.x/initials/svg?seed=RoM"),
        # Property / Real Estate Lawyer
        ("Adv. Rajesh Menon", "Property / Real Estate Lawyer", "Kochi", 16, "KER/9012/2009", "+91-9876500011", "rajesh.m@example.com", "Malayalam, English, Hindi", 4.7, 290, 25, "https://api.dicebear.com/9.x/initials/svg?seed=RM"),
        ("Adv. Geetha Kumari", "Property / Real Estate Lawyer", "Thrissur", 19, "KER/2206/2006", "+91-9876500018", "geetha.k@example.com", "Malayalam, English", 4.7, 305, 55, "https://api.dicebear.com/9.x/initials/svg?seed=GK"),
        # Labor & Employment Lawyer
        ("Adv. Arun Kumar", "Labor & Employment Lawyer", "Thiruvananthapuram", 15, "KER/4567/2010", "+91-9876500005", "arun.k@example.com", "Malayalam, English, Hindi", 4.7, 267, 7, "https://api.dicebear.com/9.x/initials/svg?seed=AK"),
        # Immigration Lawyer
        ("Adv. Fathima Beevi", "Immigration Lawyer", "Kochi", 8, "KER/2207/2017", "+91-9876500019", "fathima.b@example.com", "Malayalam, English, Arabic", 4.4, 88, 30, "https://api.dicebear.com/9.x/initials/svg?seed=FB"),
        # Intellectual Property (IP) Lawyer
        ("Adv. Arjun Nambiar", "Intellectual Property (IP) Lawyer", "Kochi", 7, "KER/2208/2018", "+91-9876500020", "arjun.n@example.com", "Malayalam, English", 4.3, 62, 17, "https://api.dicebear.com/9.x/initials/svg?seed=AN"),
        # Medical / Healthcare Lawyer
        ("Adv. Dr. Smitha Rajan", "Medical / Healthcare Lawyer", "Thiruvananthapuram", 12, "KER/2209/2013", "+91-9876500021", "smitha.r@example.com", "Malayalam, English", 4.6, 145, 10, "https://api.dicebear.com/9.x/initials/svg?seed=SR"),
        # Environmental Lawyer
        ("Adv. Biju Mathew", "Environmental Lawyer", "Kozhikode", 17, "KER/2210/2008", "+91-9876500022", "biju.m@example.com", "Malayalam, English", 4.5, 178, 135, "https://api.dicebear.com/9.x/initials/svg?seed=BM"),
        # Cyber Law Lawyer
        ("Adv. Deepa Varma", "Cyber Law Lawyer", "Kochi", 6, "KER/5678/2019", "+91-9876500006", "deepa.v@example.com", "Malayalam, English", 4.3, 54, 14, "https://api.dicebear.com/9.x/initials/svg?seed=DV"),
        ("Adv. Nikhil Prasad", "Cyber Law Lawyer", "Thiruvananthapuram", 5, "KER/2211/2020", "+91-9876500023", "nikhil.p@example.com", "Malayalam, English, Hindi", 4.2, 38, 6, "https://api.dicebear.com/9.x/initials/svg?seed=NP"),
        # Banking & Finance Lawyer
        ("Adv. Sunitha Nair", "Banking & Finance Lawyer", "Kochi", 15, "KER/2212/2010", "+91-9876500024", "sunitha.n@example.com", "Malayalam, English", 4.7, 230, 19, "https://api.dicebear.com/9.x/initials/svg?seed=SuN"),
        # Arbitration Lawyer
        ("Adv. Thomas Mathew", "Arbitration Lawyer", "Kochi", 21, "KER/2213/2004", "+91-9876500025", "thomas.m@example.com", "Malayalam, English, Hindi", 4.8, 340, 23, "https://api.dicebear.com/9.x/initials/svg?seed=TM"),
        # Consumer Court Lawyer
        ("Adv. Lakshmi Pillai", "Consumer Court Lawyer", "Thrissur", 8, "KER/3456/2017", "+91-9876500004", "lakshmi.p@example.com", "Malayalam, English", 4.4, 95, 50, "https://api.dicebear.com/9.x/initials/svg?seed=LP"),
        ("Adv. Kavitha Nambiar", "Consumer Court Lawyer", "Kozhikode", 9, "KER/1122/2016", "+91-9876500012", "kavitha.n@example.com", "Malayalam, English", 4.5, 108, 145, "https://api.dicebear.com/9.x/initials/svg?seed=KN"),
        # Human Rights Lawyer
        ("Adv. Ravi Shankar", "Human Rights Lawyer", "Thiruvananthapuram", 23, "KER/2214/2002", "+91-9876500026", "ravi.s@example.com", "Malayalam, English, Hindi, Tamil", 4.9, 450, 4, "https://api.dicebear.com/9.x/initials/svg?seed=RS"),
        ("Adv. Jyothi Lal", "Human Rights Lawyer", "Kozhikode", 16, "KER/3301/2009", "+91-9876500040", "jyothi.l@example.com", "Malayalam, English", 4.6, 210, 142, "https://api.dicebear.com/9.x/initials/svg?seed=JL"),
        # International Law Lawyer
        ("Adv. Ananya Krishnan", "International Law Lawyer", "Kochi", 11, "KER/2215/2014", "+91-9876500027", "ananya.k@example.com", "Malayalam, English, French", 4.5, 120, 28, "https://api.dicebear.com/9.x/initials/svg?seed=AnK"),
        ("Adv. Samir Hussain", "International Law Lawyer", "Thiruvananthapuram", 19, "KER/3302/2006", "+91-9876500041", "samir.h@example.com", "Malayalam, English, Arabic, Hindi", 4.7, 275, 9, "https://api.dicebear.com/9.x/initials/svg?seed=SH"),

        # ===== ADDITIONAL LAWYERS (ensuring 2-3 per category) =====

        # Constitutional Lawyer (had 1)
        ("Adv. Padmini Nair", "Constitutional Lawyer", "Thiruvananthapuram", 20, "KER/3303/2005", "+91-9876500042", "padmini.n@example.com", "Malayalam, English, Hindi", 4.8, 390, 6, "https://api.dicebear.com/9.x/initials/svg?seed=PN"),
        ("Adv. George Varghese", "Constitutional Lawyer", "Kozhikode", 17, "KER/3304/2008", "+91-9876500043", "george.v@example.com", "Malayalam, English", 4.6, 230, 155, "https://api.dicebear.com/9.x/initials/svg?seed=GV"),

        # Labor & Employment Lawyer (had 1)
        ("Adv. Sindhu Mohan", "Labor & Employment Lawyer", "Kochi", 10, "KER/3305/2015", "+91-9876500044", "sindhu.m@example.com", "Malayalam, English", 4.5, 130, 20, "https://api.dicebear.com/9.x/initials/svg?seed=SM"),
        ("Adv. Babu Raj", "Labor & Employment Lawyer", "Thrissur", 22, "KER/3306/2003", "+91-9876500045", "babu.r@example.com", "Malayalam, English, Tamil", 4.8, 360, 48, "https://api.dicebear.com/9.x/initials/svg?seed=BR"),

        # Immigration Lawyer (had 1)
        ("Adv. Reshma Salim", "Immigration Lawyer", "Thiruvananthapuram", 12, "KER/3307/2013", "+91-9876500046", "reshma.s@example.com", "Malayalam, English, Arabic", 4.5, 105, 7, "https://api.dicebear.com/9.x/initials/svg?seed=ReSa"),
        ("Adv. Jobin Chacko", "Immigration Lawyer", "Kozhikode", 15, "KER/3308/2010", "+91-9876500047", "jobin.c@example.com", "Malayalam, English, Hindi", 4.6, 175, 148, "https://api.dicebear.com/9.x/initials/svg?seed=JC"),

        # Intellectual Property (IP) Lawyer (had 1)
        ("Adv. Divya Prasad", "Intellectual Property (IP) Lawyer", "Thiruvananthapuram", 11, "KER/3309/2014", "+91-9876500048", "divya.p@example.com", "Malayalam, English", 4.5, 98, 8, "https://api.dicebear.com/9.x/initials/svg?seed=DP"),
        ("Adv. Kiran Babu", "Intellectual Property (IP) Lawyer", "Thrissur", 14, "KER/3310/2011", "+91-9876500049", "kiran.b@example.com", "Malayalam, English, Hindi", 4.6, 140, 52, "https://api.dicebear.com/9.x/initials/svg?seed=KB"),

        # Medical / Healthcare Lawyer (had 1)
        ("Adv. Asha Menon", "Medical / Healthcare Lawyer", "Kochi", 15, "KER/3311/2010", "+91-9876500050", "asha.m@example.com", "Malayalam, English", 4.7, 200, 16, "https://api.dicebear.com/9.x/initials/svg?seed=AsM"),
        ("Adv. Sunil Joseph", "Medical / Healthcare Lawyer", "Kozhikode", 9, "KER/3312/2016", "+91-9876500051", "sunil.j@example.com", "Malayalam, English", 4.3, 72, 138, "https://api.dicebear.com/9.x/initials/svg?seed=SuJ"),

        # Environmental Lawyer (had 1)
        ("Adv. Lekha Chandran", "Environmental Lawyer", "Thiruvananthapuram", 13, "KER/3313/2012", "+91-9876500052", "lekha.c@example.com", "Malayalam, English", 4.6, 160, 5, "https://api.dicebear.com/9.x/initials/svg?seed=LC"),
        ("Adv. Pramod Kumar", "Environmental Lawyer", "Kochi", 10, "KER/3314/2015", "+91-9876500053", "pramod.k@example.com", "Malayalam, English, Hindi", 4.4, 95, 24, "https://api.dicebear.com/9.x/initials/svg?seed=PK"),

        # Banking & Finance Lawyer (had 1)
        ("Adv. Jayasree Pillai", "Banking & Finance Lawyer", "Thiruvananthapuram", 18, "KER/3315/2007", "+91-9876500054", "jayasree.p@example.com", "Malayalam, English", 4.7, 280, 3, "https://api.dicebear.com/9.x/initials/svg?seed=JP"),
        ("Adv. Anil Thampi", "Banking & Finance Lawyer", "Thrissur", 12, "KER/3316/2013", "+91-9876500055", "anil.t@example.com", "Malayalam, English, Hindi", 4.5, 155, 42, "https://api.dicebear.com/9.x/initials/svg?seed=AT"),

        # Arbitration Lawyer (had 1)
        ("Adv. Vinod Gopalan", "Arbitration Lawyer", "Thiruvananthapuram", 16, "KER/3317/2009", "+91-9876500056", "vinod.g@example.com", "Malayalam, English, Hindi", 4.7, 260, 10, "https://api.dicebear.com/9.x/initials/svg?seed=VG"),
        ("Adv. Manju Sebastian", "Arbitration Lawyer", "Kozhikode", 13, "KER/3318/2012", "+91-9876500057", "manju.s@example.com", "Malayalam, English", 4.5, 150, 160, "https://api.dicebear.com/9.x/initials/svg?seed=MaS"),
    ]

    cur.executemany(
        "INSERT INTO lawyers (name, specialization, location, experience_years, bar_council_id, phone, email, languages, rating, cases_won, distance_km, avatar_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        lawyers,
    )


def get_all_lawyers(
    specialization: str | None = None,
    location: str | None = None,
    max_distance_km: int | None = None,
) -> list[dict]:
    """Get lawyers with optional filters."""
    conn = get_connection()
    query = "SELECT * FROM lawyers WHERE 1=1"
    params: list = []

    if specialization:
        query += " AND LOWER(specialization) LIKE ?"
        params.append(f"%{specialization.lower()}%")
    if location:
        query += " AND LOWER(location) LIKE ?"
        params.append(f"%{location.lower()}%")
    if max_distance_km is not None:
        query += " AND distance_km <= ?"
        params.append(max_distance_km)

    query += " ORDER BY rating DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_lawyer_by_id(lawyer_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM lawyers WHERE id = ?", (lawyer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
