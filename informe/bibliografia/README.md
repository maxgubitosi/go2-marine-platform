# Bibliografia local del informe

Esta carpeta centraliza los PDFs asociados a `informe/bibliography.bib`.

- `papers/`: un PDF por paper, nombrado como `<bibkey>.pdf`.
- `manifest.json`: estado de descarga, fuente resuelta y ruta local de cada entrada.

Uso:

```bash
python3 informe/scripts/sync_bibliography_pdfs.py
```

Notas:

- Las referencias web del `.bib` como `opencv_aruco_tutorial` y `opencv_calib3d` quedan registradas en el manifest, pero no generan PDF.
- `informe/refs/` sigue reservado para material auxiliar no bibliografico, por ejemplo `PPO_Car_Racing.pdf`.
