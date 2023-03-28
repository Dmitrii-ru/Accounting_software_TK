import sqlite3


# sqlitebrowser


# Create table
def create_table():
    conn = sqlite3.connect('taxes.db')
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS taxes (id integer primary key, mrot real, srtah_ot_13_pens real, class text)''')
    c.execute('''SELECT class FROM taxes WHERE class = "nalog"''')
    if c.fetchone() is None:
        c.execute('''INSERT INTO taxes (mrot, srtah_ot_13_pens,class) VALUES (?, ?, ?)''', (0, 0, 'nalog'))
    conn.commit()


# Update nalog
def record_nalog(mrot, srtah_ot_13_pens):
    conn = sqlite3.connect('taxes.db')
    c = conn.cursor()
    n = c.execute(
        f'''UPDATE taxes SET 'mrot' = "{mrot}", 'srtah_ot_13_pens' = "{srtah_ot_13_pens}" WHERE `class` = "nalog" ''')

    conn.commit()


# Get placeholder values
def placeholder_insert_nalog():
    conn = sqlite3.connect('taxes.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM taxes WHERE class = "nalog"''')
    nalog = c.fetchall()
    mrot = nalog[0][1]
    srtah_ot_13_pens = nalog[0][2]
    return {'mrot': mrot, 'srtah_ot_13_pens': srtah_ot_13_pens}



