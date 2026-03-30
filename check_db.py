import pyodbc
conn = pyodbc.connect(
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=localhost\\SQLEXPRESS;'
    'Database=face_attendance;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes;'
)
c = conn.cursor()
c.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
tables = [r[0] for r in c.fetchall()]
print('Tables:', tables)
for t in tables:
    c.execute(f'SELECT COUNT(*) FROM [{t}]')
    print(f'  {t}: {c.fetchone()[0]} rows')

# Check columns of employees table
print()
c.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='employees' ORDER BY ORDINAL_POSITION")
print('employees columns:', [(r[0], r[1]) for r in c.fetchall()])

# Check columns of attendance table
c.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='attendance' ORDER BY ORDINAL_POSITION")
print('attendance columns:', [(r[0], r[1]) for r in c.fetchall()])

conn.close()
print('Done.')
