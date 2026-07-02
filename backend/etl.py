import csv
import sqlite3
import re
import os

def get_cpu_fabric(name):
    if not name: return ''
    n = name.upper()
    if 'INTEL' in n or 'CORE' in n or 'XEON' in n or 'PENTIUM' in n or 'CELERON' in n or 'ATOM' in n:
        return 'Intel'
    if 'AMD' in n or 'RYZEN' in n or 'EPYC' in n or 'OPTERON' in n or 'ATHLON' in n or 'PHENOM' in n or 'SEMPRON' in n or 'FX-' in n:
        return 'AMD'
    if re.match(r'^(PRO\s+)?A\d+-', n) or 'E-SERIES' in n or 'A-SERIES' in n or 'A9-SERIES' in n:
        return 'AMD'
    return name.split(' ')[0]

def run_etl():
    db_path = os.path.join(os.path.dirname(__file__), 'database_v2.sqlite')
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS SistemaOperativo (SIO_ID INTEGER PRIMARY KEY, SIO_Desc TEXT, SIO_Version TEXT);
    CREATE TABLE IF NOT EXISTS Categoria (CAT_ID INTEGER PRIMARY KEY, CAT_Desc TEXT);
    CREATE TABLE IF NOT EXISTS Fabricante (FAB_ID INTEGER PRIMARY KEY, FAB_Desc TEXT);
    CREATE TABLE IF NOT EXISTS Pantalla (PAN_ID INTEGER PRIMARY KEY, PAN_Desc TEXT, PAN_Size REAL);
    CREATE TABLE IF NOT EXISTS GPU (GPU_ID INTEGER PRIMARY KEY, GPU_Fabric TEXT, GPU_Model TEXT);
    CREATE TABLE IF NOT EXISTS Notebook (NOT_ID INTEGER PRIMARY KEY, NOT_Desc TEXT);
    CREATE TABLE IF NOT EXISTS RAM (RAM_ID INTEGER PRIMARY KEY, RAM_Desc TEXT);
    CREATE TABLE IF NOT EXISTS Almacenamiento (ALM_ID INTEGER PRIMARY KEY, ALM_Desc TEXT);
    CREATE TABLE IF NOT EXISTS CPU (CPU_ID INTEGER PRIMARY KEY, CPU_Desc TEXT, CPU_Core INTEGER, CPU_Ghz REAL, CPU_MaxGhz REAL, CPU_Arquitecture TEXT, CPU_Tdp REAL, CPU_igpu TEXT, CPU_Fabric TEXT);
    CREATE TABLE IF NOT EXISTS DataSet_1 (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        FAB_ID INTEGER, NOT_ID INTEGER, CAT_ID INTEGER, PAN_ID INTEGER,
        CPU_ID INTEGER, RAM_ID INTEGER, ALM_ID INTEGER, GPU_ID INTEGER, SIO_ID INTEGER,
        Peso REAL, Precio_Euro REAL
    );
    """)

    def get_id(table, cols, vals):
        placeholders = " AND ".join([f"{c} = ?" for c in cols])
        cur.execute(f"SELECT {cols[0].split('_')[0] + '_ID'} FROM {table} WHERE {placeholders}", vals)
        res = cur.fetchone()
        if res: return res[0]
        cur.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals)
        return cur.lastrowid

    cpu_data = {}
    with open(os.path.join(os.path.dirname(__file__), '..', 'tpu_cpus.csv'), encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Name', '').strip()
            if not name: continue
            cpu_data[name] = row
            cpu_fab = get_cpu_fabric(name)
            cores = row['Cores'].split('/')[0].strip() if row.get('Cores') else None
            tdp = re.sub(r'[^\d.]', '', row['TDP']) if row.get('TDP') else None
            tdp = float(tdp) if tdp else None
            
            clock_str = row.get('Clock', '')
            ghz, max_ghz = None, None
            if clock_str:
                nums = re.findall(r'[\d.]+', clock_str)
                if nums:
                    ghz = float(nums[0])
                    max_ghz = float(nums[1]) if len(nums) > 1 else ghz
                    if 'MHz' in clock_str:
                        ghz /= 1000
                        max_ghz /= 1000

            get_id('CPU', 
                ['CPU_Desc', 'CPU_Core', 'CPU_Ghz', 'CPU_MaxGhz', 'CPU_Arquitecture', 'CPU_Tdp', 'CPU_igpu', 'CPU_Fabric'],
                [name, cores, ghz, max_ghz, row.get('Codename'), tdp, '', cpu_fab]
            )

    with open(os.path.join(os.path.dirname(__file__), '..', 'laptops.csv'), encoding='latin-1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sio_id = get_id('SistemaOperativo', ['SIO_Desc', 'SIO_Version'], [row['Operating System'], row['Operating System Version']])
            cat_id = get_id('Categoria', ['CAT_Desc'], [row['Category']])
            fab_id = get_id('Fabricante', ['FAB_Desc'], [row['Manufacturer']])
            
            size_m = re.search(r'[\d.]+', row['Screen Size'])
            size = float(size_m.group()) if size_m else None
            pan_id = get_id('Pantalla', ['PAN_Desc', 'PAN_Size'], [row['Screen'], size])
            
            gpu_str = row['GPU']
            gpu_fab = gpu_str.split(' ')[0] if gpu_str else ''
            gpu_id = get_id('GPU', ['GPU_Fabric', 'GPU_Model'], [gpu_fab, gpu_str])
            
            not_id = get_id('Notebook', ['NOT_Desc'], [row['Model Name']])
            ram_id = get_id('RAM', ['RAM_Desc'], [row['RAM']])
            alm_id = get_id('Almacenamiento', ['ALM_Desc'], [row.get(' Storage', row.get('Storage', ''))])
            
            cpu_name = row['CPU']
            clean_cpu_name = re.sub(r'\s+[\d.]+GHz$', '', cpu_name, flags=re.IGNORECASE).strip()
            clean_cpu_name = re.sub(r'(Intel\s+Core\s+i\d)\s+([a-zA-Z0-9]+)', r'\1-\2', clean_cpu_name, flags=re.IGNORECASE)
            clean_cpu_name = re.sub(r'(Intel\s+Atom)\s+[Xx](\d)', r'\1 x\2', clean_cpu_name, flags=re.IGNORECASE)
            
            cpu_info = cpu_data.get(clean_cpu_name)
            if not cpu_info:
                for k, v in cpu_data.items():
                    if k.replace('-', ' ') == clean_cpu_name.replace('-', ' ') or clean_cpu_name in k or k in clean_cpu_name:
                        cpu_info = v
                        break
            
            if cpu_info:
                cpu_fab = get_cpu_fabric(clean_cpu_name)
                cores = cpu_info['Cores'].split('/')[0].strip() if cpu_info.get('Cores') else None
                tdp = re.sub(r'[^\d.]', '', cpu_info['TDP']) if cpu_info.get('TDP') else None
                tdp = float(tdp) if tdp else None
                
                clock_str = cpu_info.get('Clock', '')
                ghz, max_ghz = None, None
                if clock_str:
                    nums = re.findall(r'[\d.]+', clock_str)
                    if nums:
                        ghz = float(nums[0])
                        max_ghz = float(nums[1]) if len(nums) > 1 else ghz
                        if 'MHz' in clock_str:
                            ghz /= 1000
                            max_ghz /= 1000

                cpu_id = get_id('CPU', 
                    ['CPU_Desc', 'CPU_Core', 'CPU_Ghz', 'CPU_MaxGhz', 'CPU_Arquitecture', 'CPU_Tdp', 'CPU_igpu', 'CPU_Fabric'],
                    [cpu_info.get('Name', clean_cpu_name), cores, ghz, max_ghz, cpu_info.get('Codename'), tdp, '', cpu_fab]
                )
            else:
                cpu_fab = get_cpu_fabric(clean_cpu_name)
                cpu_id = get_id('CPU', ['CPU_Desc', 'CPU_Fabric'], [clean_cpu_name, cpu_fab])
            
            peso_m = re.search(r'[\d.,]+', row['Weight'])
            peso = float(peso_m.group().replace(',', '.')) if peso_m else None
            precio = float(row['Price (Euros)'].replace(',', '.')) if row['Price (Euros)'] else None
            
            cur.execute("""INSERT INTO DataSet_1 
                (FAB_ID, NOT_ID, CAT_ID, PAN_ID, CPU_ID, RAM_ID, ALM_ID, GPU_ID, SIO_ID, Peso, Precio_Euro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (fab_id, not_id, cat_id, pan_id, cpu_id, ram_id, alm_id, gpu_id, sio_id, peso, precio))
            
    conn.commit()
    conn.close()
    print("ETL completado.")

if __name__ == '__main__':
    run_etl()
