import io
import geopandas as gpd
import pandas as pd
import streamlit as st

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Konverter Shapefile Poligon ke Koordinat Excel",
    page_icon="🗺️",
    layout="centered",
)

st.title("🗺️ Konverter Shapefile Poligon ke Excel")
st.markdown(
    "Unggah file **Shapefile dalam format `.zip`** (yang berisi file `.shp`, `.shx`, `.dbf`, dll.) untuk mengekstrak titik-titik koordinat (Latitude, Longitude) dari setiap poligon."
)

---

# 1. Unggah File ZIP Shapefile
uploaded_file = st.file_uploader(
    "Pilih file ZIP Shapefile", type=["zip"]
)

if uploaded_file is not None:
  try:
    with st.spinner("Memproses data Shapefile..."):
      # Membaca shapefile langsung dari file zip di memori menggunakan geopandas
      gdf = gpd.read_file(uploaded_file)

      # Pastikan sistem proyeksi koordinat (CRS) adalah WGS84 (EPSG:4326) agar menghasilkan Latitude & Longitude
      if gdf.crs is not None and gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs(epsg=4326)
      elif gdf.crs is None:
        st.warning(
            "⚠️ Peringatan: Shapefile tidak memiliki informasi CRS (Coordinate"
            " Reference System). Diasumsikan data menggunakan EPSG:4326"
            " (Lat/Long)."
        )

      st.success(
          f"Berhasil memuat {len(gdf)} objek poligon dari shapefile!"
      )

      # Menampilkan pratinjau data atribut (tanpa geometri)
      st.subheader("Pratinjau Atribut Data")
      st.dataframe(gdf.drop(columns="geometry").head())

      # 2. Proses Ekstraksi Koordinat
      rows = []
      for idx, row in gdf.iterrows():
        geom = row["geometry"]
        # Ambil semua atribut non-geometri sebagai identifikasi tambahan
        attributes = row.drop("geometry").to_dict()

        if geom is not None:
          # Tangani tipe geometri Polygon atau MultiPolygon
          polygons = (
              geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
          )

          for poly_idx, poly in enumerate(polygons):
            # Mengambil koordinat exterior (batas luar poligon)
            exterior_coords = list(poly.exterior.coords)

            for vertex_idx, (lon, lat) in enumerate(exterior_coords):
              row_data = {
                  "Polygon_ID": idx,
                  "SubPolygon_ID": poly_idx,
                  "Vertex_Sequence": vertex_idx,
                  "Latitude": lat,
                  "Longitude": lon,
              }
              # Gabungkan dengan atribut asli dari shapefile
              row_data.update(attributes)
              rows.append(row_data)

      # Buat DataFrame baru dari hasil ekstraksi
      df_coords = pd.DataFrame(rows)

      st.subheader("Pratinjau Hasil Koordinat")
      st.dataframe(df_coords.head(10))

      # 3. Fungsi untuk Mengunduh ke Excel
      output = io.BytesIO()
      with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_coords.to_excel(writer, index=False, sheet_name="Koordinat_Poligon")
      excel_data = output.getvalue()

      st.download_button(
          label="📥 Unduh Hasil dalam Format Excel (.xlsx)",
          data=excel_data,
          file_name="koordinat_poligon.xlsx",
          mime=(
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          ),
      )

  except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses file: {e}")
