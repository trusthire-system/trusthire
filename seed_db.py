from db import get_connection, hash_password
from datetime import datetime
import sqlite3

def seed():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Companies
    companies = [
        ("Tata Consultancy Services", "tcs.com", "active", "Mumbai", "Maharashtra", "India"),
        ("Infosys", "infosys.com", "active", "Bengaluru", "Karnataka", "India"),
        ("Reliance Industries", "reliance.com", "active", "Mumbai", "Maharashtra", "India"),
        ("Wipro", "wipro.com", "active", "Bengaluru", "Karnataka", "India"),
    ]

    for name, domain, status, city, state, country in companies:
        cur.execute("SELECT id FROM companies WHERE domain=?", (domain,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO companies (name, domain, status, city, state, country, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, domain, status, city, state, country, datetime.now().isoformat()))
            print(f"Added company: {name}")

    # Get company IDs
    cur.execute("SELECT id, domain FROM companies")
    company_map = {domain: id for id, domain in cur.fetchall()}

    # 2. Users (HR and Candidates)
    users = [
        # HRs
        ("Amit Sharma", "amit.sharma@tcs.com", "Pass@123", "hr", company_map["tcs.com"], "active", "9876543210"),
        ("Priya Patel", "priya.patel@infosys.com", "Pass@123", "hr", company_map["infosys.com"], "active", "9876543211"),
        ("Rajesh Kumar", "rajesh.kumar@reliance.com", "Pass@123", "hr", company_map["reliance.com"], "active", "9876543212"),
        
        # Pending HRs for Admin Approval Testing
        ("Anjali Singh", "anjali.singh@wipro.com", "Pass@123", "hr", company_map["wipro.com"], "pending_approval", "9876543213"),
        ("Deepak Reddy", "deepak.reddy@infosys.com", "Pass@123", "hr", company_map["infosys.com"], "pending_approval", "9876543214"),
        
        # Candidates
        ("Rahul Verma", "rahul.verma@gmail.com", "Pass@123", "candidate", None, "active", "9123456780"),
        ("Sneha Gupta", "sneha.gupta@yahoo.com", "Pass@123", "candidate", None, "active", "9123456781"),
        ("Vikram Singh", "vikram.singh@outlook.com", "Pass@123", "candidate", None, "active", "9123456782"),
    ]

    for name, email, password, role, comp_id, status, phone in users:
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO users (name, email, password, role, company_id, status, phone, created_at, verified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, email, hash_password(password), role, comp_id, status, phone, datetime.now().isoformat(), datetime.now().isoformat()))
            print(f"Added user: {name} ({role})")

    # Get HR IDs
    cur.execute("SELECT id, email FROM users WHERE role='hr'")
    hr_map = {email: id for id, email in cur.fetchall()}

    # 3. Job Posts
    job_posts = [
        (company_map["tcs.com"], hr_map["amit.sharma@tcs.com"], "Software Engineer", "Python, SQL, AWS", "2-4 years", "8-12 LPA", "Mumbai", "Looking for a Python developer with experience in cloud services."),
        (company_map["infosys.com"], hr_map["priya.patel@infosys.com"], "Data Analyst", "Python, PowerBI, Excel", "1-3 years", "6-9 LPA", "Bengaluru", "Join our data team to drive insights for global clients."),
        (company_map["reliance.com"], hr_map["rajesh.kumar@reliance.com"], "Project Manager", "Agile, PMP, Scrums", "5-8 years", "15-22 LPA", "Navi Mumbai", "Experienced PM needed for large scale digital transformation."),
    ]

    for comp_id, hr_id, role, skills, exp, salary, loc, desc in job_posts:
        cur.execute("SELECT id FROM job_posts WHERE company_id=? AND role=?", (comp_id, role))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO job_posts (company_id, hr_id, role, skills, experience, salary, location, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (comp_id, hr_id, role, skills, exp, salary, loc, desc, "open", datetime.now().isoformat()))
            print(f"Added job post: {role}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed()
