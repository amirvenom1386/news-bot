import requests
from bs4 import BeautifulSoup
import sqlite3
conn = sqlite3.connect("E:/projects/news/my_database.db")
cursor = conn.cursor()
url="https://thehackernews.com/search/label/Cyber%20Attack?max-results=20"
headers = {"User-Agent": "Mozilla/5.0"}  # برای جلوگیری از بلاک شدن
response = requests.get(url, headers=headers)
html = response.text
soup = BeautifulSoup(html, "html.parser")
# print(html)
div=soup.find("div",class_="blog-posts clear")
links=div.find_all("a",href=True)
text_links=[]
for link in links:
    print(link["href"])
    text_links.append(link)
for text_link in text_links:
    url = text_link.get("href")
    if url:
        response=requests.get(url,headers)
        html=response.text
        soup=BeautifulSoup(html,"html.parser")
        tag_p=soup.find_all("p")
        full_text = "\n".join([p.get_text(strip=True) for p in tag_p])
        cursor.execute("INSERT INTO links (text,url) VALUES (?, ?)", (full_text, url))
        conn.commit()
conn.close()