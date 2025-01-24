import os
from bs4 import BeautifulSoup
import requests
import time
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Paso 1: Descargar el HTML
url = "https://macrotrends.net/stocks/charts/TSLA/tesla/revenue#google_vignette"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Verifica si la solicitud fue exitosa
    html_data = response.text
    print("HTML descargado con éxito.")

except requests.exceptions.RequestException as e:
    print(f"Error al descargar la página: {e}")
    exit()

# Paso 2: Transformar el HTML con BeautifulSoup
soup = BeautifulSoup(html_data, "html.parser")
tables = soup.find_all("table")

# Validar que haya tablas
if not tables:
    print("No se encontraron tablas en el HTML. Revisa la página o el HTML descargado.")
    exit()

# Buscar la tabla que contiene "Tesla Quarterly Revenue"
table_index = None
for index, table in enumerate(tables):
    if "Tesla Quarterly Revenue" in str(table):
        table_index = index
        break

if table_index is None:
    print("No se encontró la tabla con 'Tesla Quarterly Revenue'. Verifica el HTML.")
    exit()

# Paso 3: Crear un DataFrame con los datos de la tabla
tesla_revenue = pd.DataFrame(columns=["Date", "Revenue"])
for row in tables[table_index].tbody.find_all("tr"):
    cols = row.find_all("td")
    if cols:
        date = cols[0].text.strip()
        revenue = cols[1].text.strip().replace("$", "").replace(",", "")
        tesla_revenue = pd.concat(
            [tesla_revenue, pd.DataFrame({"Date": [date], "Revenue": [revenue]})],
            ignore_index=True,
        )

# Paso 4: Procesar el DataFrame
tesla_revenue = tesla_revenue[tesla_revenue["Revenue"] != ""]
tesla_revenue["Date"] = pd.to_datetime(tesla_revenue["Date"], errors="coerce")
tesla_revenue["Revenue"] = pd.to_numeric(tesla_revenue["Revenue"], errors="coerce")
tesla_revenue = tesla_revenue.dropna()
print("Datos limpios:")
print(tesla_revenue.head())

# Paso 5: Almacenar los datos en SQLite
db_name = "Tesla.db"
connection = sqlite3.connect(db_name)
cursor = connection.cursor()

# Crear tabla
cursor.execute("DROP TABLE IF EXISTS revenue")
cursor.execute("CREATE TABLE revenue (Date TEXT, Revenue REAL)")

# Insertar datos en la base de datos
tesla_tuples = list(tesla_revenue.to_records(index=False))
cursor.executemany("INSERT INTO revenue VALUES (?, ?)", tesla_tuples)
connection.commit()

# Verificar los datos almacenados
print("Datos almacenados en SQLite:")
for row in cursor.execute("SELECT * FROM revenue LIMIT 5"):
    print(row)

# Cerrar la conexión
connection.close()

# Paso 6: Visualizar los datos
# Visualización 1: Línea
plt.figure(figsize=(10, 5))
sns.lineplot(data=tesla_revenue, x="Date", y="Revenue")
plt.title("Evolución del Ingreso Trimestral de Tesla")
plt.xlabel("Fecha")
plt.ylabel("Ingreso (en millones)")
plt.grid()
plt.tight_layout()
plt.show() 

# Visualización 2: Barras anuales
tesla_revenue["Year"] = tesla_revenue["Date"].dt.year
annual_revenue = tesla_revenue.groupby("Year")["Revenue"].sum().reset_index()

plt.figure(figsize=(10, 5))
sns.barplot(data=annual_revenue, x="Year", y="Revenue", hue="Year", palette="viridis")
plt.title("Ingreso Anual de Tesla")
plt.xlabel("Año")
plt.ylabel("Ingreso (en millones)")
plt.grid()
plt.tight_layout()
plt.show() 

# Visualización 3: Barras mensuales promedio
tesla_revenue["Month"] = tesla_revenue["Date"].dt.month
monthly_revenue = tesla_revenue.groupby("Month").mean().reset_index()
plt.figure(figsize=(10, 5))
sns.barplot(data=monthly_revenue, x="Month", y="Revenue", hue="Month", palette="coolwarm")
plt.title("Ingreso Promedio Mensual de Tesla")
plt.xlabel("Mes")
plt.ylabel("Ingreso Promedio (en millones)")
plt.grid()
plt.tight_layout()
plt.show(block=True) 