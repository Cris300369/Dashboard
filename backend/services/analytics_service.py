from typing import List, Dict, Optional
import sqlite3

class AnalyticsService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_laptops(self, **filters) -> List[Dict]:
        query = "SELECT ds.ID, f.FAB_Desc, noteb.NOT_Desc, c.CAT_Desc, p.PAN_Desc, p.PAN_Size, cpu.CPU_Desc, cpu.CPU_Fabric, r.RAM_Desc, a.ALM_Desc, gpu.GPU_Fabric, gpu.GPU_Model, sio.SIO_Desc, ds.Peso, ds.Precio_Euro FROM DataSet_1 ds LEFT JOIN Fabricante f ON ds.FAB_ID = f.FAB_ID LEFT JOIN Notebook noteb ON ds.NOT_ID = noteb.NOT_ID LEFT JOIN Categoria c ON ds.CAT_ID = c.CAT_ID LEFT JOIN Pantalla p ON ds.PAN_ID = p.PAN_ID LEFT JOIN CPU cpu ON ds.CPU_ID = cpu.CPU_ID LEFT JOIN RAM r ON ds.RAM_ID = r.RAM_ID LEFT JOIN Almacenamiento a ON ds.ALM_ID = a.ALM_ID LEFT JOIN GPU gpu ON ds.GPU_ID = gpu.GPU_ID LEFT JOIN SistemaOperativo sio ON ds.SIO_ID = sio.SIO_ID WHERE 1=1"
        params = []
        mapping = {
            'os_desc': 'sio.SIO_Desc',
            'fab_desc': 'f.FAB_Desc',
            'cat_desc': 'c.CAT_Desc',
            'pan_desc': 'p.PAN_Desc',
            'gpu_fab': 'gpu.GPU_Fabric',
            'cpu_fab': 'cpu.CPU_Fabric',
            'ram_desc': 'r.RAM_Desc',
            'alm_desc': 'a.ALM_Desc'
        }
        for k, col in mapping.items():
            if filters.get(k):
                query += f" AND {col} = ?"
                params.append(filters[k])
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]

    def get_canned_query(self, query_id: str) -> List[Dict]:
        queries = {
            "1": "SELECT sio.SIO_Desc AS SistemaOperativo, SUM(ds.Precio_Euro) AS PrecioTotal, COUNT(ds.NOT_ID) AS CantidadModelos, ROUND(AVG(ds.Precio_Euro), 2) AS PrecioPromedio FROM DataSet_1 ds JOIN SistemaOperativo sio ON ds.SIO_ID = sio.SIO_ID GROUP BY sio.SIO_Desc HAVING COUNT(ds.NOT_ID) > 1 ORDER BY PrecioTotal DESC",
            "2": "SELECT f.FAB_Desc AS Fabricante, c.CAT_Desc AS Categoria, sio.SIO_Desc AS SistemaOperativo, COUNT(ds.NOT_ID) AS CantidadModelos, SUM(ds.Precio_Euro) AS PrecioTotal, ROUND(AVG(ds.Precio_Euro), 2) AS PrecioPromedio, MIN(ds.Precio_Euro) AS PrecioMinimo, MAX(ds.Precio_Euro) AS PrecioMaximo, ROUND(AVG(ds.Peso), 2) AS PesoPromedio, MAX(ds.Peso) AS PesoMaximo FROM DataSet_1 ds JOIN Fabricante f ON ds.FAB_ID = f.FAB_ID JOIN Categoria c ON ds.CAT_ID = c.CAT_ID JOIN SistemaOperativo sio ON ds.SIO_ID = sio.SIO_ID GROUP BY f.FAB_Desc, c.CAT_Desc, sio.SIO_Desc HAVING COUNT(ds.NOT_ID) > 1 ORDER BY PrecioPromedio DESC, CantidadModelos DESC",
            "3": "SELECT cpu.CPU_Arquitecture, cpu.CPU_Tdp, COUNT(ds.NOT_ID) AS CantidadModelos, ROUND(AVG(ds.Precio_Euro), 2) AS PrecioPromedio, MIN(ds.Precio_Euro) AS PrecioMinimo, MAX(ds.Precio_Euro) AS PrecioMaximo, ROUND(AVG(cpu.CPU_Ghz), 2) AS GhzPromedio, ROUND(AVG(cpu.CPU_MaxGhz), 2) AS MaxGhzPromedio FROM DataSet_1 ds JOIN CPU cpu ON ds.CPU_ID = cpu.CPU_ID GROUP BY cpu.CPU_Arquitecture, cpu.CPU_Tdp HAVING COUNT(ds.NOT_ID) > 1 ORDER BY PrecioPromedio DESC, CantidadModelos DESC",
            "os_chart": "SELECT sio.SIO_Desc, COUNT(ds.NOT_ID) AS Cantidad FROM DataSet_1 ds JOIN SistemaOperativo sio ON ds.SIO_ID = sio.SIO_ID GROUP BY sio.SIO_Desc",
            "fab_chart": "SELECT f.FAB_Desc AS Fabricante, COUNT(ds.NOT_ID) AS Cantidad FROM DataSet_1 ds JOIN Fabricante f ON ds.FAB_ID = f.FAB_ID GROUP BY f.FAB_Desc HAVING COUNT(ds.NOT_ID) > 1 ORDER BY Cantidad DESC",
            "ram_chart": "SELECT ram.RAM_Desc, COUNT(ds.NOT_ID) AS Cantidad FROM DataSet_1 ds JOIN RAM ram ON ds.RAM_ID = ram.RAM_ID GROUP BY ram.RAM_Desc HAVING COUNT(ds.NOT_ID) > 1 ORDER BY Cantidad DESC",
            "gpu_chart": "SELECT gpu.GPU_Fabric, COUNT(ds.NOT_ID) AS Cantidad FROM DataSet_1 ds JOIN GPU gpu ON ds.GPU_ID = gpu.GPU_ID GROUP BY gpu.GPU_Fabric HAVING COUNT(ds.NOT_ID) > 1 ORDER BY Cantidad DESC",
            "cpu_chart": "SELECT cpu.CPU_Fabric, COUNT(ds.NOT_ID) AS Cantidad FROM DataSet_1 ds JOIN CPU cpu ON ds.CPU_ID = cpu.CPU_ID GROUP BY cpu.CPU_Fabric HAVING COUNT(ds.NOT_ID) > 1 ORDER BY Cantidad DESC",
            "top5_expensive": "SELECT f.FAB_Desc AS Fabricante, c.CAT_Desc AS Categoria, sio.SIO_Desc AS SistemaOperativo, ds.Precio_Euro FROM DataSet_1 ds JOIN Fabricante f ON ds.FAB_ID = f.FAB_ID JOIN Categoria c ON ds.CAT_ID = c.CAT_ID JOIN SistemaOperativo sio ON ds.SIO_ID = sio.SIO_ID GROUP BY f.FAB_Desc, c.CAT_Desc, sio.SIO_Desc, ds.Precio_Euro HAVING COUNT(ds.NOT_ID) > 1 ORDER BY ds.Precio_Euro DESC LIMIT 5",
            "top5_cheap": "SELECT f.FAB_Desc AS Fabricante, c.CAT_Desc AS Categoria, sio.SIO_Desc AS SistemaOperativo, ds.Precio_Euro FROM DataSet_1 ds JOIN Fabricante f ON ds.FAB_ID = f.FAB_ID JOIN Categoria c ON ds.CAT_ID = c.CAT_ID JOIN SistemaOperativo sio ON ds.SIO_ID = sio.SIO_ID GROUP BY f.FAB_Desc, c.CAT_Desc, sio.SIO_Desc, ds.Precio_Euro HAVING COUNT(ds.NOT_ID) > 1 ORDER BY ds.Precio_Euro ASC LIMIT 5",
            "cpu_gpu_combos": "SELECT cpu.CPU_Fabric, gpu.GPU_Fabric, COUNT(ds.NOT_ID) AS Cantidad FROM DataSet_1 ds JOIN CPU cpu ON ds.CPU_ID = cpu.CPU_ID JOIN GPU gpu ON ds.GPU_ID = gpu.GPU_ID GROUP BY cpu.CPU_Fabric, gpu.GPU_Fabric HAVING COUNT(ds.NOT_ID) > 1 ORDER BY Cantidad DESC"
        }
        if query_id not in queries: return [{"error": "not found"}]
        return [dict(r) for r in self.conn.execute(queries[query_id]).fetchall()]
