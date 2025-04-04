import json
import os
import io
import base64
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # GUI backend hatalarını önlemek için
import sys
import psutil
import plotly.graph_objects as go
from plotly.offline import plot
from datetime import datetime
from docx import Document
from docx.shared import Inches
import requests
import base64
import os
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "supersecretkey"
UPLOAD_FOLDER = 'uploads'
RULES_FILE = "rules.json"
MISSING_RULES_FILE = "missing_rules.json"  # Satılmayan ürünler için öneri dosyası
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

KATALOG_DOSYA = "Kategoriler.csv"

#  Ürün kataloğunu oku veya boş set oluştur
if os.path.exists(KATALOG_DOSYA):
    katalog_df = pd.read_csv(KATALOG_DOSYA, encoding="utf-8", sep=";", low_memory=False)
    if "Ürün Tanım" in katalog_df.columns:
        urun_katalogu = set(katalog_df["Ürün Tanım"].astype(str).str.strip())
    else:
        urun_katalogu = set()
else:
    urun_katalogu = set()

def load_rules():
    if not os.path.exists(RULES_FILE):
        with open(RULES_FILE, "w", encoding="utf-8") as file:
            json.dump([], file)
    with open(RULES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_rules(rules):
    with open(RULES_FILE, "w", encoding="utf-8") as file:
        json.dump(rules, file, indent=4, ensure_ascii=False)

def load_missing_rules():
    if not os.path.exists(MISSING_RULES_FILE):
        with open(MISSING_RULES_FILE, "w", encoding="utf-8") as file:
            json.dump([], file)
    with open(MISSING_RULES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_missing_rules(missing_rules):
    with open(MISSING_RULES_FILE, "w", encoding="utf-8") as file:
        json.dump(missing_rules, file, indent=4, ensure_ascii=False)

import pandas as pd




from datetime import datetime

from datetime import datetime
import pandas as pd

def detect_and_extract_columns(file_path):
    df = pd.read_csv(file_path, encoding="utf-8", sep=";", header=None, low_memory=False)

    start_date = None
    end_date = None

    # İlk 10 satırı satır bazında birleştirip içinde ara
    for i in range(10):
        row_text = " ".join(df.iloc[i].dropna().astype(str)).lower()

        if "başlangıç tarihi" in row_text and start_date is None:
            try:
                tarih_str = row_text.split("başlangıç tarihi:")[1].split()[0] + " " + row_text.split("başlangıç tarihi:")[1].split()[1]
                start_date = datetime.strptime(tarih_str.strip(), "%d.%m.%Y %H:%M:%S")
            except:
                continue

        if "bitiş tarihi" in row_text and end_date is None:
            try:
                tarih_str = row_text.split("bitiş tarihi:")[1].split()[0] + " " + row_text.split("bitiş tarihi:")[1].split()[1]
                end_date = datetime.strptime(tarih_str.strip(), "%d.%m.%Y %H:%M:%S")
            except:
                continue

    # ✅ Rapor Tipi Belirleme
    if start_date and end_date:
        days = (end_date - start_date).days
        if 25 <= days <= 34:
            rapor_tipi = "Aylık"
            # İngilizce ay ismini Türkçe'ye çevirme
            ay_ismi_en = start_date.strftime("%B")  # Örneğin "March"
            
            # Ayları Türkçe'ye çevir
            ay_cevirisi = {
                "January": "Ocak",
                "February": "Şubat",
                "March": "Mart",
                "April": "Nisan",
                "May": "Mayıs",
                "June": "Haziran",
                "July": "Temmuz",
                "August": "Ağustos",
                "September": "Eylül",
                "October": "Ekim",
                "November": "Kasım",
                "December": "Aralık"
            }
            
            # Ay ismini Türkçe'ye çeviriyoruz
            ay_ismi = ay_cevirisi.get(ay_ismi_en, ay_ismi_en)
            
            rapor_tipi = f"{ay_ismi} Ayı İçin Aylık Satış Analizi"
        elif 76 <= days <= 110:
            rapor_tipi = "3 Aylık Satış Analizi"

        elif 160 <= days <= 220:
            rapor_tipi = "6 Aylık Satış Analizi"
        elif 340 <= days <= 385:
            rapor_tipi = "Yıllık Satış Analizi"
        else:
            rapor_tipi = f"{days} Günlük"
    else:
        rapor_tipi = "Genel"

    # HTML şablonunda kullanılacak rapor tipi ve dosya ismi
    print(f"✅ Başlangıç: {start_date} | Bitiş: {end_date} ➜ Rapor Tipi: {rapor_tipi}")
    # 🧩 Son olarak buraya senin tüm veri ayıklama işlemlerin gelmeli:
    # df_cleaned = ...
    # return df_cleaned,_


    # ⬇️ SÜTUNLARI TESPİT ET (eski kodunla aynı)
    malzeme_keywords = ["malzeme grubu", "ürün grubu", "malzeme adı"]
    kategori_keywords = ["kategori"]
    satis_keywords = ["net satış miktarı", "satış miktar", "toplam satış"]
    kdvli_keywords = ["kdv li net satış tutar", "kdv'li net satış tutarı", "kdv dahil satış tutarı"]

    malzeme_sutun = kategori_sutun = satis_sutun = kdvli_sutun = data_start_row = None

    for i in range(50):
        row_values = df.iloc[i].astype(str).str.lower()

        for keyword in malzeme_keywords:
            if any(row_values.str.contains(keyword)):
                malzeme_sutun = row_values[row_values.str.contains(keyword)].index[0]
        for keyword in kategori_keywords:
            if any(row_values.str.contains(keyword)):
                kategori_sutun = row_values[row_values.str.contains(keyword)].index[0]
        for keyword in satis_keywords:
            if any(row_values.str.contains(keyword)):
                satis_sutun = row_values[row_values.str.contains(keyword)].index[0]
        for keyword in kdvli_keywords:
            if any(row_values.str.contains(keyword)):
                kdvli_sutun = row_values[row_values.str.contains(keyword)].index[0]

        if all([malzeme_sutun, kategori_sutun, satis_sutun, kdvli_sutun]):
            data_start_row = i
            break

    if None in [malzeme_sutun, kategori_sutun, satis_sutun, kdvli_sutun, data_start_row]:
        raise ValueError("Gerekli sütunlar bulunamadı!")

    # Temizlenmiş veri çerçevesi
    df_cleaned = df.iloc[data_start_row + 1:, [malzeme_sutun, kategori_sutun, satis_sutun, kdvli_sutun]]
    df_cleaned.columns = ["Malzeme Grubu", "Kategori", "Net Satış Miktarı", "Kdv Li Net Satış Tutar"]
    df_cleaned = df_cleaned[df_cleaned["Malzeme Grubu"] != "Toplam"].dropna()

    for col in ["Net Satış Miktarı", "Kdv Li Net Satış Tutar"]:
        df_cleaned[col] = (
            df_cleaned[col].astype(str)
            .str.replace(r"[^\d,-]", "", regex=True)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce")

    # Filtreleme için ayrı sütun
    df_cleaned["Filtre"] = df_cleaned["Malzeme Grubu"].apply(
        lambda x: (
            "AdaHome" if "adahome" in x.lower() else
            "AdaWall" if "adawall" in x.lower() else
            "AdaPanel" if "adapanel" in x.lower() else
            "Diğer"
        )
        
    )

    return df_cleaned, rapor_tipi,



def generate_combined_recommendations(df_cleaned):
    import pandas as pd
    import os

    def get_unit_from_keyword(keyword):
        keyword = keyword.lower()
        if any(kw in keyword for kw in ["kumaş", "perde", "poster", "katalog"]):
            return "metre"
        elif any(kw in keyword for kw in ["puf", "mobilya", "yastık", "şezlong"]):
            return "adet"
        elif "tutkal" in keyword:
            return "adet"
        elif any(kw in keyword for kw in ["adawall 16.5 m2'lik rulo", "adawall 10.6 m2'lik rulo", "duvar kağıdı", "adawall duvar kağıdı"]):
            return "rulo"
        else:
            return ""

    rules = load_rules()
    ANA_TABLO_PATH = "ana_tablo.csv"

    if not os.path.exists(ANA_TABLO_PATH):
        return "<div class='no-recommendation'>❗ ana_tablo.csv bulunamadı.</div>"

    ana_tablo_df = pd.read_csv(ANA_TABLO_PATH, encoding="utf-8", sep=";")
    ana_tablo_df["Malzeme Grubu"] = ana_tablo_df["Malzeme Grubu"].astype(str).str.strip()
    ana_tablo_df["Kategori"] = ana_tablo_df["Kategori"].astype(str).str.strip()
    df_cleaned["Malzeme Grubu"] = df_cleaned["Malzeme Grubu"].astype(str).str.strip()
    df_cleaned["Kategori"] = df_cleaned["Kategori"].astype(str).str.strip()

    ana_tablo_df["key"] = ana_tablo_df["Malzeme Grubu"] + "||" + ana_tablo_df["Kategori"]
    df_cleaned["key"] = df_cleaned["Malzeme Grubu"] + "||" + df_cleaned["Kategori"]

    merged = ana_tablo_df.merge(
        df_cleaned[["key", "Net Satış Miktarı"]],
        on="key",
        how="left",
        suffixes=("", "_Gercek")
    )
    merged["Net Satış Miktarı"] = merged["Net Satış Miktarı_Gercek"].fillna(0)
    merged = merged.drop(columns=["Net Satış Miktarı_Gercek", "key"])

    combined_blocks = []
    brands = ["adahome", "adawall", "adapanel"]

    for brand in brands:
        block = ""
        brand_df = merged[merged["Malzeme Grubu"].str.lower().str.contains(brand)]
        icon = "🏠" if brand == "adahome" else "🧱" if brand == "adawall" else "🧹"
        brand_title = brand.upper()

        general_rule = next((r for r in rules if r["keyword"].lower() == brand and isinstance(r["threshold"], (int, float))), None)
        total_sales = brand_df["Net Satış Miktarı"].sum()

        # Logo yolu
        if brand_title == "ADAHOME":
            logo_path = "/static/images/adahome-logo.png"
        elif brand_title == "ADAWALL":
            logo_path = "/static/images/adawall-logo.png"
        elif brand_title == "ADAPANEL":
            logo_path = "/static/images/adapanel-logo.png"
        else:
            logo_path = None

        block += f"""
        <div class="brand-recommendation" style="background-color: #fff; border-radius: 15px; padding: 25px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <div style='text-align: center; margin-bottom: 10px;'>
                <img src='{logo_path}' alt='{brand_title} Logo' style='height: 50px; width: auto;'>
            </div>
            <div style="text-align: center; font-size: 24px; font-weight: bold; margin-top: 5px;">
                {brand_title} GENEL DURUM RAPORU
            </div>
            <hr style="border: none; border-top: 3px dashed yellow; margin: 20px 0;">
            <div style="font-size: 16px; font-weight: bold; margin-bottom: 10px;">
                <span style='font-size: 18px;'>💡</span> ÖNERİLERİMİZ:
            </div>
        """

        product_rules = [r for r in rules if r["keyword"].lower().startswith(brand) and r["keyword"].lower() != brand]
        has_recommendation = False

        for rule in product_rules:
            keyword = rule["keyword"].lower()
            filtered = pd.DataFrame()

            if keyword == "adawall 10.6 m2'lik rulo":
                filtered = merged[(merged["Malzeme Grubu"].str.lower().str.contains("adawall duvar kağıdı")) & (merged["Kategori"].str.lower() == "10.0 mtr")]
            elif keyword == "adawall 16.5 m2'lik rulo":
                filtered = merged[(merged["Malzeme Grubu"].str.lower().str.contains("adawall duvar kağıdı")) & (merged["Kategori"].str.lower() == "15.6 mtr")]
            elif keyword == "adawall tutkal":
                filtered = merged[(merged["Malzeme Grubu"].str.lower().str.contains("adawall tutkal")) & (merged["Kategori"].str.lower().str.contains("200 gram"))]
            elif keyword == "adahome döşemelik kumaş":
                filtered = brand_df[brand_df["Malzeme Grubu"].str.lower().str.contains("adahome.*kumaş")]
            elif keyword == "adawall poster":
                filtered = brand_df[brand_df["Malzeme Grubu"].str.lower().str.contains("adawall") & brand_df["Malzeme Grubu"].str.lower().str.contains("poster|katalog")]
            elif keyword == "adahome yastık":
                filtered = merged[merged["Malzeme Grubu"].str.lower().str.contains("adahome.*yastık")]
            elif keyword == "adapanel ürünleri":
                thresholds = rule["threshold"] if isinstance(rule["threshold"], dict) else {}
                paket_df = brand_df[brand_df["Malzeme Grubu"].str.lower().str.contains("paket")]
                ozel_df = brand_df[brand_df["Malzeme Grubu"].str.lower().str.contains("özel üretim")]
                paket_satis = paket_df["Net Satış Miktarı"].sum()
                ozel_satis = ozel_df["Net Satış Miktarı"].sum()
                if paket_satis < thresholds.get("Paket", float("inf")) and ozel_satis < thresholds.get("Özel Üretim", float("inf")):
                    has_recommendation = True
                    block += f"""
                    <div class='normal-message mt-2'>
                        🔹 <b>{rule['keyword']} satış</b>: Paket: <b>{paket_satis:.1f} Adet </b>, Özel: <b>{ozel_satis:.1f} Metre</b> (Hedef: 20 Paket ve 500 Metre Özel Üretim)<br>
                        ➔ {rule['message']}
                    </div>
                    """
                continue
            else:
                filtered = brand_df[brand_df["Malzeme Grubu"].str.lower().str.contains(keyword)]

            if not filtered.empty:
                product_sales = filtered["Net Satış Miktarı"].sum()
                if isinstance(rule["threshold"], dict):
                    continue
                birim = get_unit_from_keyword(keyword)
                hedef_birim = " Rulo" if "duvar kağıdı" in keyword else (f" {birim}" if birim else "")
                if product_sales < rule["threshold"]:
                    has_recommendation = True
                    block += f"""
                    <div class='normal-message mt-2'>
                        🔹 <b>{rule['keyword']} Satışınız</b>: <b>{product_sales:.1f} {birim}</b> (Hedef: {rule['threshold']}{hedef_birim})<br>
                        ➔ {rule['message']}
                    </div>
                    """

        if not has_recommendation:
            block += """
            <div style="background-color: #f8f9fa; border-left: 4px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 10px; color: #555; font-style: italic;">
                ✅ Bu markaya ait önerilecek özel bir durum bulunmamaktadır.
            </div>
            """

        block += "</div>"
        combined_blocks.append(block)

    if not combined_blocks:
        return "<div class='no-recommendation'>✅ Tüm markalarda yeterli satış ve öneri durumu görünmüyor.</div>"

    return "".join(combined_blocks)




def group_missing_products_by_brand(products):
    grouped = {"AdaHome": [], "AdaWall": [], "AdaPanel": [], "Diğer": []}
    for urun in products:
        urun_lower = urun.lower()
        if "adahome" in urun_lower:
            grouped["AdaHome"].append(urun)
        elif "adawall" in urun_lower:
            grouped["AdaWall"].append(urun)
        elif "adapanel" in urun_lower:
            grouped["AdaPanel"].append(urun)
        else:
            grouped["Diğer"].append(urun)
    return grouped




def generate_pie_charts(satilan_urunler, satilmayan_urunler, df):
    import matplotlib.pyplot as plt
    import base64
    import io
    import matplotlib.patches as mpatches
    from adjustText import adjust_text

    df.columns = df.columns.str.strip()
    categories = ["AdaHome", "AdaPanel", "AdaWall"]
    colors = ['#ffcc00', '#66b3ff', '#99ff99']
    chart_buffers = []

    # --- GRAFİK 1: Satılan vs Satılmayan ürün adedi ---
    fig1, ax1 = plt.subplots(figsize=(3, 3))  # Grafik boyutunu büyütüyoruz
    wedges, texts, autotexts = ax1.pie(
        [len(satilan_urunler), len(satilmayan_urunler)],
        labels=["Satılan", "Satılmayan"],
        autopct='%1.1f%%',
        colors=["#4CAF50", "#FF6347"],
        explode=(0.1, 0),  # Dilimlerden birini daha belirgin yapıyoruz
        shadow=True,
        startangle=90,
        textprops={'fontsize': 8, 'fontweight': 'bold', 'ha': 'center'},  # Metin fontunu artırdık
        labeldistance=1.2  # Etiketler biraz daha uzaklaşsın
    )
    
    ax1.set_title("Toplam Ürün Çeşidi Satışı", fontsize=14, fontweight='bold', pad=20)

    fig1.tight_layout()
    buf1 = io.BytesIO()
    plt.savefig(buf1, format="png", dpi=200, bbox_inches='tight')
    buf1.seek(0)
    chart_buffers.append(base64.b64encode(buf1.read()).decode("utf8"))
    plt.close(fig1)

    # --- GRAFİK 2: KDV'li satış tutarı yüzdesi + altta renkli TL açıklama ---
    fig2, ax2 = plt.subplots(figsize=(4, 4), dpi=250)  # Grafik boyutunu büyütüyoruz
    df_satilan = df[df["Malzeme Grubu"].isin(satilan_urunler)]

    try:
        tutar_column = "Kdv Li Net Satış Tutar (TL)"
        df[tutar_column] = df[tutar_column].astype(float)
    except KeyError:
        tutar_column = "Kdv Li Net Satış Tutar"
        df[tutar_column] = df[tutar_column].astype(float)

    sales_by_category = {
        cat: df_satilan[df_satilan["Malzeme Grubu"].str.contains(fr'\b{cat}\b', na=False, case=False)][tutar_column].sum()
        for cat in categories
    }

    values = list(sales_by_category.values())
    labels = list(sales_by_category.keys())

# Yüzde hesaplama
    total_sales = sum(values)
    percentages = [round((value / total_sales) * 100, 1) for value in values]

# Pie chart (dilim üzerinde yüzde gösterme kapalı)
    wedges, texts = ax2.pie(
        values,
        labels=None,  # Etiket yok
        startangle=90,
        colors=colors,
        pctdistance=0.75,
        labeldistance=1.4,
        textprops={'fontsize': 8, 'fontweight': 'bold', 'ha': 'center'},
        wedgeprops={'width': 0.3}
    )

# Başlık
    ax2.set_title("KDV'li Net Satış Tutarına Göre Dağılım", fontsize=14, fontweight='bold')

# Altta renkli kutular ve yüzdeler
    legend_labels = [
        f"{cat}: ₺{sales_by_category[cat]:,.0f} ({percentages[i]}%)" for i, cat in enumerate(categories)
    ]
    legend_patches = [
        mpatches.Patch(color=colors[i], label=legend_labels[i]) for i in range(len(categories))
    ]

    ax2.legend(
     handles=legend_patches,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.25),
        fontsize=10,
        frameon=False
    )

    fig2.tight_layout()
    buf2 = io.BytesIO()
    plt.savefig(buf2, format="png", dpi=200, bbox_inches='tight')
    buf2.seek(0)
    chart_buffers.append(base64.b64encode(buf2.read()).decode("utf8"))
    plt.close(fig2)
    return chart_buffers










from flask import send_file

from flask import send_file, session

import os





from flask import send_file




from flask import send_file










import os
import signal

@app.route("/kapat")
def kapat():
    os.kill(os.getpid(), signal.SIGTERM)
    return "Uygulama kapatılıyor..."


@app.route("/filtered_sold_chart", methods=["POST"])
def filtered_chart():
    if 'data' not in session:
        return ""

    df = pd.DataFrame(session['data'])
    selected = request.json.get("selected_categories", [])
    
    # Seçilen kategorilere göre satışları topla
    data_dict = {}
    for category in selected:
        cat_df = df[df["Malzeme Grubu"].str.contains(category, case=False, na=False)]
        total_sales = cat_df["Net Satış Miktarı"].sum()
        data_dict[category] = total_sales

    if sum(data_dict.values()) == 0:
        data_dict = {"Seçilenlerde Satış Yok": 1}

    fig = go.Figure(data=[go.Pie(
        labels=list(data_dict.keys()),
        values=list(data_dict.values()),
        textinfo='label+percent+value',
        insidetextorientation='auto',
        marker=dict(line=dict(color='#000000', width=1))
    )])

    fig.update_layout(
        margin=dict(t=30, b=30, l=30, r=30),
        height=400,
        title=dict(text="", font=dict(size=20))
    )

    return plot(fig, output_type='div', include_plotlyjs='cdn')





import os


import threading
from flask import render_template





@app.route("/", methods=["GET", "POST"])
def upload_file():
    recommendations_html = None
    missing_recommendations_html = None
    table_data = None
    missing_products_html = None
    pie_chart_url = None
    rapor_tipi = None
    pie_chart_url2 = None
    
    uploaded_filename = None
    combined_recommendations = None
    grouped_missing = None
    ciro = 0  # ✅ GET istekleri için tanımlı olsun

    if request.method == "POST" and 'file' in request.files:
        file = request.files['file']
        if file:
            uploaded_filename = file.filename
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            try:
                df_cleaned, rapor_tipi = detect_and_extract_columns(file_path)
                session['data'] = df_cleaned.to_dict(orient="records")
                table_data = df_cleaned.to_dict(orient="records")

                # ✅ Satılan ürünler
                satilan_urunler = set(df_cleaned["Malzeme Grubu"].astype(str).str.strip())

                # ✅ Katalogtan eksikleri tespit et (sadece görüntü için)
                satilmayan_urunler = urun_katalogu - satilan_urunler
                grouped_missing = group_missing_products_by_brand(satilmayan_urunler)

                # ✅ Yeni öneri sistemi
                combined_recommendations = generate_combined_recommendations(df_cleaned)

                # ✅ Toplam Ciro Hesabı
                ciro = df_cleaned["Kdv Li Net Satış Tutar"].sum()

                # Sadece görsel gösterim için
                missing_products_html = "<br>".join(sorted(satilmayan_urunler)) if satilmayan_urunler else "✅ Tüm ürünler satılmış!"

                charts = generate_pie_charts(satilan_urunler, satilmayan_urunler, df_cleaned)
                pie_chart_url, pie_chart_url2 = charts

            except Exception as e:
                return f"Hata oluştu:<br><pre>{str(e)}</pre>"

    return render_template("index.html",
                           table_data=table_data,
                           missing_products=missing_products_html,
                           missing_recommendations=missing_recommendations_html,
                           recommendations=recommendations_html,
                           pie_chart_url=pie_chart_url,
                           rapor_tipi=rapor_tipi,
                           ciro=ciro,  # ✅ ciro template'e gönderiliyor
                           pie_chart_url2=pie_chart_url2,
                           
                           uploaded_filename=uploaded_filename,
                           combined_recommendations=combined_recommendations,
                           grouped_missing_products=grouped_missing)







@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    rules = load_rules()
    missing_rules = load_missing_rules()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            keyword = request.form.get("keyword").strip()
            threshold = int(request.form.get("threshold"))
            message = request.form.get("message")
            rules.append({"keyword": keyword, "threshold": threshold, "message": message})
            save_rules(rules)

        elif action == "delete":
            index = int(request.form.get("index"))
            if 0 <= index < len(rules):
                del rules[index]
                save_rules(rules)

        elif action == "add_missing":
            keyword = request.form.get("missing_keyword").strip()
            message = request.form.get("missing_message")
            missing_rules.append({"keyword": keyword, "message": message})
            save_missing_rules(missing_rules)

        elif action == "delete_missing":
            index = int(request.form.get("missing_index"))
            if 0 <= index < len(missing_rules):
                del missing_rules[index]
                save_missing_rules(missing_rules)

        return redirect(url_for("admin_panel"))

    return render_template("admin.html", rules=rules, missing_rules=missing_rules)

from flask import Flask, request, render_template, session


import threading
import webbrowser

if __name__ == "__main__":
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=True, use_reloader=False)
