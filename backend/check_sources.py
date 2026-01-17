"""Check source data quality in the database - write to file."""
import sqlite3

conn = sqlite3.connect('science_digest.db')
cursor = conn.cursor()

with open('data_quality_report.txt', 'w') as f:
    # Check papers by source with missing data
    f.write("SOURCE DATA QUALITY REPORT\n")
    f.write("=" * 60 + "\n\n")

    cursor.execute("""
        SELECT 
            source, 
            COUNT(*) as total,
            SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END) as missing_title,
            SUM(CASE WHEN abstract IS NULL OR abstract = '' THEN 1 ELSE 0 END) as missing_abstract,
            SUM(CASE WHEN summary_headline IS NULL THEN 1 ELSE 0 END) as no_summary
        FROM papers 
        GROUP BY source
        ORDER BY source
    """)

    f.write("Source                | Total | No Title | No Abstract | No Summary Headline\n")
    f.write("-" * 75 + "\n")
    for row in cursor.fetchall():
        source, total, no_title, no_abstract, no_summary = row
        f.write(f"{source:<22}| {total:<6}| {no_title:<9}| {no_abstract:<12}| {no_summary}\n")

    # Show sample papers with missing abstracts  
    f.write("\n\nPAPERS WITH MISSING ABSTRACTS:\n")
    f.write("-" * 60 + "\n")

    cursor.execute("""
        SELECT id, source, title, journal
        FROM papers 
        WHERE abstract IS NULL OR abstract = ''
        ORDER BY source
        LIMIT 15
    """)

    for row in cursor.fetchall():
        title = row[2] if row[2] else 'NO TITLE'
        f.write(f"[{row[1]}] ID {row[0]}: {title[:60]}...\n")
        f.write(f"    Journal: {row[3]}\n\n")
    
    # Show sample of each source
    f.write("\n\nSAMPLE FROM EACH SOURCE:\n")
    f.write("=" * 60 + "\n")
    
    cursor.execute("SELECT DISTINCT source FROM papers ORDER BY source")
    sources = [r[0] for r in cursor.fetchall()]
    
    for source in sources:
        cursor.execute("""
            SELECT id, title, abstract, journal
            FROM papers 
            WHERE source = ?
            LIMIT 2
        """, (source,))
        
        f.write(f"\n--- {source.upper()} ---\n")
        for row in cursor.fetchall():
            f.write(f"ID: {row[0]}\n")
            f.write(f"Title: {row[1][:80] if row[1] else 'NULL'}...\n")
            f.write(f"Abstract: {(row[2][:100] if row[2] else 'NULL')}...\n")
            f.write(f"Journal: {row[3]}\n\n")

conn.close()
print("Report written to data_quality_report.txt")
