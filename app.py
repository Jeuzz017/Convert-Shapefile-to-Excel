import io
import os
import zipfile
import geopandas as gpd
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Batch Konverter Shapefile ke Excel",
    page_icon="🗺️",
    layout="wide",
)

st.title("🗺️ Batch Konverter Shapefile Poligon ke Excel")
st.markdown(
    "Unggah **satu atau beberapa file ZIP Shapefile** sekaligus untuk mengekstrak titik-titik koordinat ke dalam format Excel."
)

st.divider()

# 1. Atur accept_multiple_files=True
uploaded_files = st.file_uploader(
    "Pilih satu atau beberapa file ZIP Shapefile",
    type=["zip"],
    accept_multiple_files=True,
)

if uploaded_files:
  # Opsi gabungkan sheet atau terpisah
  combine_option = st.radio(
      "Pilih format output Excel:",
      ["Satu File Excel (Tiap Shapefile beda Sheet)", "Satu Sheet Digabung"],
  )

  if st.button("🚀 Proses Semua File"):
    all_dfs = {}
    combined_rows = []

    progress_bar = st.progress(0)

    for i, file in enumerate(uploaded_files):
      file_name = file.name.replace(".zip", "")
      try:
        # Membaca shapefile dari ZIP
        gdf = gpd.read_file(file)

        # Ubah CRS ke WGS84 (Lat/Long) jika ada
        if gdf.crs is not None and gdf.crs != "EPSG:4326":
          gdf = gdf.to_crs(epsg=4326)

        rows = []
        for idx, row in gdf.iterrows():
          geom = row["geometry"]
          attributes = row.drop("geometry").to_dict()

          if geom is not None:
            polygons = (
                geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
            )

            for poly_idx, poly in enumerate(polygons):
              exterior_coords = list(poly.exterior.coords)

            for vertex_idx, pt in enumerate(exterior_coords):
              lon, lat = pt[0], pt[1]  
                
              row_data = {
                  "Source_File": file_name,
                  "Polygon_ID": idx,
                  "SubPolygon_ID": poly_idx,
                  "Vertex_Sequence": vertex_idx,
                  "Latitude": lat,
                  "Longitude": lon,
                }
                row_data.update(attributes)
                rows.append(row_data)

        df_coords = pd.DataFrame(rows)
        all_dfs[file_name[:30]] = (
            df_coords  # Nama sheet Excel maks 31 karakter
        )
        combined_rows.extend(rows)

      except Exception as e:
        st.error(f"Gagal memproses file **{file.name}**: {e}")

      # Update progress bar
      progress_bar.progress((i + 1) / len(uploaded_files))

    if all_dfs:
      st.success(
          f"Berhasil memproses {len(all_dfs)} file shapefile!"
      )

      # Buat File Excel
      output = io.BytesIO()
      with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if (
            combine_option == "Satu File Excel (Tiap Shapefile beda Sheet)"
        ):
          for sheet_name, df in all_dfs.items():
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        else:
          df_combined = pd.DataFrame(combined_rows)
          df_combined.to_excel(
              writer, index=False, sheet_name="Semua_Koordinat"
          )

      excel_data = output.getvalue()

      st.download_button(
          label="📥 Unduh Semua Hasil (.xlsx)",
          data=excel_data,
          file_name="batch_koordinat_shapefile.xlsx",
          mime=(
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          ),
      )
